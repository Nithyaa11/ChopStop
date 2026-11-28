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
- **1c.** Prices: only Mom and Aunt (admins) can change them. Correct?
  > Answer:

---

## ✅ 2. People and logins: ANSWERED by Nithyaa (28 Nov)

| Person | What they do | Role in the system |
|---|---|---|
| Mom | Runs everything, management | **admin**: everything |
| Aunt | Salads, groceries, cooks, manages | **admin**: everything, incl. the food/kitchen page |
| Hired cook | Only cooks | **cook**: kitchen screen only (orders to cook, mark Preparing / Ready). No money, prices, accounts or customer details |
| Delivery boy 1 | Deliveries | **rider**: only their own deliveries; customer name, address, phone until delivered |
| Delivery boy 2 | Deliveries | **rider** (same) |
| Helper | Helps | **no login** for now (can be added later) |

- There's no separate "founder" role: Mom and Aunt are the founders and are both admins.
- More workers may join later. Each gets their own login with the smallest role that fits.

**Still worth confirming with Mom & Aunt:**
- **2d.** What are everyone's **names** for the logins (e.g. `ravi`, `priya`)? Each person picks their own password the first time.
  > Answer:
- **2e.** If the helper starts packing or handing over orders, should they get the same kitchen screen as the cook?
  > Answer:

---

## 🔴 3. How orders flow: needed this week

- **3a.** **Walk-in orders: who adds them to the Chopstop app?** When a customer orders at the counter, someone puts that order into our app (the new kitchen system we're building) so it shows up on the kitchen screen. Is that Mom, Aunt, or whoever is free? (The hired cook can't: her screen is kitchen only.) Swiggy/Zomato orders should come in **automatically** (see section 9). Until that's set up, who copies them in?
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
- **3f.** ✅ Answered: walk-in customers eat **at the table**. When the cook finishes, the **helper takes the food to the customer's table**. So for walk-ins, "Completed" means **"Served"**.
- **3f-2.** The helper has no login. **Who taps "Served"** in the app: the cook when she hands the plate to the helper, or Mom/Aunt? Or should the helper get a simple login just for this one button?
  > Answer:
- **3f-3.** Do walk-in customers ever take food **away (parcel)** instead of eating there?
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
- **7e.** Sales and profit numbers: only Mom and Aunt (admins) see them. Correct?
  > Answer:

---

## 🟢 8. Running costs and setup: can wait

- **8a.** Is about **₹2,000/month** for running the system (server, database, backups) okay?
  > Answer:
- **8b.** Which **tablet or phone** will the kitchen use? Is there reliable Wi-Fi in the kitchen?
  > Answer:
- **8d.** Any customer data we must be careful about, or anything customers have asked us not to store?
  > Answer:

---

## 🔴 9. Swiggy & Zomato orders coming in AUTOMATICALLY: decide soon

**Goal:** when an order is accepted on Swiggy/Zomato, it appears in the Chopstop app by itself. Nobody types it.

**The catch:** Swiggy and Zomato don't give small restaurants a direct connection (API). The only **official** way is through an **approved integration partner**. The partner receives the orders from Swiggy/Zomato and passes them to our system. Here are all the options:

| Option | Cost | Safe? | How it works | Verdict |
|---|---|---|---|---|
| **A. Integration partner** (UrbanPiper, or similar POS-integration companies) | **Paid.** Prices aren't published; third-party reports range from about ₹700 to ₹15,000 per month depending on the plan. **Must get a written quote.** | ✅ Official, approved by Swiggy/Zomato | Partner sends each order to our system the moment it comes in | ✅ **Recommended**, if the quote fits the budget |
| **B. A POS that already connects** (e.g. Petpooja) | **Paid** yearly subscription | ✅ Official | Orders go into *their* POS. We'd need them to also pass orders on to our system, which not all do. **Must ask** | 🟡 Only if they can send orders to our system |
| **C. Type them in** (the earlier plan) | Free | ✅ Safe | Someone copies each order into our app (about 20 seconds, duplicates blocked) | 🟡 **Only a stop-gap** until A is set up |
| **D. Reading the Swiggy/Zomato apps automatically** (scraping, reading phone notifications, bots) | "Free" | ❌ **Not safe.** Breaks Swiggy/Zomato rules; the restaurant account can be **suspended**, and it breaks whenever their app updates | — | ❌ **Don't use** |

