# Phase 4 — VS Code Testing Guide  
## Smart Greenhouse System

---

## 1. Open Project

Open the project folder in VS Code.

Project structure:

```
docker-compose.yml
backend/
frontend/
docs/
```

---

## 2. Setup Environment

Open terminal in project root.

Create environment files:

```powershell
Copy-Item .env.example .env
Copy-Item .env backend\.env
```

---

## 3. Start Application

Make sure Docker Desktop is running.

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

## 4. Database Migration

Apply database migration:

```powershell
docker compose exec backend alembic upgrade head
```

Check migration status:

```powershell
docker compose exec backend alembic current
```

Expected:

```
(head)
```

---

## 5. Check Application URLs

Open the following:

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

Expected health response:

```json
{
  "status": "ok",
  "db": "ok"
}
```

---

# API Testing

## 6. Test Device API

Open Scalar:

```
http://localhost:8000/scalar
```

Test:

```
GET /api/devices
```

Expected:

- Sensors are returned
- Actuators are returned
- Device family information is shown

Example:

```json
{
  "device_type": "moisture_sensor",
  "role": "sensor",
  "device_family": "simulation"
}
```

---

## 7. Test Device Factory

Verify Factory Method device creation.

Simulation devices:

### Sensors

- Soil moisture sensor
- Greenhouse light sensor

### Actuators

- Irrigation pump
- Grow light


Check:

```
GET /api/devices
```

Verify devices are loaded correctly.

---

# Location and Zone Testing

## 8. Create Location Configuration

Test:

```
POST /api/locations/config
```

Example body:

```json
{
  "location_name": "Lab Site A",
  "zones": [
    {
      "name": "Zone 1",
      "moisture_threshold_low": 0.2,
      "moisture_threshold_high": 0.45,
      "schedule": {
        "watering": "08:00"
      }
    }
  ]
}
```

Verify:

- Location created
- Zone created
- Configuration saved in database

---

## 9. Test Location Configuration API

Get location configuration:

```
GET /api/locations/{location_id}/config
```

Check:

- Location information
- Zone information
- Moisture thresholds
- Watering schedule

---

## 10. Test Zone Management

Add zone:

```
POST /api/locations/{location_id}/zones
```

Update zone:

```
PATCH /api/locations/{location_id}/zones/{zone_id}
```

Delete zone:

```
DELETE /api/locations/{location_id}/zones/{zone_id}
```

Verify:

- Zone creation works
- Zone update works
- Zone deletion works

---

# Device Assignment Testing

## 11. Assign Device to Zone

Assign device:

```
PATCH /api/devices/{device_id}/zone
```

Example:

```json
{
  "zone_id": "zone_uuid"
}
```

Verify database:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT id,device_type,zone_id,location_id FROM devices;"
```

Expected:

```
device_id | device_type | zone_id | location_id
```

Assigned devices should contain:

- zone_id
- location_id

---

## 12. Test Zone Device Listing

Check devices inside a zone:

```
GET /api/locations/{location_id}/zones/{zone_id}/devices
```

Expected:

```json
[
  {
    "device_type": "moisture_sensor",
    "role": "sensor"
  }
]
```

---

# Frontend Testing

## 13. Test Dashboard

Open:

```
http://localhost:5173/dashboard
```

Verify:

 API: ok · DB: ok badge  
 Sensors section loads  
 Devices section loads  
 Simulation devices display  
 Device information displays correctly  
 Saved data remains after refresh  

---

# Database Verification

## 14. Check Database Records

Devices:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM devices;"
```

Locations:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM locations;"
```

Zones:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM zones;"
```

---

# Quality Checks

## 15. Backend Tests

Run:

```powershell
docker compose exec backend pytest tests -q
```

Expected:

```
All tests passed
```

---

## 16. Backend Lint

Run:

```powershell
docker compose exec backend ruff check src alembic tests
```

---

## 17. Frontend Check

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

# Phase 4 Final Checklist

☑ Docker services running  
☑ Database migration completed  
☑ Backend health check passes  
☑ Scalar API documentation works  
☑ Device API works  
☑ Factory Method creates devices  
☑ Sensors and actuators display correctly  
☑ Location configuration works  
☑ Zone create/update/delete works  
☑ Device-zone assignment works  
☑ Zone device listing works  
☑ PostgreSQL stores data correctly  
☑ Frontend dashboard works  
☑ Backend tests pass  
☑ Frontend build passes  

# Phase 4 Complete 