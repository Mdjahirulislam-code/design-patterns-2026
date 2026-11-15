# Decorator pattern (Phase 9)

## Problem

A command to an actuator needs more than "send it to the device". Every attempt must be
recorded, and a pump that has been running too long must be refused. More policies may come
later (retry, cooldown, rate limit).

If these rules are written into the adapter, the adapter does three jobs and every new rule
changes it. If each combination is its own subclass (`LoggingActuator`,
`MaxRunTimeActuator`, `LoggingMaxRunTimeActuator`, …), the number of classes grows with every
new policy. If the rules are `if` checks in the router, other callers skip them.

## Solution

Each policy is a small wrapper class with the **same interface** as the thing it wraps. The
wrappers are stacked around the real adapter. The caller holds one `ActuatorPort` and does
not know how many wrappers are inside.

```text
caller
  └─ ActuatorPort.apply(device_id, command, payload)
       │
       ▼
LoggingActuatorDecorator          writes one row to actuator_execution_log for every call
  └─ MaxRunTimeActuatorDecorator  blocks when the actuator has been running for 30 minutes
       └─ SimulationActuatorAdapter   the real work (simulation: remembers the command)
```

## Participants

| Role | In this project |
|------|-----------------|
| Component | `ActuatorPort` with `apply(device_id, command, payload) -> None` |
| Concrete component | `SimulationActuatorAdapter` (Phase 5) |
| Decorator | `ActuatorPortDecorator`: holds the wrapped port and forwards `apply` to it |
| Concrete decorators | `LoggingActuatorDecorator`, `MaxRunTimeActuatorDecorator` |
| Client | `ActuatorExecutionService` (and the Phase 10 commands later) |

Every decorator keeps the method name, the arguments and the return type of
`ActuatorPort.apply`. That is what makes them stackable in any number.

## The two decorators

### Max run time

- Reads the lifecycle that Phase 8 already stores: `actuator_states.state` and `updated_at`.
- Blocks when the state is `running` **and** `updated_at` is at least 30 minutes before the
  clock. Exactly 30 minutes is already blocked.
- When it blocks, it raises `MaxRunTimeExceededError` and does **not** call the wrapped port
  (short-circuit).
- Any other state, or an actuator without a state row, is passed through.
- It does not keep its own timer or a second lifecycle. The state table is the only source.

### Logging

- Calls the wrapped port and then writes exactly one row for the call.
- It is the outermost wrapper, so it also sees a call that an inner policy blocked.
- After writing the row for a blocked or failed call, it raises the same error again.

| What happened | `success` | `policy_applied` | `message` |
|---------------|-----------|------------------|-----------|
| Completed | `true` | `["logging"]` | `null` |
| Blocked by max run time | `false` | `["maxRunTime", "logging"]` | `Max run time exceeded` |
| The adapter failed | `false` | `["logging"]` | the error text |

The command string is **not validated** in this phase. An unknown command on an idle actuator
still succeeds. Applying a command also does not change the actuator state. Phase 10 (Command)
will check `allowed_commands` and move the state.

## Order matters

The chain is built in one place, `build_actuator_port` in
`backend/src/infrastructure/adapters/actuators/factory.py`:

```python
core = SimulationActuatorAdapter()
guarded = MaxRunTimeActuatorDecorator(core, states)
return LoggingActuatorDecorator(guarded, executions)
```

- **Logging outside max run time (used here):** a blocked attempt passes through logging
  first, so it is recorded with `success=false`.
- **Max run time outside logging (wrong):** the block happens before logging is reached, so a
  blocked attempt leaves no row at all. `test_wrong_order_would_lose_the_blocked_attempt`
  shows this.

Logging runs once per call from the client, not once per inner attempt, because nothing sits
outside it.

## Where the chain is wired

`interfaces/api/dependencies.py` calls `build_actuator_port(...)` and gives the result to
`ActuatorExecutionService` as a plain `ActuatorPort`. The router only calls the service. It
contains no policy check, so every caller of the port gets the same policies.

## Compared with inheritance

With inheritance every combination of policies needs its own subclass, and the combination
is fixed when the class is written. With decorators:

- a new policy is one new class,
- adding or removing it is one line in the factory,
- the order can be changed in the factory without touching any policy class,
- each policy can be tested alone around a fake port.

## Persistence

Table `actuator_execution_log` (migration `009_actuator_execution_log`), append only:

