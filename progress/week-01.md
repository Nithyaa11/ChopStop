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
| 3 | Thu 27 Nov | Alembic set up, first migration | ✅ Done 25 Nov. Audit log pulled forward from Day 7. 25 tests passing |
| 4 | Fri 28 Nov | CI (ruff + pytest), pre-commit with gitleaks secret scan | ✅ Done 26 Nov, together with the least-privilege DB user. 42 tests |
| 5 | Sat 29 Nov | Users table, Argon2 hashing, roles (founder, cook, rider, admin) | ✅ Done 27 Nov. 84 tests |
| 6 | Sun 30 Nov | JWT login, deny-by-default role checks on every endpoint | ⬜ |
| 7 | Mon 1 Dec | Tests proving each role is blocked where it should be; app writes to the audit log (table done Day 3) | ⬜ |

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

### Day 3 — Tue 25 Nov
**Done**
- Branch `feat/alembic-audit-log`. Added Alembic 1.20.
- `alembic.ini` contains **no DB URL**. `migrations/env.py` reads it from `.env` via the app settings, so no password is ever committed.
- `app/core/models.py`: shared `Base` with predictable constraint names, plus `TimestampMixin` (`created_at` / `updated_at`, timezone-aware, set by the DB).
- `app/db_models.py`: one place that imports every module's tables, so Alembic sees them all.
- First migration `0001`: the **`audit_log` table**. It records who, role, action, entity, before/after (JSONB), reason and request ID. Pulled forward from Day 7 because every later module writes to it.
- Applied to the dev DB: `alembic current` → `0001 (head)`.
- Moved the design doc into `docs/system-overview.md`.

**Guardrails added**
- 🔒 **Audit log is append-only, enforced by Postgres.** A trigger rejects UPDATE, DELETE and TRUNCATE, so no app bug, admin or AI can rewrite history.
- IDs can't be forced (`IDENTITY ALWAYS`), so fake rows with a chosen ID are impossible. Empty `action` or `entity_type` is rejected.
- 🔒 **Tests never touch real data.** They run on a separate `chopstop_test` DB, and the run aborts if the DB name doesn't end in `_test`.
- A test fails if a model and the migrations drift apart. Another fails if migration history splits into two branches.
- Every DB connection now has a timeout (app 3s, Alembic 5s, tests 3s), so nothing can hang forever.

**Problems hit & fixed**
- Docker Desktop wasn't running, and the test run hung for 37 min. Now tests that need the DB stop in seconds with "Is Docker Desktop running?". Pure tests (settings) no longer need Docker.
- Root cause of the hang: on Windows, `localhost` resolves to IPv6 `::1` first, but the DB only listens on `127.0.0.1`. Alembic's connection had no timeout, so it waited forever. Fixed by switching `DATABASE_URL` to `127.0.0.1` (`.env.example` and local `.env`) and adding timeouts everywhere.
- Fixed an Alembic deprecation warning (`path_separator`).

**Results:** `pytest` ✅ **25 passed** in ~2s · `ruff check` ✅ · `ruff format` ✅

**Open items**
- `httpx2` warning still parked for Day 4 (CI).
- Later (before go-live): the app should connect as a **separate, non-owner DB user** that can only INSERT/SELECT on `audit_log`. The table owner can still disable triggers, so this closes that gap.
- **Remember:** start Docker Desktop before working (`docker compose up -d db`).

**Next:** Day 4 — CI (GitHub Actions: ruff + pytest with a Postgres service) and gitleaks secret scanning in pre-commit.

### Day 4 — Wed 26 Nov (least-privilege DB user + CI & secret scanning)
**Setup**
- Docker Desktop now starts at Windows sign-in (`AutoStart` on, original settings backed up). The DB container has `restart: unless-stopped`, so the DB comes back by itself.

**Part A — least-privilege database user** (closes the gap from Day 3)
- New DB user **`chopstop_app`** for the running app: not superuser, owns nothing, can't create tables, users or databases.
- Settings split:
  - `DATABASE_URL` = app user.
  - `MIGRATOR_DATABASE_URL` = table owner, used **only** by Alembic and the setup script.
  - The app refuses to load if both point to the same user.
- `scripts/setup_db_roles.py`: idempotent. Creates or updates the user with its own random password from `.env`, and resets it to the weakest attributes every time.
- Migration `0002`:
  - The app user can only **SELECT + INSERT** on `audit_log`.
  - Future tables get normal read/write by default.
  - Nobody but the owner can create objects in the schema.
- 🔒 **The app refuses to start** if its DB user is a superuser, owns tables or the DB, or can create roles or DBs.
- 🔒 The audit log is now tamper-proof at **two layers**:
  - the app user is blocked by privileges ("permission denied")
  - even the owner is blocked by the trigger ("append-only")
- Tests show the app user **cannot**:
  - disable the audit trigger
  - drop or create tables
  - create users
  - promote itself to superuser
  - edit `alembic_version`

**Part B — Day 4: CI + secret scanning**
- **pre-commit** hooks on every `git commit`:
  - gitleaks secret scan
  - private-key detection
  - large-file block (>500 KB)
  - merge-conflict markers
  - YAML/TOML checks
  - end-of-file and whitespace fixes
  - **no direct commits to `main`**
  - ruff lint + format
