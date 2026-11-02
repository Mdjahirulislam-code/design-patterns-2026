# Phase 8 — VS Code Testing Guide  
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
008 (head)
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

# Sensor Reading Testing (Phase 5 — Adapter)

## 13. Read a Sensor

Get a sensor id:

```
GET /api/sensors
```

Read the sensor now:

```
POST /api/sensors/{sensor_id}/read
```

Expected: `201 Created`

```json
{
  "device_id": "<uuid>",
  "value": 0.31,
  "unit": "vwc",
  "source": "simulation",
  "recorded_at": "2026-10-13T09:00:00Z"
}
```

Verify:

- Moisture values are between 0.2 and 0.6 vwc
- Light values are between 200 and 2000 lux
- A vendor sensor ("Add vendor moisture" button) returns `"source": "vendor"`
- A missing device returns `404`

List stored readings, newest first:

```
GET /api/sensors/{sensor_id}/readings?limit=5
```

---

## 14. Test Sampling Settings

Update interval and tracking:

```
PATCH /api/devices/{device_id}/sampling
```

Example body (sampling.json):

```json
{
  "sampling_interval_seconds": 10,
  "tracking_enabled": true
}
```

Verify:

- Settings are saved and returned
- An interval below 5 (bad-sampling.json) returns `400` with "must be at least 5"
- With tracking on, new readings appear on their own after the interval
- With tracking off, no new readings are added by the sampler

---

## 15. Check Readings in the Database

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "\d sensor_readings"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT source, count(*) FROM sensor_readings GROUP BY source;"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT display_name, sampling_interval_seconds, tracking_enabled FROM devices;"
```

Expected:

- `sensor_readings` has a foreign key to `devices`
- Index on `(device_id, recorded_at DESC)`
- Every device has an interval and a tracking value

---

# Automation Strategy Testing (Phase 6 — Strategy)

## 16. Prepare Data

The location needs a zone with a moisture sensor and a stored reading.

1. Create a location if there is none (section 8)
2. Get the zone id with `GET /api/locations/{location_id}/config`
3. Assign a moisture sensor to that zone (section 11)
4. Read the sensor (section 13)

---

## 17. Test Strategy API

List strategies:

```
GET /api/automation/strategies
```

Expected: `conservative` and `aggressive`

Get the saved strategy of a location:

```
GET /api/locations/{location_id}/automation
```

Before anything is saved, `"strategy_key": "conservative"` and `"is_default": true` are returned.

Save a strategy:

```
PUT /api/locations/{location_id}/automation
```

Example body (strategy.json):

```json
{
  "strategy_key": "aggressive"
}
```

Evaluate with the saved strategy:

```
POST /api/locations/{location_id}/automation/evaluate
```

Expected:

```json
{
  "location_id": "<uuid>",
  "strategy_key": "aggressive",
  "action": "irrigate",
  "reason": "Moisture 0.33 is below the high threshold 0.50, topping up early",
  "zones": [ ... ]
}
```

Verify:

- With moisture inside the zone band, conservative returns `wait` and aggressive returns `irrigate`
- A zone without a moisture sensor returns `wait` with "No moisture sensor in this zone"
- An unknown strategy (bad-strategy.json) returns `400`
- A missing location returns `404`

---

## 18. Check Strategy in the Database

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "\d automation_rules"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT location_id, strategy_key, updated_at FROM automation_rules;"
```

Expected:

- One row per location (unique `location_id`)
- `strategy_key` changes when a new strategy is saved

---

# Location Overview Testing (Phase 7 — Facade)

## 19. Test Overview API

Get the overview of a location:

```
GET /api/locations/{location_id}/overview
```

Expected: `200 OK`

```json
{
  "location": { "id": "<uuid>", "name": "Lab Site A" },
  "device_counts": { "sensor": 1, "actuator": 0 },
  "zones": [
    {
      "id": "<uuid>",
      "name": "Zone 2",
      "moisture_threshold_low": 0.25,
      "moisture_threshold_high": 0.5,
      "devices": [ { "id": "<uuid>", "device_type": "moisture_sensor", "role": "sensor", "display_name": "Soil moisture sensor" } ],
      "latest_readings": [ { "device_id": "<uuid>", "value": 0.33, "unit": "vwc", "recorded_at": "...", "tracking_enabled": true, "sampling_interval_seconds": 300 } ]
    }
  ],
  "strategy_key": "aggressive",
  "last_recommendation": { "action": "irrigate", "reason": "..." }
}
```

Verify:

- Every zone of the location is listed, also a zone without devices
- `device_counts` only counts devices assigned to a zone
- Unassigned devices do not appear in any zone
- A device without a reading is in `devices` but not in `latest_readings`
- Without a saved strategy, `strategy_key` and `last_recommendation` are `null` and the status is still `200`
- `last_recommendation` matches `POST /api/locations/{location_id}/automation/evaluate`
- A missing location returns `404`

---

## 20. Check That the Overview Follows the Database