| Column | Notes |
|--------|-------|
| `id` | UUID primary key |
| `device_id` | FK to `devices`, ON DELETE CASCADE |
| `success` | boolean |
| `policy_applied` | JSONB list of policy names |
| `message` | text, null for a successful row |
| `created_at` | timestamptz |

Indexes: `created_at DESC` for the recent list and `(device_id, created_at DESC)` for the
newest row of one device.

## API

| Method | Path | Result |
|--------|------|--------|
| GET | `/api/actuators/executions?limit=20` | rows of the log, newest first (`limit` 1–200) |
| POST | `/api/actuators/{device_id}/apply` | demo apply; body `{ "command": "start", "payload": {} }` |

Apply answers:

| Case | Status | Log row |
|------|--------|---------|
| Completed | 200 + the written row | `success=true` |
| Blocked by max run time | 409 `Max run time exceeded` | `success=false`, `["maxRunTime","logging"]` |
| Adapter rejected the command (empty command) | 400 | `success=false`, `["logging"]` |
| Device missing or not an actuator | 404 | no row, the port is not called |

```json
{
  "id": "<uuid>",
  "device_id": "<uuid>",
  "success": false,
  "policy_applied": ["maxRunTime", "logging"],
  "message": "Max run time exceeded",
  "created_at": "2026-11-10T12:00:00Z"
}
```

The apply route is a demo until Phase 10, which will execute commands through this same
decorated port.

## Demo: a blocked attempt

1. Move an actuator to `running` (Devices section, or `POST /api/devices/{id}/transition`).
2. Move its `updated_at` 31 minutes back:

   ```powershell
   docker compose exec postgres psql -U greenhouse -d greenhouse -c "UPDATE actuator_states SET updated_at = now() - interval '31 minutes' WHERE state = 'running';"
   ```

3. Apply any command to that actuator. The answer is 409.
4. Refresh the execution log. The newest row is `failed` with the policies `maxRunTime` and
   `logging` and the message `Max run time exceeded`.

## Frontend

The **Actuator execution log** block on the dashboard shows the newest 20 rows: time, device,
result badge, policies and message. It has an empty state, a Refresh button and a small demo
control (actuator, command, Apply). The table is always loaded from the API, also after a
blocked attempt. No policy is checked in React.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/actuators/ports.py` | `ActuatorPort`, `ActuatorPortDecorator` |
| Domain | `backend/src/domain/actuators/policies.py` | policy names, 30 minute limit |
| Domain | `backend/src/domain/actuators/errors.py` | `ActuatorPolicyError`, `MaxRunTimeExceededError` |
| Domain | `backend/src/domain/actuators/execution.py` | `ActuatorExecution` (one log row as plain data) |
| Application | `backend/src/application/actuators/executions.py` | `ActuatorExecutionService` |
| Application | `backend/src/application/actuators/dto.py` | `ExecutionDto`, `ApplyCommandRequest` |
| Infrastructure | `backend/src/infrastructure/adapters/actuators/simulation.py` | innermost adapter |
| Infrastructure | `backend/src/infrastructure/adapters/actuators/logging_decorator.py` | logging |
| Infrastructure | `backend/src/infrastructure/adapters/actuators/max_runtime_decorator.py` | max run time |
| Infrastructure | `backend/src/infrastructure/adapters/actuators/factory.py` | the chain and its order |
| Infrastructure | `backend/src/infrastructure/persistence/models.py` | `ActuatorExecutionLogRow` |
| Infrastructure | `backend/src/infrastructure/persistence/execution_log_repository.py` | insert, recent, latest per device |
| Infrastructure | `backend/alembic/versions/009_actuator_execution_log.py` | migration |
| API | `backend/src/interfaces/api/actuators.py` | executions list, demo apply |
| Frontend | `frontend/src/features/actuators/ExecutionLog.tsx` | execution log block |

## Adding a third decorator

Example: a cooldown that refuses a second command within 10 seconds.

1. Add `CooldownActuatorDecorator(ActuatorPortDecorator)` next to the other decorators. It
   overrides `apply`, raises an `ActuatorPolicyError` subclass with `policy = "cooldown"` when
   it blocks, and otherwise calls `super().apply(...)`.
2. Add one line to `build_actuator_port`, inside the logging decorator so blocked attempts are
   still recorded.
3. Add unit tests around a fake port.

The port, the adapter, the service, the API, the table and the UI stay the same. A blocked
row will show `["cooldown", "logging"]` without any other change.
