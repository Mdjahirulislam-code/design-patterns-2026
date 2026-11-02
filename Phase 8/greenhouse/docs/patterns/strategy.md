# Strategy pattern (Phase 6)

## Problem

The greenhouse must decide when a zone needs water, and there is more than one sensible
policy. One operator wants to save water and only irrigate when the soil is really dry.
Another wants the soil to stay near the top of its band.

If both policies live as `if strategy == "conservative" ... elif ...` in the API handler or
the service, every new policy means editing that code, the branches are hard to test on
their own, and HTTP or database details leak into the decision logic.

## Solution

Each policy is its own class behind one interface. The application picks the class from the
key saved for the location and calls `decide(context)`. It never needs to know which policy
it is running.

```text
PUT  /api/locations/{id}/automation   -> automation_rules (one row per location)

POST /api/locations/{id}/automation/evaluate
        |
        v
AutomationService.evaluate(location_id)
  1. location exists?                       (404 if not)
  2. saved strategy_key                     (default "conservative")
  3. get_strategy(key)                      (unknown key -> 400, before decide)
  4. one LocationAutomationContext per zone:
       zone low / high      <- zones
       latest moisture      <- sensor_readings of moisture sensors with devices.zone_id = zone
  5. strategy.decide(context) -> Recommendation(action, reason, score)
        |
        v
RecommendationDto { location_id, strategy_key, action, reason, evaluated_at, zones[] }
```

## Interface

```python
class AutomationStrategy(ABC):
    key: str
    def decide(self, context: LocationAutomationContext) -> Recommendation: ...
```

| Type | Fields |
|------|--------|
| `LocationAutomationContext` | `location_id`, `zone_id`, `zone_name`, `low`, `high`, `moisture` (or None), `has_moisture_sensor`, `light` (or None) |
| `Recommendation` | `action` (`irrigate` or `wait`), `reason`, `score` (0..1, optional) |

The context is a frozen dataclass with plain values. Strategies never see SQLAlchemy rows,
FastAPI types or Pydantic models, and they never call an actuator. They only recommend.

## Participants

| Role | In this project |
|------|-----------------|
| Strategy | `AutomationStrategy` |
| Concrete strategies | `ConservativeMoistureStrategy`, `AggressiveMoistureStrategy` |
| Context | `AutomationService`, which holds the chosen strategy for one evaluation and feeds it `LocationAutomationContext` objects |
| Client | the API (`PUT .../automation`) and the dashboard strategy panel, which choose the key |

## The two strategies

| Moisture, zone band 0.25–0.45 | conservative | aggressive |
|-------------------------------|--------------|------------|
| 0.20, below low | irrigate | irrigate |
| 0.35, inside the band | **wait** | **irrigate** |
| 0.45 or more | wait | wait |

- **Conservative** irrigates only when moisture is below the zone's low threshold. It saves
  water.
- **Aggressive** irrigates whenever moisture is below the zone's high threshold. It tops up
  early and keeps the soil near the top of the band.

Both strategies wait when the zone has no moisture sensor ("No moisture sensor in this zone")
or the sensor has no stored reading yet. A zone never borrows a reading from another zone or
from an unassigned device.

## Location result

Evaluate builds one context per zone of the location. The location-level `action` is
`irrigate` if any zone needs water, otherwise `wait`. With one zone, the location `reason` is
that zone's reason. With several zones it summarizes, for example
"1 of 2 zones need water: Zone 1". A location without zones returns `wait` with
"Location has no zones".

## Persistence choice

A dedicated `automation_rules` table, not columns on `locations`:

| Column | Notes |
|--------|-------|
| `id` | UUID primary key |
| `location_id` | FK to `locations`, **unique** (one active strategy per location), ON DELETE CASCADE |
| `strategy_key` | `conservative` or `aggressive` |
| `parameters` | JSONB, default `{}`; reserved for strategy settings later |
| `updated_at` | timestamptz |

A separate table keeps automation settings out of the location configuration built by the
Phase 4 Builder. `PUT` upserts the row. When no row exists, evaluate uses the default
`conservative` and `GET .../automation` reports `is_default: true`.

Evaluate always uses the **saved** key. The dropdown in the UI must be saved first.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/automation/context.py` | `LocationAutomationContext`, `Recommendation` |
| Domain | `backend/src/domain/automation/strategy.py` | `AutomationStrategy`, both strategies, `get_strategy`, registry |
| Domain | `backend/src/domain/automation/rule.py` | `StrategyRule` (saved choice) |
| Domain | `backend/src/domain/automation/errors.py` | `UnknownStrategyError`, `LocationNotFoundError` |
| Application | `backend/src/application/automation/service.py` | `AutomationService` |
| Application | `backend/src/application/automation/dto.py` | request and response DTOs |
| Infrastructure | `backend/src/infrastructure/persistence/models.py` | `AutomationRuleRow` |
| Infrastructure | `backend/src/infrastructure/persistence/automation_repository.py` | rule upsert, zone thresholds as plain data |
| Infrastructure | `backend/alembic/versions/007_automation_rules.py` | migration |
| API | `backend/src/interfaces/api/automation.py` | strategy list, get / save, evaluate |
| Frontend | `frontend/src/features/automation/StrategyPanel.tsx` | `#automation` panel |

## API

| Method | Path | Result |
|--------|------|--------|
| GET | `/api/automation/strategies` | available keys with label and description |
| GET | `/api/locations/{location_id}/automation` | saved key, or the default with `is_default: true`; 404 |
| PUT | `/api/locations/{location_id}/automation` | body `{ "strategy_key": "aggressive" }`; 200, 400 unknown key, 404 |
| POST | `/api/locations/{location_id}/automation/evaluate` | `RecommendationDto`; 400, 404 |

```json
{
  "location_id": "<uuid>",
  "strategy_key": "conservative",
  "action": "wait",
  "reason": "Moisture 0.35 is within 0.25–0.45",
  "evaluated_at": "2026-10-13T09:00:00Z",
  "zones": [
    {
      "zone_id": "<uuid>",
      "zone_name": "Zone 1",
      "action": "wait",
      "reason": "Moisture 0.35 is within 0.25–0.45",
      "score": 0.0,
      "moisture": 0.35,
      "light": null,
      "moisture_threshold_low": 0.25,
      "moisture_threshold_high": 0.45
    }
  ]
}
```

## Exercise: add a third strategy

Example: a **balanced** strategy that irrigates below the middle of the band.

1. Add a class in `domain/automation/strategy.py`:

   ```python
   class BalancedMoistureStrategy(AutomationStrategy):
       key = "balanced"
       label = "Balanced"
       description = "Irrigate when moisture is below the middle of the zone band."

       def decide(self, context):
           missing = _missing_reading(context)
           if missing is not None:
               return missing
           middle = (context.low + context.high) / 2
           if context.moisture < middle:
               return Recommendation("irrigate", f"Moisture {context.moisture:.2f} is below the middle {middle:.2f}")
           return Recommendation("wait", f"Moisture {context.moisture:.2f} is at or above the middle {middle:.2f}")
   ```

2. Register it: add `BalancedMoistureStrategy.key: BalancedMoistureStrategy` to `_STRATEGIES`.
3. Add unit tests with a plain context.

The service, the API, the table and the UI do not change. The dropdown reads its options from
`GET /api/automation/strategies`, so the new strategy shows up by itself.
