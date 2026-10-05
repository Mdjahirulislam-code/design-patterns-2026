# Smart Greenhouse

A three-tier smart greenhouse control system developed step by step for the Design Patterns course.

The system manages greenhouse devices, locations, zones, sensors, and actuators using clean architecture principles and design patterns.

---

# Technology Stack

## Backend
FastAPI

## Database
PostgreSQL with Alembic migrations

## Frontend
React + TypeScript + Tailwind CSS v4

## Containerization
Docker Compose


**Current Phase:** Phase 5 — Adapter: sensor readings, sampling and history

---

# Project Overview

Phase 1 created the basic three-tier project structure.

Phase 2 introduced database-connected sensors.

Phase 3 added a flexible device creation system using the Factory Method pattern with multiple device families and actuator support.

Phase 4 extends the system with greenhouse locations, zones, device assignment, and configuration management.

Phase 5 reads sensors through ports and adapters (simulation, vendor stub, MQTT translator), stores every reading in `sensor_readings`, and adds a simulation sampler.

The current system supports:

- Simulation devices
- Edge devices
- Sensors
- Actuators
- Factory Method device creation
- PostgreSQL persistence
- Location management
- Zone management
- Device-zone assignment
- Frontend dashboard visualization
- Sensor reading through adapters
- Reading history in PostgreSQL
- Sampling interval and tracking per device

Project phase documentation:

- [Phase overview](docs/phases/README.md)
- [Adapter pattern note](docs/patterns/adapter.md)
- [Phase 5 questions](docs/phases/phase-05/questions.md)

---

# Phase 5 — How to run and test

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current      # 006 (head)
docker compose exec backend pytest tests -q
```

Open the dashboard at http://localhost:5173/dashboard and the API docs at http://localhost:8000/scalar.

Try the API (replace `<id>` with a sensor id from `GET /api/sensors`):

```powershell
curl.exe -X POST http://localhost:8000/api/sensors/<id>/read
curl.exe "http://localhost:8000/api/sensors/<id>/readings?limit=5"
curl.exe -X PATCH http://localhost:8000/api/devices/<id>/sampling -H "Content-Type: application/json" -d "@sampling.json"
curl.exe -X PATCH http://localhost:8000/api/devices/<id>/sampling -H "Content-Type: application/json" -d "@bad-sampling.json"   # 400
```

Check the table:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "\d sensor_readings"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT source, count(*) FROM sensor_readings GROUP BY source"
```
