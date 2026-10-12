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


**Current Phase:** Phase 6 — Strategy: automation strategy per location

---

# Project Overview

Phase 1 created the basic three-tier project structure.

Phase 2 introduced database-connected sensors.

Phase 3 added a flexible device creation system using the Factory Method pattern with multiple device families and actuator support.

Phase 4 extends the system with greenhouse locations, zones, device assignment, and configuration management.

Phase 5 reads sensors through ports and adapters (simulation, vendor stub, MQTT translator), stores every reading in `sensor_readings`, and adds a simulation sampler.

Phase 6 adds automation strategies. Each location saves a strategy (conservative or aggressive), and evaluate recommends irrigate or wait per zone from the zone thresholds and the latest stored readings.

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
- Automation strategy per location
- Irrigation recommendation per zone

Project phase documentation:

- [Phase overview](docs/phases/README.md)
- [Adapter pattern note](docs/patterns/adapter.md)
- [Phase 5 questions](docs/phases/phase-05/questions.md)
- [Strategy pattern note](docs/patterns/strategy.md)
- [Phase 6 questions](docs/phases/phase-06/questions.md)

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

---

# Phase 6 — How to run and test

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current      # 007 (head)
docker compose exec backend pytest tests -q
```

Prepare data (skip what you already have):

```powershell
# 1. create a location with one zone (band 0.2–0.45)
curl.exe -X POST http://localhost:8000/api/locations/config -H "Content-Type: application/json" -d "@location.json"

# 2. put the zone id from step 1 into assign.json, then assign a moisture sensor to the zone
curl.exe -X PATCH http://localhost:8000/api/devices/<sensor-id>/zone -H "Content-Type: application/json" -d "@assign.json"

# 3. store a reading for that sensor (the sampler also adds rows on its own)
curl.exe -X POST http://localhost:8000/api/sensors/<sensor-id>/read
```

Try the automation API (`<location-id>` from `GET /api/locations`):

```powershell
curl.exe http://localhost:8000/api/automation/strategies
curl.exe http://localhost:8000/api/locations/<location-id>/automation
curl.exe -X PUT http://localhost:8000/api/locations/<location-id>/automation -H "Content-Type: application/json" -d "@strategy.json"
curl.exe -X POST http://localhost:8000/api/locations/<location-id>/automation/evaluate
curl.exe -i -X PUT http://localhost:8000/api/locations/<location-id>/automation -H "Content-Type: application/json" -d "@bad-strategy.json"   # 400
```

Check the table:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "\d automation_rules"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT location_id, strategy_key, updated_at FROM automation_rules"
```

In the dashboard, the **Automation strategy** panel lets you pick a location and strategy, save it and evaluate.
