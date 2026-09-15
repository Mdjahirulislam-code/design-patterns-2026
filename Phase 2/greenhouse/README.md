# Smart Greenhouse

Three-tier smart greenhouse control system built phase by phase for the Design Patterns course.

**Backend:** FastAPI  
**Database:** PostgreSQL with Alembic migrations  
**Frontend:** React + TypeScript + Tailwind CSS v4  

**Current phase:** Phase 2 — Factory Method

Phase 1 is the foundation of this project. Phase 2 adds persisted moisture and light sensors using the Factory Method pattern without changing the original structure.

See `docs/phases/README.md` for the phase order.



# What Phase 2 Adds

- Full Docker Compose setup with PostgreSQL, backend, and frontend.
- A shared `devices` table for sensor storage.
- Factory Method implementation with `SensorCreator`.
- Separate creators for moisture and light sensors.
- `POST /api/sensors` for creating sensors.
- `GET /api/sensors` for listing sensors.
- Dashboard Sensors section for displaying sensors.
- Scalar documentation for sensor APIs.



# Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker Desktop | Current |
| Git | Any |


# First-Time Setup

Run commands from the project root.

## 1. Environment

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

## 2. Start Application

```powershell
docker compose up --build -d
docker compose ps
```

## 3. Apply Database Migration

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Expected migration:

```
002 (head)
```

## 4. Run Backend Tests

```powershell
docker compose exec backend pytest tests -q
```

---

# Daily Start

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

Stop:

```powershell
docker compose down
```

Use:

```powershell
docker compose down -v
```

only when deleting database data.

---

# URLs

| URL | Purpose |
|---|---|
| http://localhost:8000 | API information |
| http://localhost:8000/health | API and database health |
| http://localhost:8000/scalar | API documentation |
| http://localhost:8000/api/sensors | Sensor API |
| http://localhost:5173 | Frontend |
| http://localhost:5173/dashboard | Dashboard |

Swagger `/docs` is disabled intentionally.

---

# Project Structure

```
greenhouse/

├── docker-compose.yml
├── README.md
├── docs/
│   ├── phases/
│   └── patterns/
│       └── factory-method.md

├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_baseline.py
│   │       └── 002_devices.py
│   │
│   ├── tests/
│   │   ├── test_health.py
│   │   └── test_sensor_creators.py
│   │
│   └── src/
│       ├── domain/
│       │   └── sensors/
│       │       ├── entity.py
│       │       └── creators.py
│       │
│       ├── application/
│       │   └── sensors/service.py
│       │
│       ├── infrastructure/
│       │   └── persistence/
│       │       ├── models.py
│       │       └── device_repository.py
│       │
│       └── interfaces/api/
│           ├── health.py
│           └── sensors.py

└── frontend/
    └── src/
        ├── services/api.ts
        ├── features/sensors/SensorList.tsx
        └── pages/DashboardPage.tsx
```

---

# Testing Sensors

Create moisture sensor:

```powershell
curl.exe -X POST http://localhost:8000/api/sensors `
-H "Content-Type: application/json" `
-d '{"type":"moisture"}'
```

Create light sensor:

```powershell
curl.exe -X POST http://localhost:8000/api/sensors `
-H "Content-Type: application/json" `
-d '{"type":"light"}'
```

List sensors:

```powershell
curl.exe http://localhost:8000/api/sensors
```

Restart backend and check persistence:

```powershell
docker compose restart backend

curl.exe http://localhost:8000/api/sensors
```


# Tests

Backend:

```powershell
docker compose exec backend pytest tests -q
```

Lint:

```powershell
docker compose exec backend ruff check src alembic tests
```

Frontend:

```powershell
cd frontend

npm run build
npm run lint
```

---

# Troubleshooting

| Problem | Solution |
|---|---|
| Backend cannot connect to database | Check that Compose uses `postgres` as database host |
| `devices` table missing | Run `docker compose exec backend alembic upgrade head` |
| POST `/api/sensors` gives 404 | Check sensor router is included in FastAPI |
| Sensors disappear after restart | Check repository commit |
| Frontend cannot reach API | Check `VITE_API_BASE_URL` and CORS settings |