1. Run `POST /api/sensors/{sensor_id}/read` on a sensor in the zone
2. Get the overview again: the new value is shown
3. Save another strategy with `PUT /api/locations/{location_id}/automation`
4. Get the overview again: `strategy_key` and `last_recommendation` have changed

No new table is used. Check that the schema did not change:

```powershell
docker compose exec backend alembic current
```

Expected: Phase 7 added no table. After Phase 8 the head is `008 (head)`.

---

# Actuator State Testing (Phase 8 — State)

## 21. Test Actuator State API

Get the actuators. If there are none, provision the simulation family first (`POST /api/devices/provision?family=simulation`).

```
GET /api/devices?role=actuator
```

Expected: every actuator has `state` and `allowed_commands`. Sensors have `"state": null` and `"allowed_commands": []`.

```json
{
  "id": "<uuid>",
  "role": "actuator",
  "state": "idle",
  "allowed_commands": ["start", "power_off", "begin_maintenance", "report_fault"]
}
```

Read one actuator's state:

```
GET /api/devices/{device_id}/state
```

Move it (transition.json):

```
POST /api/devices/{device_id}/transition
```

```json
{ "target": "running" }
```

Verify:

- idle → running returns `200` with `"allowed_commands": ["stop", "report_fault"]`
- running → maintenance (bad-transition.json) returns `409` with the reason and the allowed commands
- An unknown target such as `"flying"` returns `400`
- A sensor id or a missing id returns `404`

---

## 22. Check State in the Database

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "\d actuator_states"
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT device_id, state, updated_at FROM actuator_states;"
```

Expected:

- One row per actuator
- After a legal move, `state` and `updated_at` change
- After an illegal move, the row stays the same

Restart the backend and check again:

```powershell
docker compose restart backend
```

The states are still the same.

---

# Frontend Testing

## 23. Test Dashboard

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
 Sensor cards show latest value and source badge  
 "Read now" stores a new reading  
 Interval and tracking can be changed on each sensor card  
 Automation strategy panel shows locations and strategies  
 "Save strategy" saves the selected strategy  
 "Evaluate" shows irrigate or wait with a reason per zone  
 Overview panel shows sensor and actuator counts  
 Overview panel shows strategy and recommendation, or an empty state  
 Overview panel shows one card per zone with devices and readings  
 Refresh loads the overview again  
 Actuator cards show a state badge  
 Hovering the badge shows the allowed commands  
 "Move to" with a legal state updates the badge  
 "Move to" with an illegal state shows the reason  
 Overview zone cards show the new state after Refresh  

---

# Database Verification

## 24. Check Database Records

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

Actuator states:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM actuator_states;"
```

Sensor readings:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM sensor_readings ORDER BY recorded_at DESC LIMIT 10;"
```

Automation rules:

```powershell
docker compose exec postgres psql -U greenhouse -d greenhouse -c "SELECT * FROM automation_rules;"
```

---

# Quality Checks

## 25. Backend Tests

Run:

```powershell
docker compose exec backend pytest tests -q
```

Expected:

```
All tests passed, none skipped
```

---

## 26. Backend Lint

Run:

```powershell
docker compose exec backend ruff check src alembic tests
```

---

## 27. Frontend Check

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

# Phase 8 Final Checklist

## Phases 1–4

☑ Docker services running  
☑ Database migration completed (008 head)  
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

## Phase 5 — Adapter

☑ "Read now" stores a reading and returns 201  
☑ Reading shows value, unit, source and time  
☑ Simulation and vendor adapters give different sources  
☑ Missing device returns 404  
☑ Sampling interval and tracking are saved  
☑ Interval below 5 returns 400  
☑ Sampler adds readings only when tracking is on  
☑ Latest reading stays after refresh  
☑ `sensor_readings` table has foreign key and index  

## Phase 6 — Strategy

☑ Strategy list shows conservative and aggressive  
☑ Strategy is saved per location in `automation_rules`  
☑ Evaluate uses the saved strategy  
☑ Evaluate uses zone thresholds and the latest stored reading  
☑ Same moisture gives wait with conservative and irrigate with aggressive  
☑ Zone without moisture sensor returns wait  
☑ Unknown strategy returns 400  
☑ Missing location returns 404  
☑ Strategy panel can save and evaluate  

## Phase 7 — Facade

☑ Overview endpoint returns one DTO for a location  
☑ Overview handler calls only the facade  
☑ Every zone is listed, also an empty zone  
☑ Only assigned devices are counted and listed  
☑ Latest readings are listed per zone with tracking and interval  
☑ No saved strategy returns 200 with null strategy fields  
☑ Recommendation matches evaluate  
☑ Missing location returns 404  
☑ Overview panel uses one request, Refresh repeats it  
☑ No new table was added in Phase 7  

## Phase 8 — State

☑ `actuator_states` has one row per actuator  
☑ Existing actuators were seeded to idle  
☑ Legal transitions are saved  
☑ Illegal transitions return 409 and are not saved  
☑ Device list shows `state` and `allowed_commands`  
☑ States are the same after a backend restart  
☑ Dashboard shows state badges with allowed commands  

## Quality

☑ Backend tests pass  
☑ Frontend build passes  

# Phase 8 Complete
