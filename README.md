# Chopstop

[![CI](https://github.com/Nithyaa11/ChopStop/actions/workflows/ci.yml/badge.svg)](https://github.com/Nithyaa11/ChopStop/actions/workflows/ci.yml)

Operations and intelligence system for **Chopstop** — a cloud kitchen with one physical outlet.

Chopstop takes orders from four channels: **Swiggy, Zomato, subscriptions and walk-ins**. This system brings them into one place, runs the kitchen and delivery workflow, tracks inventory, and builds up clean operational data. Over time, an AI layer will use that data to recommend improvements.

> **Guiding principle:** make Chopstop easier to operate — not another system that creates more work for the people running it.

---

## Status

🚧 **Early development.** Building Layer 1 (core operations) first.
Done: database, secure config, migrations, append-only audit log, least-privilege DB user,
users & roles, login API, deny-by-default permissions, CI + secret scanning.
Daily progress: [`progress/`](progress/).

---

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript (Vite), Tailwind CSS, installable PWA |
| Backend | FastAPI (Python 3.12), Pydantic v2 |
| Database | PostgreSQL 16 (single source of truth) |
| Migrations | Alembic |
| ORM | SQLAlchemy 2.x |
| Live updates | WebSockets (FastAPI) |
| Auth | Argon2 password hashing + short-lived JWT, role-based access |
| Analytics | SQL views + Python (pandas), read-only DB role |
| Forecasting | statsmodels / scikit-learn (switched on once there is enough history) |
| AI harness | LLM API via a separate `harness/` package, read-only, optional |
| Order intake | Manual entry first; pluggable adapter for a POS-partner webhook later |
| Quality | ruff, pytest, pre-commit, gitleaks (secret scanning), GitHub Actions CI |
| Architecture | Modular monolith |
| Local dev | Docker Compose |

Daily progress is logged in [`progress/`](progress/).

---

## Modules

### Layer 1 — Core operations (MVP)
| # | Module | Responsibility |
|---|---|---|
| 1 | Auth & Users | Login, roles, permissions |
| 2 | Orders | Swiggy, Zomato, subscriptions, walk-ins |
| 3 | Kitchen | Queue, preparation, timers, delays |
| 4 | Subscriptions | Plans, customer preferences, daily orders |
| 5 | Inventory & Procurement | Ingredients, recipes, grocery lists |
| 6 | Packing & Delivery | Labels, assignments, routes, delivery status |

### Layer 2 — Business management (later)
| # | Module | Responsibility |
|---|---|---|
| 7 | Customers | Profiles, history, preferences |
| 8 | Finance | Revenue, expenses, settlements, cash flow, profit |

### Layer 3 — Intelligence & analytics (growth)
| # | Module | Responsibility |
|---|---|---|
| 9 | Business Analytics | Sales, menu, retention, operational KPIs |
| 10 | Forecasting | Demand, prep time, churn, inventory |

### Layer 4 — AI & infrastructure (advanced)
| # | Module | Responsibility |
|---|---|---|
| 11 | Agent Harness | Context, memory, tools, planning, policies |
| 12 | Feedback & Evaluation | Recommendation outcomes, continuous improvement |

---

## Project structure

```
chopstop/
├── backend/
│   ├── app/
│   │   ├── core/           # config, db session, auth, logging
│   │   ├── modules/        # one folder per business module
│   │   │   ├── auth/
│   │   │   ├── orders/
│   │   │   ├── kitchen/
│   │   │   ├── subscriptions/
│   │   │   ├── inventory/
│   │   │   ├── delivery/
│   │   │   ├── analytics/      # scaffolded early: SQL views + KPI functions, read-only
│   │   │   └── forecasting/    # scaffolded early: returns "not enough data" until history exists
│   │   ├── integrations/   # order intake adapters: manual (now), POS-partner webhook (later)
│   │   └── main.py
│   ├── migrations/         # Alembic
│   ├── tests/
│   └── pyproject.toml
├── harness/                # AI agent harness (separate from the app)
│   ├── context/
│   ├── memory/
│   ├── tools/
│   ├── policies/
│   └── evals/
├── frontend/               # React PWA
├── docker-compose.yml
├── .env.example
└── README.md
```

Each module contains `models.py`, `schemas.py`, `service.py` and `router.py`.

---

## Getting started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 1. Clone and configure
```bash
git clone <repo-url> chopstop
cd chopstop
cp .env.example .env      # then fill in the values
```

### 2. Start the database
```bash
docker compose up -d db
```

### 3. Run the backend
```bash
cd backend
uv sync
uv run python -m scripts.setup_db_roles   # once: creates the limited chopstop_app DB user
uv run alembic upgrade head
uv run python -m scripts.create_user     # once: create the first admin (hidden password prompt)
uv run python -m scripts.dev             # API on port 8010
```
API: http://127.0.0.1:8010 · Docs: http://127.0.0.1:8010/docs

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

---

## Everyday commands (what you should see)

Run `uv run ...` commands from `backend/` (prompt ends in `ackend>`). Docker Desktop must be running.
Dev API port is **8010** (8000/8001 are taken by other apps on this machine).

| Command | What it does | Expected output |
|---|---|---|
| `docker compose ps` *(repo root)* | Is the database up? | `chopstop-db ... Up ... (healthy)` |
| `uv run pytest -q` | All tests | `153 passed` (number grows over time) |
| `uv run ruff check .` | Lint incl. security rules | `All checks passed!` |
| `uv run alembic current` | Which migration the DB is on | `0003 (head)` |
| `uv run alembic check` | Do models match migrations? | `No new upgrade operations detected.` |
| `uv run python -m scripts.create_user` | Add a user (hidden password prompt) | `Created cook 'ravi' (id 2).` |
| `uv run python -m scripts.show_audit` | Last 20 audit entries | a table of who / action / when |
| `uv run python -m scripts.setup_db_roles` | Re-apply the limited DB user (safe to repeat) | `OK: database user 'chopstop_app' ...` |
| `uv run python -m scripts.dev` | Start the API on port 8010 | `Uvicorn running on http://127.0.0.1:8010` … `Application startup complete.` |
| `curl http://127.0.0.1:8010/health` | Is the API + DB OK? | `{"status":"ok","database":"ok"}` |
| `uv run pre-commit run --all-files` | All commit checks | every line `Passed` |

---

## API

Interactive docs (development only, switched off in production): **http://127.0.0.1:8010/docs**.
Click **Authorize**, enter a username + password, then try any endpoint.

**Deny by default:** every endpoint declares which roles may use it, and a test fails
if one doesn't. The full matrix lives in [`backend/tests/test_role_matrix.py`](backend/tests/test_role_matrix.py).

| Endpoint | admin | founder | cook | rider | Notes |
|---|:-:|:-:|:-:|:-:|---|
| `GET /health` | ✅ | ✅ | ✅ | ✅ | Public. API + DB status, no details leaked |
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ | Public. Rate-limited; locks after 5 wrong passwords (15 min) |
| `GET /auth/me` | ✅ | ✅ | ✅ | ✅ | Your own account |
| `POST /auth/change-password` | ✅ | ✅ | ✅ | ✅ | Own password; returns a new token, old ones stop working |
| `POST /auth/logout-all` | ✅ | ✅ | ✅ | ✅ | Kills every token for your account |
| `GET /users` | ✅ | ❌ | ❌ | ❌ | List accounts |
| `POST /users` | ✅ | ❌ | ❌ | ❌ | Create account |
| `POST /users/{id}/role` | ✅ | ❌ | ❌ | ❌ | Reason required; last admin protected |
| `POST /users/{id}/deactivate` | ✅ | ❌ | ❌ | ❌ | Reason required; never deleted |
| `POST /users/{id}/reset-password` | ✅ | ❌ | ❌ | ❌ | Also unlocks a locked account |

No token → `401`. Wrong role → `403`. Tokens last 60 minutes.

---

## Environment variables

See `.env.example` for the full list. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | App's connection, as the limited `chopstop_app` user |
| `MIGRATOR_DATABASE_URL` | Table owner's connection, used **only** by Alembic and the setup script |
| `JWT_SECRET` | Signing key for auth tokens |
| `JWT_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Allowed frontend origins |
| `LLM_API_KEY` | AI harness only — optional, app runs without it |

---

## Development

```bash
# Backend
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run alembic revision --autogenerate -m "message"   # new migration

# Frontend
npm run lint
npm run build
```

Pre-commit hooks (gitleaks secret scan, ruff, safety checks). Install once:
```bash
cd backend
uv run pre-commit install
uv run pre-commit run --all-files   # optional: check everything now
```

CI (GitHub Actions) runs on every push: gitleaks over the full history, ruff,
migrations on a fresh Postgres, and the test suite.

---

## Design rules

These hold across the codebase:

1. **Modules talk through services, not tables.** One module never queries another module's tables directly.
2. **No duplicate orders.** Orders have a unique `(source, external_order_id)` constraint, so the same Swiggy or Zomato order can't be entered twice.
3. **Delay is a flag, not a status.** An order can be `preparing` *and* delayed.
4. **Don't assume ingredient usage.** An order coming in doesn't mean ingredients were used; stock changes are recorded explicitly.
5. **The app works without AI.** The harness reads from the app; the app never depends on the harness.
6. **Humans approve consequential actions.** Anything the AI suggests that spends money, changes the menu or contacts customers needs approval.
7. **Manual entry first** for Swiggy and Zomato until integrations are in place.

---

## Roadmap

- [x] **Phase 0** — Repo setup, CI, database, health check
- [x] **Phase 1** — Auth, roles, user accounts
- [ ] **Phase 2** — Orders (all four channels) + kitchen queue
- [ ] **Phase 3** — Subscriptions
- [ ] **Phase 4** — Inventory, recipes, grocery lists
- [ ] **Phase 5** — Packing and delivery
- [ ] **Phase 6** — Customers and finance
- [ ] **Phase 7** — Analytics and forecasting
- [ ] **Phase 8** — Agent harness and feedback loop

---

## Contributing

1. Branch from `main`: `feat/<module>-<short-desc>` or `fix/<short-desc>`
2. Keep PRs small and scoped to one module where possible
3. CI (lint, tests, frontend build) must pass before merge
