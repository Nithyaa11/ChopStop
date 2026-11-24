# Week 1 — Foundation & security

**Dates:** Mon 24 Nov – Mon 1 Dec 2026
**Goal:** Repo skeleton, database, health check, CI with secret scanning, login with roles, audit log.
**Time budget:** 30–60 min per day

## Plan for the week

| Day | Date | Task | Status |
|---|---|---|---|
| 0 | Mon 24 Nov | Read the design doc, pick the stage 1 scope, agree on guardrails and stack | ✅ Done |
| 1 | Tue 25 Nov | Repo skeleton, `.gitignore`, `.env.example`, Postgres in Docker Compose | ✅ Done (started early, 24 Nov). DB tested and healthy |
| 2 | Wed 26 Nov | FastAPI app, config, DB session, `/health` endpoint | ✅ Done (started early, 24 Nov). 16 tests passing |
| 3 | Thu 27 Nov | Alembic set up, first migration | ⬜ |
| 4 | Fri 28 Nov | CI (ruff + pytest), pre-commit with gitleaks secret scan | ⬜ |
| 5 | Sat 29 Nov | Users table, Argon2 hashing, roles (founder, cook, rider, admin) | ⬜ |
| 6 | Sun 30 Nov | JWT login, deny-by-default role checks on every endpoint | ⬜ |
| 7 | Mon 1 Dec | Append-only audit log, tests proving each role is blocked where it should be | ⬜ |

**Alongside the coding (stage 0, no code):** watch 7 days of real orders. For each day, note the number of Swiggy, Zomato, walk-in and subscription orders, the rush hours, and what caused stress. This decides whether paid Swiggy/Zomato integration is worth it.

---

## Daily log

### Day 0 — Mon 24 Nov
**Done**
- Read *Chopstop — The System We're Building* and the README.
- Stage 1 scope agreed: modules 1–6 (MVP) live by 25 Dec. Analytics and forecasting get scaffolded early and turn on once real data exists.
- Guardrail rules agreed: enforced in code and the DB, every guardrail has a test, the AI is read-only and needs human approval.
- Swiggy/Zomato intake decided: fast manual entry now, a pluggable adapter for a POS-partner webhook later. No scraping.
- WhatsApp decided: no Business API and no unofficial bots. The broadcast message carries a "pick your salad" link to our app, and reminders go out as tap-to-send wa.me links.
- README stack updated; added `analytics/`, `forecasting/` and `integrations/` to the planned structure.

**Next:** Day 1 — repo skeleton and Postgres.

**Blockers / questions for founders**
- Real Swiggy/Zomato commission rates.
- How money moves between business and personal (needed for module 8).

### Day 1 — Mon 24 Nov (started early)
**Done**
- Branch `feat/repo-skeleton`.
- Folder skeleton matching the README: `backend/app/{core,modules/*,integrations}`, `backend/{migrations,tests}`, `harness/*`, `frontend/`.
- `README` renamed to `README.md`.
- `.gitignore`: keeps out secrets (`.env`, keys), DB dumps and backups, Python and Node build files, OS junk.
- `.env.example`: placeholders only, plus an LLM monthly budget cap setting.
- Local `.env` created with randomly generated DB password and JWT secret. Checked that git ignores it.
- `.gitattributes`: LF line endings.
- `docker-compose.yml`: Postgres 16.

**Guardrails added**
- DB port bound to `127.0.0.1` only.
- No default DB password: compose refuses to start without one.
- DB data lives in a Docker volume, outside the repo and OneDrive.
- Secrets and backups can't be committed by accident.

**Docker installed later the same day, DB tested**
- `docker compose up -d db`: Postgres 16.16 healthy, port only on `127.0.0.1:5432`.
- 🔒 Found a gap: by default the Postgres image trusts connections made from inside the container, without a password. Fixed with `POSTGRES_INITDB_ARGS` (scram-sha-256 for every connection) and recreated the empty DB.
- Guardrail tests, all passing:
  - ✅ correct password connects
  - ✅ wrong password rejected (inside the container)
  - ✅ no password rejected
  - ✅ wrong password from another container rejected
  - ✅ compose refuses to start with no password set

**Not done / blockers**
- `uv` not installed yet. It's needed on Day 2 for the backend.
- VS Code was opened before Docker was installed, so its terminals don't see `docker` yet. Restart VS Code to fix.

**Next:** Day 2 — FastAPI app with `/health` that also checks the DB.

### Day 2 — Mon 24 Nov (started early)
**Done**
- Branch `feat/backend-health`.
- `backend/pyproject.toml`:
  - Python 3.12.
  - FastAPI, SQLAlchemy 2, psycopg 3, pydantic-settings.
  - Dev tools: pytest, httpx, ruff, with ruff's security rules (`S`) switched on.
- `app/core/config.py`: settings read from `.env`.
- `app/core/db.py`: DB engine with a 3s connect timeout and dead-connection checks; one session per request.
- `app/main.py`: `/health` endpoint.
- Tests:
  - `tests/test_config.py`: 13 checks on unsafe settings.
  - `tests/test_health.py`: health OK, health when the DB is down, and an unknown origin being blocked.

**Guardrails added**
- The app refuses to start with:
  - a weak or placeholder `JWT_SECRET` (needs 32+ random characters)
  - the placeholder DB password
  - a wildcard `*` in CORS
  - a token lifetime outside 5 min–24 h
- Secrets are hidden in logs and printouts (`SecretStr`).
- When the DB is down, `/health` returns 503 with a generic message. It never shows the error or connection string; the full error is logged server-side only.
- API docs (`/docs`) are switched off in production.
- CORS only allows the listed origins and the methods and headers we use.

**Verified**
- User installed uv 0.13.9 manually (Claude's auto mode blocked the install script).
- `uv sync`: Python 3.12.16 set up, packages locked in `uv.lock`.
- `ruff check`: all checks passed, including the security rules. `ruff format --check`: clean.
- `pytest`: ✅ **16 passed** (13 settings guardrails + 3 health/CORS).
- Live run: started the server, `GET /health` returned `200 {"status":"ok","database":"ok"}` against the real Docker DB.

**Open items**
- ⚠️ One harmless test warning: the Starlette test client suggests `httpx2` instead of `httpx`. Not switched yet, because a new package should be checked first (supply-chain safety). Revisit when we set up CI on Day 4.

**Next:** Day 3 — Alembic and the first migration.
