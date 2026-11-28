# Guide for Mom: getting Swiggy and Zomato orders into our app automatically

**Prepared by:** Nithyaa · **Date:** 29 Nov 2026

**Why you're reading this:** today, Swiggy and Zomato orders come in on their own apps, and someone has to watch them, remember them and tell the kitchen. We're building our own Chopstop app so all orders appear in **one place**, by themselves. This guide explains how that can happen, what it costs, what is safe, and what we need from you. Nothing here is decided yet: **you decide**.

---

## 1. What we want

- When a customer orders on **Swiggy or Zomato** and you accept it, the order **appears in the Chopstop app by itself**. Nobody types it again.
- When a dish **runs out**, it is **switched off on Swiggy and Zomato at the same time**, so customers can't order something we can't cook.
- When you **change a price or the menu**, it changes **on both apps together**.
- All orders (**Swiggy, Zomato, subscriptions, walk-ins**) show on **one screen**, the most urgent on top.

---

## 2. Why we can't connect to Swiggy and Zomato ourselves

Swiggy and Zomato **do not allow** small restaurants or developers to connect directly to their systems. They only allow a few **approved companies** to do it.

**Think of it like this:** you can't walk into the bank's back office and move money yourself. You use an approved app, like GPay or PhonePe, which the bank trusts. In the same way, we need an **approved "middle company"** that Swiggy and Zomato trust. It takes the orders from them and passes them to our app.

**Our app is the kitchen. The middle company is the delivery van that brings the orders to it.**

---

## 3. The middle companies we found

| Company | What we know | Price | Verdict |
|---|---|---|---|
| **UrbanPiper** | The biggest and best known in India. Does orders + menu + stock sync | **Not published.** Others report roughly ₹700 to ₹15,000 per month depending on the plan | ✅ Ask them first |
| **LimeTray** (their tool is called "Merge") | Connects restaurant systems to Swiggy and Zomato. Friendlier to small restaurants | Not published | ✅ Ask them too |
| **Restrologic** | Says it connects custom systems to Swiggy and Zomato | Prices we found **don't match** each other (one says ₹24,999 setup, another ₹49,999 + minimum 25 outlets). Their website says it is for **large** businesses | 🟡 Ask, but check carefully |

**Important:** none of these companies have a "sign up and pay online" button. **You have to talk to their sales person first.** That person is called the **POC** (point of contact). Only after talking to them do we get a price and can start.

**Prices on websites are not reliable. We only trust a written quote** (a price on their letterhead or email).

---

## 4. What is NOT safe (never do these)

Some people use shortcuts. **We will not**, because they can shut down our business on these apps:

- ❌ **Apps or tools that "read" the Swiggy/Zomato screen or phone notifications** and copy orders automatically. This **breaks Swiggy/Zomato rules**, and they can **suspend our restaurant account**. It also breaks every time their app updates.
- ❌ **Unofficial WhatsApp bots** (apps that log in as your phone to send messages). WhatsApp can **ban the number**, and all our subscribers would lose their way to reach us.

**Rule:** only official, approved companies. If something sounds "free and automatic", it is usually one of these unsafe shortcuts.

---

## 5. Why not just use Petpooja (a POS)?

A **POS** (like Petpooja) is a complete billing software for restaurants: it prints bills, makes GST invoices, keeps the menu, tracks stock, and also connects to Swiggy and Zomato.

**Good points of a POS:**
- Ready to use in a few days, with a support team
- **GST bills and printed invoices** (our app does not do billing)

**Why we're not choosing it as the main system:**
- We'd be **paying for many things we're already building** (kitchen screen, menu, stock, reports).
- It does **not** do what makes our kitchen different: **daily salad subscriptions**, the **grocery list from subscribers' choices**, the **business vs personal money** picture, and our **smart suggestions** later.
- Our **data would live in their system**, not ours.
- If we later offer Chopstop to other kitchens, Petpooja would be a **competitor**.

**So the plan:** use a **middle company (like UrbanPiper)** only for the one thing we can't do ourselves (talking to Swiggy and Zomato), and keep **our own app** as the main system.

**When a POS would make sense:** only if **GST billing and printed invoices** are very important to you. Then we'd pick a POS that can **also send orders to our app**.

---

## 6. "But UrbanPiper also has some of the same features?"

Yes, some overlap, and that's fine:

