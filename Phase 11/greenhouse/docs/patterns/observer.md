# Observer pattern (Phase 11)

## Problem

Several parts of the system produce things that other parts care about:

- a new reading can be below the zone's low moisture threshold,
- a command can fail (for example `Max run time exceeded`),
- an actuator can move to `error`.

Somebody has to turn these into alerts that the operator can see. If `ReadingIngest`,
`CommandService` and `ActuatorStateService` each called an alert service directly, every
producer would need to know about alerts, and every new reaction (an email, a WebSocket push,
a statistic) would change all producers again.

## Solution

The producers only **publish an event** on an event bus. Code that cares **subscribes** to
the event type. The publisher does not know who listens, how many listeners there are, or
what they do.

```text
ReadingIngest ──── ReadingCreated ─────┐
CommandService ─── CommandFailed ──────┤
CommandService ─┐                      ├──► EventBus ──► subscribers
ActuatorState ──┴─ ActuatorStateChanged┘

MoistureThresholdSubscriber   ReadingCreated  → (below zone low) → ThresholdCrossed
AlertPersistenceSubscriber    ThresholdCrossed / CommandFailed / ActuatorStateChanged(error)
                              → row in alerts → AlertCreated
```

`AlertCreated` has no subscriber yet. Phase 12 subscribes the dashboard WebSocket to it.

## Participants

| Role | In this project |
|------|-----------------|
| Subject (event bus) | `EventBus` in `backend/src/domain/events/bus.py`: `subscribe(event_type, handler)`, `publish(event)` |
| Publisher interface | `EventPublisher` protocol (only `publish`) |
| Events | `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged`, `AlertCreated` |
| Publishers | `ReadingIngest`, `CommandService`, `ActuatorStateService` |
| Observers (subscribers) | `MoistureThresholdSubscriber`, `AlertPersistenceSubscriber` |
| Wiring | `build_event_bus(session)` in `backend/src/infrastructure/events.py` |

The publishers depend only on `EventPublisher`. None of them imports anything from the alerts
code. `test_publishers.py` checks this with an AST scan of their imports.

## Events

All events are small frozen dataclasses with a fixed `event_type` string.

| Event | `event_type` | Published by | When |
|-------|--------------|--------------|------|
| `ReadingCreated` | `reading.created` | `ReadingIngest` | after the reading row is stored, only for a sensor with tracking enabled |
| `ThresholdCrossed` | `threshold.crossed` | `MoistureThresholdSubscriber` | moisture (`vwc`) strictly below the zone's low threshold |
| `CommandFailed` | `command.failed` | `CommandService` | after a `failed` row is written to `command_log` |
| `ActuatorStateChanged` | `state.changed` | `CommandService`, `ActuatorStateService` | after a new state is saved |
| `AlertCreated` | `alert.created` | `AlertPersistenceSubscriber` | after an alert row is stored |

A `rejected` command publishes nothing, because nothing happened on the actuator.

## The bus

- **In process and synchronous.** `publish` calls the handlers one after another in the order
  they subscribed, inside the same request and the same database session.
- **Handler errors are isolated.** If one handler raises, the error is logged and stored in
  `bus.errors`, and the next handler still runs. The publisher never sees the error, so a
  broken subscriber cannot fail a reading or a command.
- **One bus per request.** `build_event_bus(session)` creates a new bus with subscribers that
  use the request's session. Nothing is global, and the tests build their own bus.
- Subscribers can publish again. `MoistureThresholdSubscriber` publishes `ThresholdCrossed`
  on the same bus, and `AlertPersistenceSubscriber` publishes `AlertCreated`.

## The subscribers

### MoistureThresholdSubscriber

Listens to `reading.created`. It publishes `ThresholdCrossed` only when:

1. the unit is `vwc` (moisture),
2. the sensor is assigned to a zone,
3. the zone exists and the value is **strictly below** `moisture_threshold_low`.

A value equal to the low threshold is not an alert.

### AlertPersistenceSubscriber

Writes one row to `alerts` and then publishes `AlertCreated`.

| Event | Severity | Message |
|-------|----------|---------|
| `threshold.crossed` | `warning` | `Moisture below zone low` |
| `command.failed` | `warning` | the command's error text, for example `Max run time exceeded` |
| `state.changed` to `error` | `critical` | `Actuator entered error` |
| `state.changed` to any other state | – | nothing stored |

