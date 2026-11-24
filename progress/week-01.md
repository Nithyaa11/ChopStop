# Week 1 — Foundation & security

**Dates:** Mon 24 Nov – Mon 1 Dec 2026
**Goal:** Repo skeleton, database, health check, CI with secret scanning, login with roles, audit log.
**Time budget:** 30–60 min per day

## Plan for the week

| Day | Date | Task | Status |
|---|---|---|---|
| 0 | Mon 24 Nov | Read the design doc, pick the stage 1 scope, agree on guardrails and stack | ✅ Done |
| 1 | Tue 25 Nov | Repo skeleton, `.gitignore`, `.env.example`, Postgres in Docker Compose | ✅ Done (started early, 24 Nov). DB tested and healthy |
| 2 | Wed 26 Nov | FastAPI app, config, DB session, `/health` endpoint | ⬜ |
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
