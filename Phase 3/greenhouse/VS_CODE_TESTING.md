# Phase 3 — VS Code Testing Guide

## 1. Open Project

Open the project folder in VS Code.

The folder should contain:

```
docker-compose.yml
backend/
frontend/
docs/
```

---

# 2. Setup Environment

Open the terminal in the project root.

Create environment files:

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

---

# 3. Start Application

Make sure Docker Desktop is running.

Start all services:

```powershell
docker compose up --build -d
```

Check containers:

```powershell
docker compose ps
```

Expected running services:

- PostgreSQL
- Backend
- Frontend

---

# 4. Apply Database Migration

Run:

```powershell
docker compose exec backend alembic upgrade head
```

Check migration:

```powershell
docker compose exec backend alembic current
```

Expected:

```
003 (head)
```

---

# 5. Check Application URLs

Open these URLs:

Backend health:

```
http://localhost:8000/health
```

API documentation:

```
http://localhost:8000/scalar
```

Frontend dashboard:

```
http://localhost:5173/dashboard
```

Health response should show:

```json
{
  "status": "ok",
  "db": "ok"
}
```

---

# 6. Test Device API

Open Scalar:

```
http://localhost:8000/scalar
```

Test:

```
GET /api/devices
```

Expected result:

- Simulation devices
- Edge devices
- Sensors
- Actuators

Example:

```json
[
 {
  "device_type":"moisture_sensor",
  "role":"sensor",
  "device_family":"simulation"
 }
]
```

---

# 7. Test Device Factory

Check that devices are created from different factories.

Expected devices:

## Simulation

Sensors:

- Soil moisture sensor
- Greenhouse light sensor

Actuators:

- Irrigation pump
- Grow light


## Edge

Sensors:

- Edge soil moisture sensor
- Edge greenhouse light sensor

---

# 8. Test Frontend Dashboard

Open:

```
http://localhost:5173/dashboard
```

Check:

✅ Health badge shows:

```
API: ok · DB: ok
```

✅ Sensors section is visible

✅ Devices section is visible

✅ Simulation / Edge buttons work

✅ Device information loads correctly

✅ Refresh keeps saved data

---

# 9. Run Backend Tests

Run:

```powershell
docker compose exec backend pytest tests -q
```

All tests should pass.

---

# 10. Backend Lint Check

Run:

```powershell
docker compose exec backend ruff check src alembic tests
```

---

# 11. Frontend Check

Go to frontend:

```powershell
cd frontend
```

Install packages:

```powershell
npm install
```

Build:

```powershell
npm run build
```

Lint:

```powershell
npm run lint
```

---

# 12. Final Phase 3 Checklist

Before completing Phase 3, confirm:

☑ Docker services running  
☑ Database migration completed  
☑ API health check passes  
☑ Device API works  
☑ Factory Method creates devices  
☑ Simulation devices display  
☑ Edge devices display  
☑ Frontend dashboard works  
☑ Backend tests pass  
☑ Frontend build passes  

Phase 3 is complete.