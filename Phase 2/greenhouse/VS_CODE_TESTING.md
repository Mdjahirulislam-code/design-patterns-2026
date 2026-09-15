# Phase 2 — VS Code Testing Guide

## 1. Open project

Open the folder containing:


docker-compose.yml
backend/
frontend/
docs/


## 2. Setup environment

In the project root:

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
3. Start application

Make sure Docker Desktop is running:

docker compose up --build -d
docker compose ps

Check that PostgreSQL, backend, and frontend are running.

4. Apply migration
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current

Expected:

002 (head)
5. Check URLs

Open:

http://localhost:8000/health
http://localhost:8000/scalar
http://localhost:5173/dashboard

Health should show:

{"status":"ok","db":"ok"}
6. Test sensors

Create sensors from Scalar or API:

Moisture:

{
"type":"moisture"
}

Light:

{
"type":"light"
}

Check:

GET /api/sensors

Both sensors should appear.

7. Test frontend

Open:

http://localhost:5173/dashboard

Check:

Health badge works
Sensors section is visible
Add Moisture and Add Light buttons work
Created sensors remain after refresh
8. Run tests
docker compose exec backend pytest tests -q
9. Frontend check
cd frontend
npm install
npm run build
npm run lint