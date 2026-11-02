# State pattern (Phase 8)

## Problem

An actuator (water pump, grow light) goes through a lifecycle: it can be off, ready, running,
broken or being serviced, and what it may do depends on where it is in that lifecycle.

Modelled as booleans (`is_running`, `is_fault`, `is_maintenance`) the rules end up as `if`
checks spread over routers, services and the UI. Impossible combinations appear (running
**and** in maintenance), one place forgets a check, and adding a state means hunting through
every `if`.

## Solution

Each lifecycle state is its own object. The state object knows which commands it accepts and
which state each command leads to. A context object holds the current state and delegates to
it. A move that the current state does not allow raises a domain error **before** anything is
saved.

```text
POST /api/devices/{id}/transition { "target": "running" }
        |
        v
ActuatorStateService.transition(device_id, target)
  1. device exists and is an actuator          (404 if not)
  2. load stored state from actuator_states    (no row -> initial "idle")
  3. ActuatorContext(device_id, state).transition_to(target)
        -> current state object finds the command that leads there
        -> none?  IllegalTransitionError (409), nothing saved
  4. save the new state, return state + allowed_commands
```

## Participants

| Role | In this project |
|------|-----------------|
| Context | `ActuatorContext` (`domain/actuators/context.py`) |
| State interface | `ActuatorState` with `handle(command)`, `command_to(target)`, `allowed_commands()` |
| Concrete states | `OffState`, `IdleState`, `RunningState`, `ErrorState`, `MaintenanceState` (`domain/actuators/state.py`) |
| Client | `ActuatorStateService`, and later the Phase 10 commands |

The router only maps errors to HTTP codes. React only shows `state` and `allowed_commands`.
Neither contains a transition rule.

## States

| State | Meaning |
|-------|---------|
| `off` | Powered off. Must be powered on before it can run. |
| `idle` | Powered and ready, not running. The initial state. |
| `running` | Running (pump watering or light on). |
| `error` | A fault was reported. |
| `maintenance` | Being serviced. Cannot run. |

## Legal transitions

| From | Command | To |
|------|---------|----|
| off | `power_on` | idle |
| idle | `start` | running |
| idle | `power_off` | off |
| idle | `begin_maintenance` | maintenance |
| idle | `report_fault` | error |
| running | `stop` | idle |
| running | `report_fault` | error |
| error | `reset` | idle |
| error | `begin_maintenance` | maintenance |
| error | `power_off` | off |
| maintenance | `end_maintenance` | idle |
| maintenance | `report_fault` | error |

Everything else is illegal. Important refinements of the "anything → error" idea:

- **`running → maintenance` is illegal.** The actuator must be stopped first.
- **`off → running` is illegal.** It must be powered on first.
- **`off → error` is illegal.** A device without power cannot report a fault.
- **`maintenance → off` is illegal.** Maintenance must be ended first.
- **Same state is not a move.** `idle → idle` is rejected.

`allowed_commands` is derived from the current state object, for example
`idle → [start, power_off, begin_maintenance, report_fault]` and `running → [stop, report_fault]`.
These names are the commands Phase 10 will implement. They are generic, so the same `start`
and `stop` work for a pump and for a grow light.

## Persistence

Table `actuator_states`, one row per actuator:

| Column | Notes |
|--------|-------|
| `device_id` | primary key, FK to `devices`, ON DELETE CASCADE |
| `state` | `off`, `idle`, `running`, `error` or `maintenance` |
| `updated_at` | timestamptz, set on every saved transition |

- **Seeding:** migration `008_actuator_states` seeds every existing actuator to `idle` in its
  `upgrade()`.
- **New actuators:** actuators created later by provisioning get an `idle` row in the same
  transaction (`DeviceRepository.save_devices`).
- **Missing rows:** if a row is still missing, the actuator is read as `idle` and the row is
  written on its first legal transition.
- **Restarts:** the state lives only in the database, never in FastAPI memory, so it
  survives a backend restart.
- **Illegal moves:** the domain raises before `save()` is called, so the row and its
  `updated_at` stay unchanged.

## API

| Method | Path | Result |
|--------|------|--------|
| GET | `/api/devices` | every device; actuators have `state` and `allowed_commands`, sensors have `null` and `[]` |
| GET | `/api/locations/{location_id}/zones/{zone_id}/devices` | same fields for the devices in one zone |
| GET | `/api/locations/{location_id}/overview` | zone devices include `state` and `allowed_commands` |
| GET | `/api/devices/{device_id}/state` | `ActuatorStateDto`; 404 if not an actuator |
| POST | `/api/devices/{device_id}/transition` | body `{ "target": "running" }`; 200, 400 unknown target, 404 not an actuator, 409 illegal |

The transition endpoint is a demo. Phase 10 will run named commands through the Command
pattern and call `ActuatorContext.apply(command)`.

```json
{
  "device_id": "<uuid>",
  "state": "running",
  "allowed_commands": ["stop", "report_fault"],
  "updated_at": "2026-11-02T09:00:00Z"
}
```

An illegal move:

```json
{ "detail": "Cannot go to maintenance while the actuator is running. Allowed commands: stop, report_fault." }
```

States for a whole device list (or an overview) are loaded in one query, not one per device.

## Frontend

- Actuator cards in the Devices section show a colored state badge: idle slate, running
  emerald, error red, maintenance amber, off gray. Its tooltip lists the commands allowed now.
- A small "Move to" control calls the demo transition endpoint. The list holds only state
  names. If the move is illegal, the backend's reason is shown under the card.
- The Overview zone cards show the same badge after Refresh.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/actuators/state.py` | state objects, transition table, `get_state` |
| Domain | `backend/src/domain/actuators/context.py` | `ActuatorContext` |
| Domain | `backend/src/domain/actuators/errors.py` | `IllegalTransitionError`, `UnknownActuatorStateError`, `ActuatorNotFoundError` |
| Domain | `backend/src/domain/actuators/record.py` | `ActuatorStateRecord` |
| Application | `backend/src/application/actuators/service.py` | `ActuatorStateService` |
| Application | `backend/src/application/devices/queries.py` | device DTOs with state |
| Application | `backend/src/application/devices/dto.py` | `state`, `allowed_commands` |
| Infrastructure | `backend/src/infrastructure/persistence/models.py` | `ActuatorStateRow` |
| Infrastructure | `backend/src/infrastructure/persistence/actuator_state_repository.py` | load, bulk load, save |
| Infrastructure | `backend/alembic/versions/008_actuator_states.py` | table + seed |
| API | `backend/src/interfaces/api/devices.py` | state and transition routes |
| Frontend | `frontend/src/components/devices/ActuatorStateBadge.tsx`, `ActuatorStateControl.tsx` | badge, demo control |

## Adding a state

1. Add a class in `state.py` with its `name`, `description` and `transitions`.
2. Add transitions into it from the states that may reach it.
3. Register it in `_STATES` and add tests for its legal and illegal edges.

The service, the table, the API and the UI need no change.
