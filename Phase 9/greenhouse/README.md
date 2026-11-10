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


**Current Phase:** Phase 9 — Decorator: actuator policies and execution log

---

# Project Overview

Phase 1 created the basic three-tier project structure.

Phase 2 introduced database-connected sensors.

Phase 3 added a flexible device creation system using the Factory Method pattern with multiple device families and actuator support.

Phase 4 extends the system with greenhouse locations, zones, device assignment, and configuration management.

Phase 5 reads sensors through ports and adapters (simulation, vendor stub, MQTT translator), stores every reading in `sensor_readings`, and adds a simulation sampler.

Phase 6 adds automation strategies. Each location saves a strategy (conservative or aggressive), and evaluate recommends irrigate or wait per zone from the zone thresholds and the latest stored readings.

Phase 7 adds a location overview. One facade call returns the location, its zones with assigned devices and their newest readings, the saved strategy and the current recommendation.

Phase 8 adds the actuator lifecycle. Every actuator has a stored state (off, idle, running, error or maintenance), the domain guards every transition, and the API returns the state and the commands allowed now.

Phase 9 wraps the actuator port with decorators. A logging decorator stores every command attempt in `actuator_execution_log`, and a max-run-time decorator blocks an actuator that has been running for 30 minutes.

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
- Location overview in one request
- Persisted actuator state with guarded transitions
- Decorated actuator port with an execution log

Project phase documentation:

- [Phase overview](docs/phases/README.md)
- [Adapter pattern note](docs/patterns/adapter.md)
- [Phase 5 questions](docs/phases/phase-05/questions.md)
- [Strategy pattern note](docs/patterns/strategy.md)
- [Phase 6 questions](docs/phases/phase-06/questions.md)
- [Facade pattern note](docs/patterns/facade.md)
- [Phase 7 questions](docs/phases/phase-07/questions.md)
- [State pattern note](docs/patterns/state.md)
- [Phase 8 questions](docs/phases/phase-08/questions.md)
- [Decorator pattern note](docs/patterns/decorator.md)
- [Phase 9 questions](docs/phases/phase-09/questions.md)

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

---

# Phase 7 — How to run and test

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current      # still 007 (head), no new migration
docker compose exec backend pytest tests -q
```

Get the overview of a location (`<location-id>` from `GET /api/locations`):

```powershell
curl.exe http://localhost:8000/api/locations/<location-id>/overview
curl.exe -i http://localhost:8000/api/locations/00000000-0000-0000-0000-000000000000/overview   # 404
```

In the dashboard, the **Overview** panel shows the counts, strategy, recommendation and one card per zone. Pick a location or press Refresh to load it again.

---

# Phase 8 — How to run and test

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current      # 008 (head)
docker compose exec backend pytest tests -q
```

Get an actuator id (`role=actuator`) and try the state API:

```powershell
curl.exe "http://localhost:8000/api/devices?role=actuator"
curl.exe http://localhost:8000/api/devices/<actuator-id>/state
curl.exe -X POST http://localhost:8000/api/devices/<actuator-id>/transition -H "Content-Type: application/json" -d "@transition.json"
curl.exe -i -X POST http://localhost:8000/api/devices/<actuator-id>/transition -H "Content-Type: application/json" -d "@bad-transition.json"   # 409 while running
```

Check the table:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT device_id, state, updated_at FROM actuator_states;"
```

In the dashboard, actuator cards in the **Devices** section show a state badge (hover it to see the allowed commands) and a small "Move to" control. The **Overview** zone cards show the same badge after Refresh.

---

# Phase 9 — How to run and test

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current      # 009 (head)
docker compose exec backend pytest tests -q
```

Get an actuator id (`role=actuator`), apply a command and read the log:

```powershell
curl.exe "http://localhost:8000/api/devices?role=actuator"
curl.exe -X POST http://localhost:8000/api/actuators/<actuator-id>/apply -H "Content-Type: application/json" -d "@apply.json"
curl.exe "http://localhost:8000/api/actuators/executions?limit=20"
```

Show a blocked attempt:

```powershell
# 1. move the actuator to running
curl.exe -X POST http://localhost:8000/api/devices/<actuator-id>/transition -H "Content-Type: application/json" -d "@transition.json"

# 2. pretend it has been running for 31 minutes
docker compose exec postgres psql -U greenhouse -d greenhouse -c "UPDATE actuator_states SET updated_at = now() - interval '31 minutes' WHERE state = 'running';"

# 3. apply again: 409 "Max run time exceeded"
curl.exe -i -X POST http://localhost:8000/api/actuators/<actuator-id>/apply -H "Content-Type: application/json" -d "@apply.json"

# 4. the newest row has success=false and the policies maxRunTime and logging
curl.exe "http://localhost:8000/api/actuators/executions?limit=5"
```

Check the table:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT success, policy_applied, message, created_at FROM actuator_execution_log ORDER BY created_at DESC LIMIT 10;"
```

In the dashboard, the **Actuator execution log** block (below Devices) has a small apply control and a table of the newest rows. Press Refresh to load it again.