**Questions to decide:**
- **9a.** Can we contact **UrbanPiper** (and 1–2 similar companies) for a **written quote** for 1 outlet with Swiggy + Zomato? (We won't sign up for anything without a written price.)
  > Answer:
- **9b.** What monthly cost for this would be okay? ₹______ / month
  > Answer:
- **9c.** Do you already use any POS or billing software (Petpooja, etc.)? If yes, which one?
  > Answer:

**Questions to ask the integration companies** (for the quote call):
1. Total cost per month for **1 outlet, Swiggy + Zomato**, including setup fees and GST?
2. Can you **send each order to our own system** automatically (they may call it "webhook" or "POS API")? We have our own app.
3. When an order is accepted on Swiggy/Zomato, how fast does it reach us?
4. Can we still accept and reject orders in the Swiggy/Zomato partner apps, or only through you?
5. Does it also update **"food ready"** or **item out of stock** back to Swiggy/Zomato?
6. Minimum contract length? Can we cancel any month?

---

## 🟡 10. WhatsApp for subscriptions: options

**You're right that the WhatsApp Business *API* isn't straightforward**, but it's possible:
- You need a **Meta Business account**, plus business verification (documents).
- Usually you go through a **WhatsApp partner company** (called a "BSP") that handles the setup for a monthly fee.
- Meta now allows **"coexistence"**: the **same number** can stay on the normal WhatsApp Business app (Mom keeps using it on her phone) **and** be connected to the API, so you don't lose the number.

| Option | Cost | Safe? | What it gives | Verdict |
|---|---|---|---|---|
| **A. Normal WhatsApp Business app + pick link** | **Free** | ✅ | Mom sends one broadcast with a link; subscribers tap Salad A or B; replies land in our app automatically; reminders are one tap | ✅ **Start here**: no setup, no cost |
| **B. WhatsApp Business API through a partner company** (e.g. Interakt, AiSensy, Wati, or Meta directly) | **Paid:** partner's monthly fee **plus** Meta's per-message charge. Recent rates: about ₹0.86 per marketing message and about ₹0.12 per utility message, plus GST (confirm with Meta) | ✅ Official | Our app sends the daily menu and reminders **by itself**, and reads replies **by itself** | 🟡 **Later**, if sending broadcasts by hand becomes a burden |
| **C. Unofficial WhatsApp tools/bots** (apps that log in as your phone) | "Free" | ❌ **Not safe:** WhatsApp can **ban the number**, and all subscribers lose their way to reach you | — | ❌ **Don't use** |

**Questions to decide:**
- **10a.** Is it okay to **start with option A** (free) and move to B later only if needed?
  > Answer:
- **10b.** Which number do subscribers message today? Is it already a **WhatsApp Business** number, or a normal WhatsApp number?
  > Answer:
- **10c.** Is the business **registered** (GST / shop licence)? Meta asks for this to verify the business for the API.
  > Answer:

---

## ✅ Already decided (just for reference, no need to ask)

- Safety rule: **no scraping, bots or unofficial tools** for Swiggy, Zomato or WhatsApp. They can get the restaurant account suspended or the number banned. Only official routes (sections 9 and 10).
- Delivery orders go **Ready → On the way → Delivered**. Walk-ins (eat at the table) go **Ready → Served**.
- Roles: Mom and Aunt = admin (everything); hired cook = kitchen screen only; 2 delivery boys = their own deliveries; helper = no login for now.
- Orders are never deleted. Every change is recorded with who did it and when.
- The AI (later) only **suggests**. A person always approves. It can never change prices, spend money or cancel orders on its own.

---

*Sources for prices (third-party, may be out of date; always get a written quote):*
- *UrbanPiper pricing not published; reported ranges: swadeshiapps.com/business/urbanpiper, techarion.com (2025 POS comparison), codingclave.com (2026 POS roundup)*
- *WhatsApp per-message rates (India, 2026): amomic.in, digitaltoolbox.in; confirm on Meta's pricing page*
- *WhatsApp coexistence (same number on app + API): docs.360dialog.com, support.wati.io*
