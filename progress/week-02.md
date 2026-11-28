# Week 2 — Orders & kitchen

**Dates:** Fri 28 Nov – Fri 5 Dec 2026 (started ~4 days ahead of the original plan)
**Goal:** Orders from all 4 channels (Swiggy, Zomato, subscriptions, walk-ins), no duplicates, a fixed list of allowed status steps, kitchen queue sorted by spare time, live updates.
**Time budget:** 30–60 min per day

## Plan for the week

| Day | Date | Task | Status |
|---|---|---|---|
| 8 | Fri 28 Nov | DB design: menu items, orders, order items, allowed status steps enforced by the DB | ✅ Done. 220 tests |
| 9 | Sat 29 Nov | Order service + API: manual entry for all 4 channels, totals in paise, audit | ⬜ |
| 10 | Sun 30 Nov | Status changes + delay flag + cancel with reason; role rules per step | ⬜ |
| 11 | Mon 1 Dec | Kitchen queue: spare time = due − now − cook time, most urgent first, "at risk" flag | ⬜ |
| 12 | Tue 2 Dec | Live updates (WebSockets) with login check on connect | ⬜ |
| 13 | Wed 3 Dec | Edge cases: duplicate entry, menu changes after ordering, timezones, big orders | ⬜ |
| 14 | Thu 4 Dec | Week 2 review, README API table, role matrix updated | ⬜ |

**Design rules this week** (from the README):
- No duplicate orders: unique `(source, external_order_id)`.
- Delay is a flag, not a status.
- Swiggy/Zomato are typed in by hand for now.
- Money is stored as whole paise (integers), never decimals or floats.

---

## Daily log

### Day 8 — Fri 28 Nov (orders database design)
**Done**
- Branch `feat/orders-schema`. Migration `0004`: tables `menu_items`, `orders`, `order_items`.
- **Channels:** `swiggy`, `zomato`, `subscription`, `walk_in`.
- **Status steps:**
  - `received → preparing → ready → completed`
  - `ready → out_for_delivery → completed` (own rider)
  - `cancel` from any open step
- **Delay** is a separate flag (`is_delayed` + `delay_reason`), so an order can be *preparing and delayed* at the same time.
- Order lines store a **snapshot** of name, price and cook time, so later menu edits never change past orders.
- Index on open orders by due time, for the Day 11 kitchen queue.

**Guardrails added (all enforced by the database, tested by trying to break them as the app user)**
- 🔒 **No duplicate platform orders:** the same Swiggy/Zomato order number can't be entered twice. Swiggy/Zomato orders *must* have their order number. The same number on different platforms is fine.
- 🔒 **Status steps enforced by a trigger.**
  - New orders must start as `received`.
  - **All 30 possible changes tested**: the allowed ones work, the rest are refused.
  - `completed`/`cancelled` orders are frozen.
  - Cancelling needs a reason. A delay needs a reason.
- 🔒 **Money:**
  - Whole paise only.
  - Line total = price × quantity.
  - Quantity 1–50.
  - Order total capped at ₹1,00,000 (typo guard).
  - **The total must equal the sum of the lines, and an order must have at least one line.** Checked at commit by deferred triggers.
- 🔒 **Column-level permissions:**
  - The app can only change status, delay and cancel fields on an order.
  - **Price, total, channel, platform order number and creator are locked** after creation.
  - Order lines can't be edited at all.
  - Nothing (menu, orders, lines) can ever be deleted.
- Menu: price ₹0–10,000, cook time 1–180 min, names unique ignoring case.
- Customer data kept minimal: a name to call out, plus notes. Notes are stored as plain data (the later AI must treat them as data, not instructions).
- The migration keeps its **own frozen copy** of the status rules (migrations must not depend on app code that changes later). A test checks it equals the app's rules.

**Problems hit & fixed**
- 🐛 The totals trigger used `CASE ... NEW.id ELSE NEW.order_id`. PL/pgSQL resolves *both* branches, and orders have no `order_id` column, so the check crashed. Caught by the tests before committing. Fixed with `IF`.
- The test DB still had the old migration applied, so "upgrade to latest" didn't re-run it. Re-applied it on both the dev and test DBs. CI always uses a fresh DB, so it's unaffected.
- Rewrote a test to avoid SQL built with an f-string (ruff S608).

**Results:** `pytest` ✅ **220 passed** (66 new) · `ruff` ✅ · `alembic check` ✅

**Assumptions to confirm with the founders**
1. Platform rider pickup = `completed` straight from `ready`. Our own rider (subscriptions) goes through `out_for_delivery`.
2. An order's items can't be edited after entry; a mistake means cancel (with reason) and re-enter.
3. Typo caps: ₹10,000 per item, ₹1,00,000 per order, 50 of one item.

**Next:** Day 9 — order service + API: create orders (manual entry), menu management, who can do what, audit.
