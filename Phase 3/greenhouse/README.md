# Smart Greenhouse

A three-tier smart greenhouse control system developed step by step for the Design Patterns course.

The system manages greenhouse devices such as sensors and actuators using a clean architecture approach and design patterns.

## Technology Stack

**Backend:** FastAPI  
**Database:** PostgreSQL with Alembic migrations  
**Frontend:** React + TypeScript + Tailwind CSS v4  
**Containerization:** Docker Compose  

**Current Phase:** Phase 3 — Device Factory using Factory Method

---

# Project Overview

Phase 1 created the basic three-tier project structure.

Phase 2 added database-connected sensors using the Factory Method pattern. Moisture and light sensors can be created, stored in PostgreSQL, and displayed on the dashboard.

Phase 3 extends the system by adding different device families and supporting both sensors and actuators.

The current system supports:

- Simulation devices
- Edge devices
- Sensors
- Actuators
- Database persistence
- Factory Method based device creation
- Frontend dashboard display

Project phase details can be found here:

```
docs/phases/README.md
```

---

# Phase 3 Features

Phase 3 adds a flexible device creation system.

## Added Features

- Device abstraction and entity model
- Factory Method implementation for devices
- Multiple device families:
  - Simulation
  - Edge
- Support for sensors and actuators
- Device repository for database operations
- PostgreSQL device storage
- API endpoints for devices
- Frontend device dashboard
- Device family switching

## Supported Devices

### Sensors

- Soil moisture sensor
- Greenhouse light sensor

### Actuators

- Irrigation pump
- Grow light

---

# Architecture

The project follows a three-tier architecture:

```
Frontend (React)
        |
        |
Backend API (FastAPI)
        |
        |
Persistence Layer
        |
        |
PostgreSQL Database
```

---

# Design Pattern

## Factory Method Pattern

The Factory Method pattern is used to create greenhouse devices without changing the main application logic.

Instead of creating objects directly, the application uses factory classes.

Example:

```
Device Factory
       |
       |
 -------------------
 |                 |
Simulation       Edge
Factory          Factory
 |                 |
Devices           Devices
```

This makes it easier to add new device types in future phases.

---

# Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker Desktop | Current |
| Git | Any |

---

# First Time Setup

Run all commands from the project root folder.

## 1. Create Environment Files

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

---

## 2. Start Application

Build and start all services:

```powershell
docker compose up --build -d
```

Check running containers:

```powershell
docker compose ps
```

Expected services:

- PostgreSQL
- Backend
- Frontend

---

## 3. Apply Database Migration

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

# Daily Start

Start application:

```powershell
docker compose up --build -d
```

Apply migrations:

```powershell
docker compose exec backend alembic upgrade head
```

---

# Stop Application

Normal stop:

```powershell
docker compose down
```

Remove database data:

```powershell
docker compose down -v
```

Use `down -v` only when you want to completely reset the database.

---

# Application URLs

| URL | Purpose |
|---|---|
| http://localhost:8000 | Backend information |
| http://localhost:8000/health | API and database health |
| http://localhost:8000/scalar | API documentation |
| http://localhost:8000/api/devices | Device API |
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
│   │       ├── 002_devices.py
│   │       └── 003_device_families.py
│
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_sensor_creators.py
│   │   └── test_device_factory.py
│
│   └── src/
│
│       ├── domain/
│       │
│       │   └── devices/
│       │       ├── entity.py
│       │       └── factories.py
│
│       ├── application/
│       │   └── devices/
│       │       └── service.py
│
│       ├── infrastructure/
│       │   └── persistence/
│       │       ├── models.py
│       │       └── device_repository.py
│
│       └── interfaces/
│           └── api/
│               ├── health.py
│               ├── sensors.py
│               └── devices.py


└── frontend/

    └── src/

        ├── services/
        │   └── api.ts

        ├── features/
        │   └── sensors/
        │       └── SensorList.tsx

        ├── components/
        │   └── devices/
        │       ├── DeviceList.tsx
        │       └── DeviceFamilySwitcher.tsx

        └── pages/
            └── DashboardPage.tsx
```

---

# API Testing

## Get Devices

```powershell
curl.exe http://localhost:8000/api/devices
```

Example response:

```json
[
  {
    "device_type": "moisture_sensor",
    "role": "sensor",
    "device_family": "simulation",
    "display_name": "Soil moisture sensor"
  }
]
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

---

# Testing

## Backend Tests

```powershell
docker compose exec backend pytest tests -q
```

## Backend Lint

```powershell
docker compose exec backend ruff check src alembic tests
```

## Frontend Build

```powershell
cd frontend

npm run build
```

## Frontend Lint

```powershell
npm run lint
```

---

# Troubleshooting

| Problem | Solution |
|---|---|
| Backend cannot connect to database | Check PostgreSQL service and database host |
| Device table missing | Run Alembic migration |
| API returns 404 | Check FastAPI router registration |
| Devices disappear after restart | Check repository save and database commit |
| Frontend cannot reach backend | Check API URL and CORS settings |

---

# Future Improvements

Possible future phases can add:

- Automatic greenhouse rules
- Sensor data history
- Real IoT device connection
- Actuator controls
- Notifications and alarms
- Greenhouse overview dashboard

---

# Author

Smart Greenhouse project created for the Design Patterns course.