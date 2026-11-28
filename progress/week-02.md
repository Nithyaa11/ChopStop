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

### Day 8b — Fri 28 Nov (delivery steps per channel — requested change)
**Requested:** when a rider picks up an order it should show "on the way", and only when delivered become "completed". Completed orders should sit in a separate clickable box on the same page.

**Done**
- Migration `0005` (new migration; `0004` is already on `main`, and pushed migrations are never edited): status rules now depend on the **channel**.
  - **Swiggy, Zomato, subscription:** `ready → on the way → completed (delivered)`. **Can't skip "on the way"** (DB refuses).
  - **Walk-in:** `ready → completed (collected)`. **Can never be "on the way"** (DB refuses).
- Screen labels: `out_for_delivery` is shown as **"On the way"**, `received` as **"New"** (`STATUS_LABELS`).
- `docs/ui-requirements.md` (new): orders page layout. Live orders grouped by step, with **"Completed today (N) ▸" and "Cancelled today (N) ▸" as collapsible boxes** at the bottom, closed by default. Delay shown as a badge. Only allowed next-step buttons shown. To be built in week 3.
- Tests: every status change **for every channel** (115 combinations), plus explicit "must go on the way" and "walk-ins never on the way" tests, and a check that migration `0005`'s frozen rules equal the app's rules.

**Results:** ✅ 309 tests passed · `ruff` ✅ · `alembic check` ✅
- ⚠️ One full run took 50 min instead of ~30 s. A rerun with timings took **32.7 s** (slowest test 1.1 s), with no stuck DB connections, so the cause was the machine (most likely sleep), not the code.

**Open questions for the founders** (also in `docs/ui-requirements.md`)
1. Swiggy/Zomato don't tell us when their rider delivers. Who taps "Delivered", or auto-complete after X minutes "On the way"?
2. Does "Completed today" mean since midnight IST, or since opening time?

### Extra — Fri 28 Nov (founder questions)
- `docs/founder-questions.md`: every open question, in priority order, with space for answers.
  - 🔴 this week: menu with prices and cook times; people and roles; how orders flow (who enters them, the "Delivered" tap vs auto-complete, cancel + re-enter, "today", typo limits, due times); 7 days of real order counts (stage 0).
  - 🟡 next 2–3 weeks: subscriptions (plans, cutoff, pick link); groceries (amounts, suppliers, buffer); money (commissions, payouts, business vs personal).
  - 🟢 later: running cost, tablet and Wi-Fi, integration quote, customer data.
- Nithyaa asks the founders tomorrow (29 Nov). The answers shape Day 9's menu and order API.

### Extra — Fri 28 Nov (roles fitted to the real team)
**Decided with Nithyaa:**
- Mom = **admin**, Aunt = **admin**: both have everything, incl. the food/kitchen page.
- Hired cook = **cook**: kitchen screen only.
- 2 delivery boys = **rider**: own deliveries; customer name, address and phone until delivered.
- Helper: no login for now.

**Done**
- Migration `0006`: roles are now `admin`, `cook`, `rider`; **`founder` removed** (Mom and Aunt are the founders and are admins).
  - 🔒 The migration **refuses to run** if anyone still has the founder role. It never silently promotes people to admin. Tested.
- Tests updated for 3 roles. New test: the `founder` role is rejected by the app and the DB.
- README: new **Roles** table; API table now admin / cook / rider.
- `docs/ui-requirements.md`: "who sees which screen" table (cook: no prices or customer details; rider: contact details hidden after delivery).
- `docs/founder-questions.md`: section 2 marked answered, with 2 follow-ups (login names; helper later). Questions about prices and profit now say "only Mom & Aunt, correct?".

**Results:** `pytest` ✅ **302 passed** · `ruff` ✅ · `alembic check` ✅ · dev DB at `0006`