The location and zone come from the event. For an actuator that is not assigned to a zone,
both are `null`.

## Persistence

Table `alerts` (migration `011_alerts`):

| Column | Notes |
|--------|-------|
| `id` | UUID primary key |
| `location_id` | FK to `locations`, nullable, ON DELETE SET NULL |
| `zone_id` | FK to `zones`, nullable, ON DELETE SET NULL |
| `device_id` | FK to `devices`, nullable, ON DELETE SET NULL |
| `severity` | `info`, `warning` or `critical` |
| `message` | text |
| `event_type` | the event that caused the alert |
| `status` | `active` (default) or `resolved` |
| `created_at` | timestamptz |
| `acknowledged_at` | timestamptz, null for now |

SET NULL keeps the alert history when a device, zone or location is deleted.

Indexes: `(status, created_at DESC)`, `(zone_id, created_at DESC)`,
`(location_id, created_at DESC)`.

## API

| Method | Path | Result |
|--------|------|--------|
| GET | `/api/alerts` | alerts, newest first |

Query parameters: `status` (`active` by default, `resolved` or `all`), `location_id`,
`zone_id`, `since` (ISO time), `limit` (1–200, default 50). An unknown status gives 400.

```json
{
  "id": "<uuid>",
  "location_id": "<uuid>",
  "zone_id": "<uuid>",
  "device_id": "<uuid>",
  "severity": "warning",
  "message": "Moisture below zone low",
  "event_type": "threshold.crossed",
  "status": "active",
  "created_at": "2026-11-23T12:00:00Z"
}
```

## Frontend

The **Events** block (`#events`) on the dashboard:

- loads `GET /api/alerts` right away and then every 5 seconds,
- has a location filter and a zone filter (zones come from the location config),
- shows a severity badge, the message, the event type, the zone and the time,
- has an empty state.

`frontend/src/services/realtime.ts` is a stub with `subscribeRealtime(handler)`. In Phase 12
its body opens the dashboard WebSocket, and the backend subscribes that socket to the same
`EventBus`, so no second pub/sub system is needed.

## Demo

1. Set a zone's low threshold above the simulation range (simulation moisture is 0.2–0.6):
   `PATCH /api/locations/{location_id}/zones/{zone_id}` with `alert-zone.json`
   (low 0.7, high 0.9).
2. Make sure a simulation moisture sensor is assigned to that zone and has tracking enabled.
3. Press **Read now** on that sensor (or wait for the sampler). Within 5 seconds the Events
   feed shows `warning · Moisture below zone low · threshold.crossed`.
4. Send `stop_pump` to an actuator that has been running for 30 minutes. The command is
   `failed`, and the feed shows `warning · Max run time exceeded · command.failed`.
5. Move an actuator to `error`. The feed shows `critical · Actuator entered error`.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/events/events.py` | event dataclasses |
| Domain | `backend/src/domain/events/bus.py` | `EventBus`, `EventPublisher`, `NullEventBus` |
| Domain | `backend/src/domain/alerts.py` | severities, statuses, `Alert` |
| Application | `backend/src/application/alerts/subscribers.py` | the two subscribers, `subscribe_alert_handlers` |
| Application | `backend/src/application/alerts/service.py` | `AlertQueryService` |
| Application | `backend/src/application/readings/service.py` | publishes `ReadingCreated` |
| Application | `backend/src/application/commands/service.py` | publishes `CommandFailed`, `ActuatorStateChanged` |
| Application | `backend/src/application/actuators/service.py` | publishes `ActuatorStateChanged` |
| Infrastructure | `backend/src/infrastructure/events.py` | `build_event_bus(session)` |
| Infrastructure | `backend/src/infrastructure/persistence/alert_repository.py` | insert and list |
| Infrastructure | `backend/alembic/versions/011_alerts.py` | migration |
| API | `backend/src/interfaces/api/alerts.py` | `GET /api/alerts` |
| Frontend | `frontend/src/components/alerts/EventFeed.tsx` | Events block |
| Frontend | `frontend/src/services/realtime.ts` | Phase 12 stub |

## Adding another subscriber

Example: count failed commands per device.

1. Write a class with a method that takes `CommandFailed`.
2. Subscribe it in `build_event_bus` (or in `subscribe_alert_handlers`).
3. Add a unit test with a plain `EventBus`.

`CommandService` does not change.
