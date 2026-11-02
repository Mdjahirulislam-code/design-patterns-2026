# Facade pattern (Phase 7)

## Problem

The dashboard overview needs data from five places at once:

- the location and its zones (Phase 4)
- the devices assigned to those zones (Phases 2–4)
- the newest stored reading of each of those devices (Phase 5)
- the strategy saved for the location (Phase 6)
- the current recommendation of that strategy (Phase 6)

Without a facade every caller has to repeat that multi-step work. The router would import five
repositories, or the React page would call four endpoints and merge the answers itself. Each
copy can get the rules slightly wrong (counting unassigned devices, dropping empty zones), and
a change to the query shape has to be made in every copy.

## Solution

`LocationOverviewFacade.get_overview(location_id)` is the one entry point. It asks the existing
subsystems for their part and assembles a single read model, `LocationOverviewDto`. The
overview route calls only the facade, and the Overview panel makes only one request.

```text
GET /api/locations/{location_id}/overview
        |
        v
LocationOverviewFacade.get_overview(location_id)
  1. LocationRepository.get_with_zones          location + every zone        (404 if missing)
  2. DeviceRepository.list_assigned_to_location  devices with this location_id AND a zone_id
  3. ReadingRepository.latest_for_devices        newest reading of those ids, ONE query
  4. AutomationRuleRepository.get                saved strategy key, or none
  5. AutomationService.evaluate                  only when a key is saved
        |
        v
LocationOverviewDto
```

## What the facade hides

| Subsystem | Hidden behind the facade |
|-----------|--------------------------|
| Locations and zones | `LocationRepository` |
| Assigned devices | `DeviceRepository` |
| Latest readings | `ReadingRepository` |
| Saved strategy | `AutomationRuleRepository` |
| Recommendation | `AutomationService.evaluate`, which runs the saved Strategy |

The facade only coordinates. It does **not**:

- decide irrigation (Strategy `decide` stays inside `AutomationService.evaluate`)
- translate sensor payloads (Adapters from Phase 5)
- write anything or own any table

## Rules of the read model

- **Scope:** everything is scoped by `location_id`. There is no greenhouse id.
- **Assigned device:** a device counts only when it has this `location_id` and a non-null
  `zone_id`. Unassigned devices are not counted and do not appear in any zone.
- **Device counts:** `device_counts` splits the assigned devices by `role` into `sensor` and
  `actuator`.
- **Every zone:** every zone of the location is listed, including a zone with no devices. Its
  `devices` and `latest_readings` are then empty lists.
- **Latest readings per zone:** `latest_readings` sits inside each zone, one row per device
  that has a reading. A device without a reading stays in `devices` and is left out of
  `latest_readings`.
- **Any source:** a reading may come from a manual read, the sampler or MQTT ingest. The newest
  `recorded_at` wins and `source` is not filtered.
- **Sampling settings:** `tracking_enabled` and `sampling_interval_seconds` on a reading
  summary are copied from the device. They are not columns of `sensor_readings`.

## Phase 8 addition

The zone devices now also carry `state` and `allowed_commands` for actuators (null and empty
for sensors). The facade loads the states of all assigned actuators in one more query
(`ActuatorStateRepository.get_many`). The rules for those states stay in the State pattern
(`domain/actuators/state.py`).

## Recommendation: computed, not cached

`last_recommendation` is computed on every GET by calling the existing
`AutomationService.evaluate`, which uses the saved key, zone thresholds and stored readings.
It is not stored in a new table, so the next overview always shows the current state of the
database. When no key is saved, evaluate is not called and the response is still 200 with
`strategy_key: null` and `last_recommendation: null`.

## Query shape and N+1

An N+1 problem would be one query for the devices and then one more query per device for its
latest reading. With many devices that is many round trips.

The facade avoids it:

| Step | Queries |
|------|---------|
| Location + zones | 2 (location row, its zones) |
| Assigned devices | 1, for the whole location |
| Newest readings | 1, `SELECT DISTINCT ON (device_id) … WHERE device_id IN (…) ORDER BY device_id, recorded_at DESC`, using the Phase 5 index `(device_id, recorded_at DESC)` |
| Saved strategy | 1 |
| Evaluate | only when a key is saved |

`evaluate` still loads moisture once per zone inside the automation service. That lookup is
left there on purpose, because the facade must not re-implement `decide` just to save a few
queries. Both live in the repository and application layers; there is no SQL in the router.

## Errors

The route maps only `LocationNotFoundError` to 404. "No strategy saved" is not an error
(200 with nulls). Other failures, such as a database outage, are not hidden behind a generic
"overview failed" message; they surface as their own server errors so they can be told apart.

## Database

No new table and no migration. The existing tables are enough: `locations`, `zones`,
`devices`, `sensor_readings` and `automation_rules`. The optional `location_overview_v1` view
was not added.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Application | `backend/src/application/overview/dto.py` | `LocationOverviewDto` and nested DTOs |
| Application | `backend/src/application/overview/facade.py` | `LocationOverviewFacade` |
| Domain | `backend/src/domain/locations/entity.py` | `LocationSummary`, `ZoneThresholds` (plain data) |
| Domain | `backend/src/domain/locations/errors.py` | `LocationNotFoundError` |
| Infrastructure | `backend/src/infrastructure/persistence/location_repository.py` | `get_with_zones` |
| Infrastructure | `backend/src/infrastructure/persistence/device_repository.py` | `list_assigned_to_location` |
| Infrastructure | `backend/src/infrastructure/persistence/reading_repository.py` | `latest_for_devices` |
| API | `backend/src/interfaces/api/overview.py` | the route; imports only the facade |
| API | `backend/src/interfaces/api/dependencies.py` | `get_overview_facade` wires the repositories |
| Frontend | `frontend/src/components/overview/OverviewPanel.tsx` | `#overview` cards |

## API

| Method | Path | Result |
|--------|------|--------|
| GET | `/api/locations/{location_id}/overview` | 200 + `LocationOverviewDto`; 404 missing location |

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
      "devices": [
        {
          "id": "<uuid>",
          "device_type": "moisture_sensor",
          "role": "sensor",
          "display_name": "Soil moisture sensor"
        }
      ],
      "latest_readings": [
        {
          "device_id": "<uuid>",
          "value": 0.33,
          "unit": "vwc",
          "recorded_at": "2026-10-27T09:00:00Z",
          "tracking_enabled": true,
          "sampling_interval_seconds": 300
        }
      ]
    }
  ],
  "strategy_key": "aggressive",
  "last_recommendation": {
    "action": "irrigate",
    "reason": "Moisture 0.33 is below the high threshold 0.50, topping up early"
  }
}
```

## Frontend

The Overview panel loads the location list for its dropdown. Selecting a location makes **one**
`GET .../overview` request, and Refresh repeats that same request. The panel does not call the
device, reading or automation endpoints. A new reading or a newly saved strategy shows up on
the next overview request because the facade reads the database every time.
