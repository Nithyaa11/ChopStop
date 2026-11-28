# Questions for the founders

**Meeting date:** ____________ **Asked by:** Nithyaa

**How to use this:** ask in order. 🔴 blocks the work we're about to build, 🟡 is needed in the next 2–3 weeks, 🟢 can wait. Write the answers in the space under each question. Then send it back to Claude, and we'll update the system and the README.

---

## 🔴 1. Menu: needed for Day 9 (this week)

We need the real menu to set up the system. A photo of the menu or a list is fine.

| Dish | Walk-in price (₹) | Swiggy price (₹) | Zomato price (₹) | Usual cooking time (min) |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

- **1a.** Are Swiggy/Zomato prices different from walk-in prices? If yes, which price should our system record: what the customer paid on the app, or our walk-in price?
  > Answer:
- **1b.** Are there any combos, add-ons or extras (extra cheese, extra dressing)? Do they change the price?
  > Answer:
- **1c.** Who is allowed to change menu prices? Only founders, or also the manager?
  > Answer:

---

## 🔴 2. People and logins: needed this week

Each person gets their own login. Nobody shares one.

| Name | What they do | Role in the system (admin / founder / cook / rider) |
|---|---|---|
| | | |
| | | |
| | | |
| | | |
| | | |
| | | |

- **2a.** Mom runs the kitchen day to day. Should she see **money** (sales, totals) or just orders? If not money, we'll add a separate "manager" role.
  > Answer:
- **2b.** Who should be the **admin**, the person who creates logins and resets passwords? We suggest 1–2 people only.
  > Answer:
- **2c.** Should riders see the customer's phone number and address, or only the order and the area?
  > Answer:

---

## 🔴 3. How orders flow: needed this week

- **3a.** **Who types the orders into the system?** Mom, a cook, a founder? Is it the same person for Swiggy, Zomato and walk-ins?
  > Answer:
- **3b.** When a Swiggy or Zomato rider picks up an order, our system will show it as **"On the way"**. The apps don't tell us when it's delivered. What should happen next?
  - [ ] Someone taps **"Delivered"**
  - [ ] Mark it completed automatically after ____ minutes "On the way"
  > Answer:
- **3c.** If an order was entered wrong (wrong dish or quantity), is it okay to **cancel it with a reason and enter it again**? (The system doesn't allow editing an order after it's entered, to keep the money records honest.)
  > Answer:
- **3d.** For the **"Completed today"** box on the orders screen, should "today" start at **midnight**, or at **opening time**? What are the opening hours?
  > Answer:
- **3e.** Typo safety limits. Do these sound right?
  - Max ₹10,000 for one item · max ₹1,00,000 for one order · max 50 of the same dish in one order
  > Answer:
- **3f.** Do walk-in customers ever get **delivery** (by our riders)? Or do they always collect?
  > Answer:
- **3g.** How long before pickup does Swiggy/Zomato usually give you? What's a normal **"due" time** for each channel?
  > Answer:

---

## 🔴 4. One week of real numbers ("Stage 0")

Please note this down every day for the next 7 days. A notebook or WhatsApp note is fine. It tells us what to build first and whether paid Swiggy/Zomato integration is worth it.

| Day | Swiggy orders | Zomato orders | Walk-ins | Subscriptions | Busiest hour(s) | What was most stressful? |
|---|---|---|---|---|---|---|
| Day 1 | | | | | | |
| Day 2 | | | | | | |
| Day 3 | | | | | | |
| Day 4 | | | | | | |
| Day 5 | | | | | | |
| Day 6 | | | | | | |
| Day 7 | | | | | | |

---

## 🟡 5. Subscriptions: needed in about 2 weeks

- **5a.** What plans exist (e.g. weekly / monthly, how many meals), and what do they cost?
  > Answer:
- **5b.** Every day Mom sends 2 salad options on WhatsApp. **By what time** must people reply (the cutoff)? What happens if someone doesn't reply: skip that day, or a default salad?
  > Answer:
- **5c.** Is it okay to put a **link in the WhatsApp message** where subscribers tap to pick their salad (no app or login needed)? Replies then go straight into the system, with no counting by hand.
  > Answer:
- **5d.** About how many subscribers are there now? Where are they (areas)?
  > Answer:
- **5e.** Who delivers subscriptions, our 2 riders? Roughly what time?
  > Answer:

---

## 🟡 6. Groceries and stock: needed in about 3 weeks

- **6a.** For each dish, roughly **how much of each ingredient** goes into one portion? (Even rough amounts help.)
  > Answer:
- **6b.** Who buys groceries, how often, and from where? Is there one supplier or several?
  > Answer:
- **6c.** The grocery list will add a **10% safety buffer**. Is that the right amount?
  > Answer:

---

## 🟡 7. Money: needed before we build finance (after Dec)

The system is designed for this from day one, but we can't build it until we understand it.

- **7a.** What **commission %** do Swiggy and Zomato actually take? Are there other fees (payment, ads, packaging)?
  > Swiggy: ______ % · Zomato: ______ % · Other fees:
- **7b.** How do Swiggy/Zomato **pay you** (how often, to which account)?
  > Answer:
- **7c.** **Business vs personal money:** right now some of it is mixed. How do founders put money into the business, and take money out?
  > Answer:
- **7d.** Shared costs (rent, gas, electricity): who pays and how is it split?
  > Answer:
- **7e.** Who should be allowed to **see** sales and profit numbers?
  > Answer:

---

## 🟢 8. Running costs and setup: can wait

- **8a.** Is about **₹2,000/month** for running the system (server, database, backups) okay?
  > Answer:
- **8b.** Which **tablet or phone** will the kitchen use? Is there reliable Wi-Fi in the kitchen?
  > Answer:
- **8c.** Later, connecting Swiggy/Zomato automatically needs a paid partner (e.g. UrbanPiper, Petpooja). Should we ask them for a **written price quote**? (We won't sign up for anything without one.)
  > Answer:
- **8d.** Any customer data we must be careful about, or anything customers have asked us not to store?
  > Answer:

---

## ✅ Already decided (just for reference, no need to ask)

- Swiggy/Zomato orders are **typed in by hand** for now. No scraping their apps (it breaks their rules and could get the account suspended).
- No WhatsApp bots or unofficial tools (the number could get banned). We use the normal WhatsApp Business app plus a pick link.
- Delivery orders go **Ready → On the way → Completed**. Walk-ins go **Ready → Completed**.
- Orders are never deleted. Every change is recorded with who did it and when.
- The AI (later) only **suggests**. A person always approves. It can never change prices, spend money or cancel orders on its own.