| Thing | UrbanPiper | Our Chopstop app |
|---|---|---|
| Bring Swiggy/Zomato orders in | ✅ (we can't) | uses UrbanPiper for this |
| Update menu, price, stock on Swiggy/Zomato | ✅ (we can't) | uses UrbanPiper for this |
| Order screen | Only Swiggy/Zomato orders | **All 4**: Swiggy, Zomato, subscriptions, walk-ins |
| Kitchen order "most urgent first", late warnings | ❌ | ✅ |
| Subscriptions + grocery list | ❌ | ✅ |
| Real profit after commission, business vs personal money | ❌ | ✅ |
| Logins for our team (cook sees only cooking, riders only deliveries) | ❌ | ✅ |

**Think of UrbanPiper as a supplier**, like our vegetable or gas supplier: it gives us one service. Our app is where we **run the business**.

**Don't pay twice:** ask only for the plan that has (1) **sending orders to our app** and (2) **menu, price and stock sync**. Skip their billing/POS extras unless you want them.

---

## 7. Switching dishes on and off automatically: our safety rules

Turning a dish off on Swiggy/Zomato affects sales, so:

- **Turning OFF** a dish when stock hits zero can happen **automatically** (it protects customers from orders we can't cook).
- **Turning it back ON** needs **you or Aunt** to confirm, so a counting mistake can't re-open sales by accident.
- **Changing prices** always needs **you or Aunt**.
- Every change is **recorded**: who did it and when. Nothing can be secretly changed or deleted.
- Later, the "smart assistant" can only **suggest** (for example, "Greek Salad sold out by 7 PM three Fridays in a row, make more?"). It can **never** change prices, switch dishes or cancel orders by itself.
- If the middle company is down, **our app keeps working** and shows a clear warning.

---

## 8. How to start: step by step

1. **You (or Aunt) are the main contact.** It's your restaurant, your licence and your Swiggy/Zomato accounts. Nithyaa joins the calls as "our tech person".
2. **We contact all three companies at the same time** (UrbanPiper, LimeTray, Restrologic). This gives us prices to compare.
3. **We introduce ourselves as a restaurant**, not as "someone building software". That's the truth, and restaurants get a proper sales person faster.
4. **They call back.** Ask the questions in section 10.
5. **They send a written quote.** Nithyaa compares them (total cost, how well they fit our app, the safety checks).
6. **You decide** which one, or none.
7. **Meanwhile nothing stops.** Our app is being built so that orders can be typed in for now. When the company is ready, it **plugs in** without rebuilding anything.

---

## 9. Keep these ready (they will ask)

- **FSSAI licence number**
- **Swiggy restaurant ID** (found in the Swiggy partner app or on Swiggy's emails)
- **Zomato restaurant ID** (found in the Zomato partner app or on Zomato's emails)
- **Outlet address**
- **Roughly how many orders a day** on Swiggy and on Zomato
- **Your budget** for this per month (for comparing quotes)
- **GST number**, if registered

---

## 10. Questions to ask them on the call

1. **What is the total cost** for **1 outlet, Swiggy + Zomato**? Setup fee + monthly or yearly + GST.
2. Can you **send each order to our own app** automatically? (They may call it a "webhook" or "POS API". Nithyaa will handle the details.)
3. Can you **update our menu, prices and "out of stock" on Swiggy and Zomato** from our app?
4. **What happens if your system is down?** Do orders wait and arrive later, or get lost?
5. Can we still **accept or reject orders in the Swiggy/Zomato apps**, or only through you?
6. **How long is the contract?** Can we **stop any month**? Do we get our menu and order data back if we leave?
7. Can you give us **2–3 small restaurants** who use you now?

**Warning signs (be careful if you see these):**
- They won't give a **written price**.
- Only a WhatsApp number, no **company name, GST number or contract**.
- They ask for our **Swiggy/Zomato passwords** (a real partner never needs your password).
- They push a **long contract** with no way to cancel.

---

## 11. Message to send them (copy, fill the blanks, send by email or their website form)

**Subject:** Swiggy + Zomato integration for 1 cloud kitchen with an in-house system

Hello,

We run Chopstop, a cloud kitchen in ________ (1 outlet), live on Swiggy and Zomato, with about ____ orders a day across both.

We have our own in-house order system and would like Swiggy and Zomato orders to reach it automatically, and to keep our menu, prices and item availability in sync on both platforms.

Could you please share: (1) your plans and total cost (setup + monthly/yearly, incl. GST) for 1 outlet; (2) whether you can send orders to our own system (webhook / API); (3) menu, price and stock sync to Swiggy and Zomato; (4) what happens to orders if your service is down; (5) contract length and how to cancel.

FSSAI licence: ________ · Swiggy restaurant ID: ________ · Zomato restaurant ID: ________

Contact: ________ (owner) · Phone: ________

Thank you, ________

---

## 12. WhatsApp for subscriptions (the same idea)

Today you send 2 salad options on WhatsApp and count the replies by hand. Two safe ways to make this easier:

| Option | Cost | What happens | Verdict |
|---|---|---|---|
| **A. Normal WhatsApp Business app + a "pick" link** | **Free** | You send one message with a link. Each subscriber taps Salad A or B. Their choice goes **straight into our app**, with no counting. Our app shows who hasn't replied, and you send them a reminder with one tap | ✅ **Start here** |
| **B. Official WhatsApp "API"** (through a company like Interakt, AiSensy or Wati) | **Paid:** their monthly fee + WhatsApp charges per message (about ₹0.86 per marketing message, about ₹0.12 per reminder-type message, + GST) | Our app sends the daily menu and reminders **by itself** | 🟡 **Later**, only if sending the message yourself becomes a burden |

Good to know about option B:
- It needs a **Meta (Facebook) business account** and **business documents** (GST or shop licence) for verification.
- WhatsApp now allows the **same number** to stay on your phone **and** be connected, so subscribers don't need a new number.

---

## 13. What we need from you: decisions

- **A.** Is it okay to contact **UrbanPiper, LimeTray and Restrologic** for written quotes?
  > Answer:
- **B.** Who should be the **main contact** for them: you or Aunt?
  > Answer:
- **C.** What **monthly budget** is okay for automatic Swiggy/Zomato orders? ₹______ / month
  > Answer:
- **D.** Do you need **GST bills / printed invoices** from the system? (If yes, a POS may be worth considering.)
  > Answer:
- **E.** Is it okay that a dish is switched **off automatically** when stock runs out, but switched **on only by you or Aunt**?
  > Answer:
- **F.** For subscriptions, is it okay to **start with the free option** (WhatsApp Business app + pick link)?
  > Answer:
- **G.** Do we have the **FSSAI licence**, **Swiggy ID**, **Zomato ID** and **GST number** handy? Where are they kept?
  > Answer:

---

*Prices are from public websites and reviews (checked 28–29 Nov 2026) and may be out of date. We only rely on written quotes.*