- 🔒 **Found & fixed a gap:** gitleaks' default rules **missed database URLs with passwords** (tested with fake ones). Added a custom rule in `.gitleaks.toml`. Only the placeholders `change-me`, `${ENV_VAR}` and two fixed fake test values are allowed.
- Verified:
  - fake GitHub token blocked ✅
  - fake DB URLs blocked ✅
  - full git history clean ✅
  - the rule recognizes the real `.env` (which stays ignored) ✅
- **GitHub Actions CI** (`.github/workflows/ci.yml`) on every push:
  - Gitleaks over the **full history**.
  - Install must match `uv.lock` exactly (`uv sync --locked`).
  - ruff lint + format.
  - Fresh Postgres: create the app user, `alembic upgrade head`, `alembic check` (models match migrations).
  - pytest.
- CI guardrails: workflow token is read-only; per-run random passwords and JWT secret, masked in logs.
- README: CI badge, setup step for the DB user, new env var, pre-commit instructions.

**Problems hit & fixed**
- I put a ruff `noqa` comment *inside* a SQL string by mistake, which would have broken the migration. Caught before running it. Fixed with a documented per-folder exception (`migrations/versions/**` may interpolate only validated constants), and the migration now checks the role name against a strict regex.

**Results:** `pytest` ✅ **42 passed** in ~1.6s · `ruff` ✅ · `pre-commit --all-files` ✅

**Open items**
- `httpx2` deprecation warning still parked (package not yet vetted).
- Before go-live: the owner user on the server should not be a superuser either (go-live checklist).
- Tip: in VS Code, pick `backend/.venv` as the Python interpreter (Ctrl+Shift+P → "Python: Select Interpreter") so imports stop showing as "not installed".

**Next:** Day 5 — `users` table, Argon2 password hashing, roles (founder, cook, rider, admin).

### Day 5 — Thu 27 Nov (users, roles, password hashing)
**Done**
- Branch `feat/users-roles`. Added `argon2-cffi`.
- `app/core/security.py`:
  - **Argon2id** hashing (RFC 9106 profile: t=3, 64 MiB, p=4).
  - Password rules: 10–128 chars, not a common password, at least 4 different characters, must not contain the username.
- `users` table (migration `0003`):
  - Fields: username, display name, role, password hash, active flag.
  - Login protection fields for Day 6: failed-login count, `locked_until`, `token_version`, `last_login_at`.
- 4 roles: **admin** (accounts), **founder** (business, money, reports), **cook** (kitchen only, no money), **rider** (own deliveries only).
- `users/service.py`: create user, set password, change role, deactivate. Every change writes an audit entry in the same transaction.
- `audit/service.py`: `record()` used by all modules.
- `scripts/create_user.py`: creates the first admin. The password is typed at a hidden prompt, never as an argument (keeps it out of shell history).
- DB container auto-recovered when Docker started (restart policy works). Auto-start at sign-in applies after the next Windows sign-in; the PC hasn't restarted since 17 Nov.

**Guardrails added**
- 🔒 **Database-enforced:**
  - role must be one of the 4
  - username lowercase `a-z 0-9 . _ -`, 3–32 chars, unique
  - `password_hash` must be an Argon2id hash, so plaintext **can't** be stored even by a buggy insert
- 🔒 **Users can never be deleted:** the app DB user has no DELETE/TRUNCATE on `users`. Deactivate instead, so audit history always points at a real person.
- 🔒 `audit_log.actor_user_id` must reference a real user (foreign key).
- 🔒 **Only admins manage accounts**, checked in the service (defence in depth; Day 6 adds the API check).
  - Users may change their *own* password.
  - Founder/cook/rider can't create users or reset others' passwords.
- 🔒 **The last active admin can't be deactivated or demoted** (no lock-out).
- Role change, deactivation and password change **bump `token_version`**, so old logins stop working (used by Day 6 tokens).
- Reason is required for role changes and deactivation, and stored in the audit log.
- 🔒 **Audit redaction:** password, hash, token, secret, api_key, OTP and PIN fields are replaced with `[REDACTED]` at any depth. Whole-word matching, so `shipping_address` isn't wrongly hidden.
- Login timing safety ready for Day 6: `verify_password(None, pw)` takes the same time when the user doesn't exist, so usernames can't be probed.
- The hash never appears in API responses (`UserOut`) or `repr()`.

**Problems hit & fixed**
- Docker Desktop had been closed; restarted it and the DB came back by itself.
- Alembic's draft wrote `LIKE '$argon2id$%%'`. The doubled `%` could have been stored literally and blocked every real hash. Replaced with `left(password_hash, 10) = '$argon2id$'`; a test inserts real and fake hashes to prove it.
- First version of redaction matched substrings (`pin` would hide `shipping_address`). Switched to whole-word matching, with a test.

**Results:** `pytest` ✅ **84 passed** · `ruff` ✅ · `alembic check` ✅ (models = migrations)

**👉 Your step:** create the first admin account (choose your own password):
`cd backend` → `uv run python -m scripts.create_user` → role `admin`

**Next:** Day 6 — login API: JWT tokens, deny-by-default role checks on every endpoint, lockout after repeated failures, rate limiting.
