# Smart Greenhouse

Three-tier smart greenhouse control system built phase by phase for the Design Patterns course:
**FastAPI** backend, **PostgreSQL** database with **Alembic** migrations, **React + TypeScript + Tailwind CSS v4** frontend.

**Current phase:** Phase 1 — Skeleton. The stack runs end to end, but there is no greenhouse
business logic and no design pattern yet. See [docs/phases/README.md](docs/phases/README.md) for the phase order.

---

## Prerequisites

| Tool | Minimum version | Verify |
|------|-----------------|--------|
| Python | 3.11+ | `python --version` |
| Node.js | 20 LTS | `node --version` |
| Docker Desktop | current | `docker --version` |
| Git | any | `git --version` |

---

## First-time setup

Run these once, from the repository root (the folder containing `docker-compose.yml`).

### 1. Environment file

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

`.env` is gitignored. `.env.example` is committed and shows every variable that is needed.

### 2. Start PostgreSQL

```powershell
docker compose up -d
docker compose ps
```

Wait until the `greenhouse-postgres` service reports **healthy**.

### 3. Install the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 4. Apply the database baseline migration

```powershell
alembic upgrade head
alembic current    # should print: 001 (head)
```

### 5. Install the frontend

```powershell
cd ..\frontend
npm install
Copy-Item .env.example .env
```

---

## Daily start (three terminals)

```text
Terminal 1: docker compose up -d
Terminal 2: cd backend; .\.venv\Scripts\Activate.ps1; cd src; uvicorn main:app --reload --port 8000
Terminal 3: cd frontend; npm run dev
```

Uvicorn must be started from `backend\src` so that imports such as `infrastructure.db` resolve.

Stop the database with `docker compose down` (add `-v` to also delete the data volume).

---

## URLs

| URL | What it is |
|-----|------------|
| http://localhost:8000/ | API discovery payload |
| http://localhost:8000/health | Health check: `{"status":"ok","db":"ok"}` |
| http://localhost:8000/scalar | Scalar API reference (Swagger `/docs` is disabled on purpose) |
| http://localhost:8000/openapi.json | OpenAPI schema |
| http://localhost:5173/ | Frontend home |
| http://localhost:5173/dashboard | Dashboard with placeholder sections |

---

## Project layout

```text
.
├── docker-compose.yml          PostgreSQL 16 with healthcheck
├── .env.example                Committed template; copy to .env
├── docs/phases/README.md       Phase order
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py              Reads DATABASE_URL from application settings
│   │   └── versions/001_baseline.py   Empty baseline, no business tables
│   ├── tests/test_health.py
│   └── src/
│       ├── main.py             FastAPI app, CORS, Scalar
│       ├── domain/             Business entities and rules (empty in Phase 1)
│       ├── application/        Use cases (empty in Phase 1)
│       ├── infrastructure/     settings.py, db.py
│       └── interfaces/api/     health.py└── frontend/src/
    ├── services/api.ts         Typed API client (the only place that calls fetch)
    ├── components/AppLayout.tsx, HealthStatus.tsx
    └── pages/HomePage.tsx, DashboardPage.tsx
```

---

## Tests and linting (optional)

```powershell
cd backend
$env:PYTHONPATH="src"; pytest -q
ruff check src alembic tests
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `"db": "fail"` | Postgres down or wrong `DATABASE_URL` | `docker compose ps`; check `.env` |
| Port 5432 already in use | A local Postgres is installed | Change `POSTGRES_PORT` in `.env` |
| Alembic cannot connect | `.env` missing in `backend/` | Copy `.env` to `backend\.env` |
| `ModuleNotFoundError: infrastructure` | Uvicorn started from the wrong folder | Run it from `backend\src` |
| CORS error in the browser | Origin not allowed | Check `CORS_ORIGINS` in `.env` |
| Badge shows "API: unreachable" | Backend not running | Start Terminal 2 |
