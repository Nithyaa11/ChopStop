[*C*Chopstop](#home)

[Problem](#problem)[Order journey](#journey)[12 modules](#modules)[Who sees what](#screens)[Helpers](#smart)[Money](#money)[Analytics](#analytics)[AI](#learns)[Costs](#costs)[Plan](#plan)

The system we're building

# Four order streams. One *overloaded* manager.

Chopstop is growing fast — a cloud kitchen for over a year, a new outlet for 4–5 months. But all of it runs on memory, phones and WhatsApp. We're building one system that runs the operations, keeps the money straight, understands the business — and slowly learns to improve it.

🛵 Swiggy🍽️ Zomato🥗 Subscriptions🚶 Walk-ins

**2**cooks

**2**delivery riders

**2**founders

**0**systems today

[See the problem ↓](#problem)

01 · The problem → the solution

## What a dinner rush feels like

The problem isn't the number of orders. It's how much everyone has to keep in their heads. Press **Start the rush**, then switch to **With Chopstop** and try again.

Manager stress 0%

4

places to check

0

things to remember

0

orders running late

🙂Calm… for now

Today: orders land in four separate places. Mom checks each one, works out what's urgent, tells the cooks, plans the riders, and remembers it all.

02 · How it works

## Follow one order through the system

Every order, wherever it comes from, follows the same simple path. Each screen updates live, so nobody has to shout across the kitchen.

03 · The building blocks

## 12 modules, in 4 layers

Everything Chopstop does lives in one of these modules. We build from the bottom up: operations first, intelligence last. Tap any module.

### How they connect

Each layer feeds the next, and the results loop back so future advice gets better.

1–8**Operations & records**Orders, kitchen, customers, money: what happened

→

9–10**Analytics & predictions**What it means, and what's likely next

→

11**Agent harness**Investigates and recommends

→

12**Feedback & evaluation**Did the advice actually work?

↺ Outcomes flow back into the records and improve future recommendations

04 · One system, four views

## Everyone sees only what they need

Each person has their own login. A cook doesn't see money; a rider doesn't see the kitchen. Tap a role.

05 · Smart helpers (no AI needed)

## The math the manager does in her head — automated

Two jobs that eat time every day. These are plain, predictable calculations — always the same answer for the same input.

### 🥗 Subscriptions → grocery list

Today: Mom sends two salad options on WhatsApp, tallies replies, and works out what to buy. Try it here. *(Recipes below are made-up examples.)*

Picked **Salad A**Greek: cucumber, tomato, feta

12

Picked **Salad B**Chickpea: chickpeas, cucumber, onion

8

Haven't replied yetShown clearly — never guessed

3

| Ingredient | Need | In stock | Buy |
| --- | --- | --- | --- |

Buy = need − stock + 10% safety buffer. Mom approves the list; whoever shops records what they actually bought.

### 🔥 What should the kitchen cook first?

The system works out how much **spare time** each order has, and puts the tightest at the top. Drag the clock.

7:00 PM

Spare time = due time − now − cooking time

Red = at risk of being late, flagged early so someone can act. Later, cooking times are learned from real data instead of guesses.

06 · Module 8 · Financial management

## Where does the money actually go?

Today, business and personal money are mixed, and nobody can easily say which dish truly makes money. A bestseller isn't always profitable. Try it:

### 🧮 Is this dish really making money?

Selling price

Ingredients

Packaging

Discount given

Platform commission Example rate only. We'll use the real figure once the founders confirm it.

Contribution margin = price − ingredients − packaging − commission − discount. The real system calculates it from recorded costs, never guesses.

#### 💸 It will track

Revenue by channelExpensesSwiggy/Zomato payoutsSupplier paymentsCash flowFounder contributions & withdrawalsProfit

#### 📑 Reports it will give

Daily salesWeekly / monthly revenueExpense breakdownDish profitabilitySettlement checkProfit & loss

#### ⏸️ Why it comes later

We first need the founders to explain how money flows: what's business vs personal, how founders put in and take out money, and how shared costs are settled. **The system is designed for it from day one**, so orders, groceries and purchases can link to the money records later.

07 · Modules 9 & 10 · Analytics & forecasting

## Numbers first, AI second

Analytics is a core part of the system, not a side feature of the AI. These numbers are calculated with plain SQL and Python, so they work even if the AI is switched off. Pick an area:

Actual measured from real records · Forecast a prediction (module 10) · AI note an interpretation (module 11). The dashboard always keeps these three apart.

All numbers here are made up to show what the dashboard could look like.

08 · Modules 11 & 12 · AI agent & feedback

## A system that slowly learns the business

Once the daily data is clean, the system grows in three stages. Tap each to see an example.

tap ↓

Stage 1

### Remember

Orders, preferences, kitchen tasks, groceries, packing and deliveries — all in one place.

“Mrs. Rao chose Salad B for the 5th day running. 3 subscribers haven't replied for tomorrow.”

tap ↓

Stage 2

### Understand

Loyal customers, who stopped ordering, popular dishes, busy hours, bottlenecks, revenue patterns.

“Friday 7–8 PM is the busiest hour. 18 regular customers haven't ordered in 3 weeks.”

tap ↓

Stage 3

### Advise

An AI assistant spots repeated problems, suggests fixes, and checks whether they actually worked.

“Evening orders with Dish X keep running late when orders pile up. Consider prepping its ingredients earlier.” → Mom approves → system checks a week later.

### What a recommendation looks like

Every suggestion shows its evidence and waits for a human. Then module 12 checks whether it worked. Try approving it.

AI recommendationKitchen · evening shift

👀 ObservedEvening orders with Paneer bowl ran late 7 times in 3 weeks.

📚 EvidenceEvery case was when 5+ orders arrived within 10 minutes. Prep took 9 min longer than usual.

💡 SuggestionChop and marinate the paneer before 6 PM on busy days (if food-safety and storage rules allow).

📏 ConfidenceMedium: 7 incidents is a pattern, but still a small sample.

#### 🤝 The AI can…

Spot patternsExplain whyAnswer questionsSuggest changesAsk for approvalMeasure results

#### 🛑 The AI never, on its own…

Changes pricesSpends moneyCancels ordersReassigns ridersPromises delivery timesChanges kitchen plansMakes permanent stock changes

The AI doesn't do the math either: SQL and Python calculate the numbers, and the AI explains them. And if the AI is ever down, the kitchen keeps running, because it sits on top of the system, not in the middle.

09 · Running costs

## What will it cost every month?

The system runs in the cloud, so there's a monthly bill. Pick a stage, then switch services on or off to see where the money goes. All prices are rough planning estimates in ₹, not vendor quotes.

Estimated monthly bill

₹2,000 target

₹0

#### Where the money goes (upper estimate)

#### 🛠️ Saved by building it ourselves

Order systemKitchen screenSubscriptionsGrocery mathsBasic delivery planningNo POS needed

#### ⏳ Paid only when it's worth it

Swiggy/Zomato linkWhatsApp automationMaps & routingAI assistantRedisSMS login codesPayment gateway

#### ⚠️ Not included in these numbers

Development work itself, and the Swiggy/Zomato connector fee, which is **unknown until a provider like UrbanPiper sends a written quote**. Don't commit to any provider without one.

10 · How we'll build it

## Start small, prove it, then grow

0

#### Watch for 7 days

Observe real orders, timings, rush hours and what stresses Mom most. Sit down with the founders about money.

1

#### Core operations

Modules 1–6, the MVP. Go live on the real tablet. Swiggy/Zomato orders typed in at first.

2

#### Business management

Modules 7–8: customer profiles, then finance once we understand how money flows.

3

#### Intelligence

Modules 9–10: analytics dashboards, then forecasts once there's enough history.

4

#### AI & feedback

Modules 11–12: the AI assistant and its scorecard. Paid integrations only when they've proven worth it.

⏸️ **Not at the start, on purpose:** automatic WhatsApp messages · direct Swiggy/Zomato connections · fancy route planning · anything expensive. Target running cost: about **₹2,000/month**, on a server that stays awake so the kitchen never waits.

For developers: React PWATailwindPython FastAPIPostgreSQLLive updates (WebSockets)SQL + Python analyticsLLM + harness (later)One app, neat modules

Guiding principle

Build a system that makes Chopstop easier to run — not another thing the people running it have to manage.
