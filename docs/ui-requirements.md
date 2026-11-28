# UI requirements (collected as we go)

What the screens must do, captured when decided so nothing is lost before the
frontend is built (week 3). Each item notes who asked for it and when.

---

## Orders page (founder / manager view)

**Layout: one page, live orders on top, finished orders folded away below.**

```
┌──────────────────────────────────────────────────────────────┐
│  Orders                                    [ + New order ]   │
├──────────────────────────────────────────────────────────────┤
│  🟠 New (3)                                                   │
│     #SWG-4411  Swiggy   Greek Salad ×2    due 7:30   ₹498    │
│     ...                                                      │
│  🔵 Preparing (2)        ⚠ delayed shown as a badge, not a    │
│     ...                     separate column                  │
│  🟢 Ready (1)                                                 │
│     ...                    [ Rider picked up → On the way ]  │
│  🛵 On the way (2)                                            │
│     ...                    [ Delivered ]                     │
├──────────────────────────────────────────────────────────────┤
│  ▸ Completed today (14)      ← collapsed by default; click   │
│  ▸ Cancelled today (1)          to expand the list           │
└──────────────────────────────────────────────────────────────┘
```

- **Completed orders go in a separate, clickable, collapsible box on the same page**,
  closed by default and showing the count, e.g. "Completed today (14) ▸". Clicking
  expands the list. *(Requested by Nithyaa, 28 Nov 2026)*
- Cancelled orders: same idea, in their own collapsed box, with the cancel reason shown.
- Live orders are grouped by step. Inside each group, the most urgent (least spare
  time) is on top.
- "Delayed" is a badge on the order card (with its reason), not its own group,
  because delay is a flag, not a status.

## Status names on screen

| Stored value | Shown as |
|---|---|
| `received` | New |
| `preparing` | Preparing |
| `ready` | Ready |
| `out_for_delivery` | **On the way** |
| `completed` | Completed (delivered / collected) |
| `cancelled` | Cancelled |

(Source of truth: `STATUS_LABELS` in `backend/app/modules/orders/models.py`.)

## Order steps by channel (enforced by the database)

- **Swiggy, Zomato, subscription:** Ready → **rider picks up → On the way** → Delivered = Completed.
  Can't jump from Ready to Completed. *(Requested by Nithyaa, 28 Nov 2026)*
- **Walk-in:** Ready → Collected = Completed. Never "On the way".
- Buttons shown on a card are only the next steps allowed for that channel.

## Open questions (for the founders)

1. Swiggy/Zomato deliveries: our system isn't told when the platform's rider
   delivers. Who taps "Delivered"? Or should orders auto-complete after X minutes
   "On the way"? (Default for now: someone taps it.)
2. "Today" for the completed box means since midnight IST. Or since opening time?
