# Command pattern (Phase 10)

## Problem

Starting a pump is more than one function call. The request must be checked against the
actuator state, sent through the policy decorators, change the stored state, and leave a
record of who asked for what and how it ended.

If the router calls the actuator port directly, those steps live in an HTTP handler. Other
callers skip them, there is no history, and a request cannot be stored, listed or repeated
because it only exists as a function call.

## Solution

Each operator request is an **object**: it carries its type, the device and the payload, and
knows how to execute itself against a port. Because it is an object, it can be created from
a type string, handed to an invoker, checked, and written to a log.

```text
POST /api/commands { command_type, device_id, payload }
        |
        v
CommandService.execute
  1. device is an actuator?                  no  -> 404, no row
  2. command_for(type) -> command object     unknown type -> 400, no row
  3. guard: type in allowed_commands() of the saved state?
        no  -> command_log "rejected", 409, stop (no apply, no state write)
  4. CommandInvoker.run(command, port)       port = Phase 9 stack
        raises (Max run time exceeded, adapter error)
            -> command_log "failed", 200, state unchanged
  5. target_state differs? ActuatorContext.transition + save
  6. command_log "success", 200
```

## Participants

| Role | In this project |
|------|-----------------|
| Command | `Command` with `execute(port)`, `command_type`, `target_state` |
| Concrete commands | `StartPumpCommand`, `StopPumpCommand`, `SetLightLevelCommand` |
| Invoker | `CommandInvoker.run(command, port)` |
| Receiver | the decorated `ActuatorPort` (logging → max run time → simulation adapter) |
| Client | `CommandService`, which creates the command with `command_for` and gives it to the invoker |

The registry in `domain/commands/invoker.py` maps the type string to a class. Neither the
invoker nor the service contains `if command_type == "start_pump"`.

## Commands

| `command_type` | Class | Target state | Payload |
|----------------|-------|--------------|---------|
| `start_pump` | `StartPumpCommand` | `running` | free |
| `stop_pump` | `StopPumpCommand` | `idle` | free |
| `set_light_level` | `SetLightLevelCommand` | `running` | `{ "level": 1 }` by default; level must be a number of 0 or more |

`set_light_level` on an idle actuator turns it on (idle → running). On an actuator that is
already running it only sends the new level and does not transition.

The guard looks only at the saved state (Phase 8), not at the device type:

| State | Allowed operator commands |
|-------|---------------------------|
| idle | `start_pump`, `set_light_level` |
| running | `stop_pump`, `set_light_level` |
| off, error, maintenance | none |

## The three outcomes

| Status | Meaning | Example | HTTP | State | Execution log (Phase 9) |
|--------|---------|---------|------|-------|-------------------------|
| `success` | accepted and carried out | `start_pump` on an idle pump | 200 | changes if the target differs | row with `success=true` |
| `failed` | accepted, but a policy or the adapter stopped it | `stop_pump` on a pump that has been running 30 minutes: `Max run time exceeded` | 200 | unchanged | row with `success=false` |
| `rejected` | not legal in this state, never sent | `stop_pump` on an idle pump | 409 | unchanged | no row, the port is not reached |

Unknown `command_type` and an unusable payload answer 400 and write no row. A missing
device or a sensor answers 404 and writes no row.

## Two logs

| Table | Records | Written by |
|-------|---------|------------|
| `command_log` | what the operator asked for and how it ended, including rejected requests | `CommandService` |
| `actuator_execution_log` | each attempt that reached the actuator port and which policies were applied | the logging decorator |

A rejected command appears only in `command_log`. A successful or failed command appears in
both.

## Why not call the port from the router

- The state guard, the decorators, the state update and the log would have to be repeated
  by every caller, and one of them would be forgotten.
- A function call leaves nothing behind. A command object can be logged, listed and, later,
  queued or published as an event (Phase 11).
- A new command is one class and one registry entry. The router, the service and the invoker
  do not change.

## Persistence

Table `command_log` (migration `010_command_log`), append only:

| Column | Notes |
|--------|-------|
| `id` | UUID primary key |
| `command_type` | varchar |
| `device_id` | FK to `devices`, ON DELETE CASCADE |
| `payload` | JSONB |
| `status` | `success`, `failed` or `rejected` |
| `error_message` | text, null on success |
| `created_at` | timestamptz, indexed newest first |

## API

| Method | Path | Result |
|--------|------|--------|
| POST | `/api/commands` | body `{ command_type, device_id, payload? }`; 200 success/failed, 409 rejected, 400, 404 |
| GET | `/api/commands?limit=50` | history, newest first (`limit` 1–200) |

```json
{
  "id": "<uuid>",
  "command_type": "stop_pump",
  "device_id": "<uuid>",
  "payload": {},
  "status": "rejected",
  "error_message": "Cannot stop_pump while the actuator is idle. Allowed commands: start_pump, set_light_level, power_off, begin_maintenance, report_fault.",
  "created_at": "2026-11-15T12:00:00Z"
}
```

## Frontend

The **Controls** block (`#controls`) shows every actuator with its state badge and three
buttons: Start pump, Stop pump and Set light level (with a level field, default 1). A button
is disabled when its command is not in the actuator's `allowed_commands`. After every click
the actuators and the history are loaded again, so the buttons follow the new state. The
**Command history** table shows time, device, command, payload, status and message.

The backend still checks every command. The disabled buttons are only a convenience.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/commands/base.py` | `Command`, `CommandResult`, statuses, errors |
| Domain | `backend/src/domain/commands/pump.py` | `StartPumpCommand`, `StopPumpCommand` |
| Domain | `backend/src/domain/commands/light.py` | `SetLightLevelCommand` |
| Domain | `backend/src/domain/commands/invoker.py` | registry, `command_for`, `CommandInvoker` |
| Domain | `backend/src/domain/actuators/state.py` | `allowed_commands` per state (the guard) |
| Application | `backend/src/application/commands/service.py` | `CommandService` |
| Application | `backend/src/application/commands/dto.py` | `CommandRequest`, `CommandLogDto` |
| Infrastructure | `backend/src/infrastructure/persistence/models.py` | `CommandLogRow` |
| Infrastructure | `backend/src/infrastructure/persistence/command_log_repository.py` | insert, recent |
| Infrastructure | `backend/alembic/versions/010_command_log.py` | migration |
| API | `backend/src/interfaces/api/commands.py` | POST and GET |
| Frontend | `frontend/src/components/commands/CommandPanel.tsx` | controls + history |

## Adding a command

1. Add a class with `command_type` and `target_state` (and `prepare_payload` if needed).
2. Add it to the registry in `invoker.py`.
3. Add its name to the states that allow it in `domain/actuators/state.py`.

The service, the API, the table and the history need no change.
