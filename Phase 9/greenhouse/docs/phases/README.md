# Current Phase

**Phase 9 — Decorator Pattern**

---

# Phase Overview

The project is developed incrementally through design pattern phases.

Current implementation:

| Phase | Pattern / Focus | Database | Status |
|---|---|---|---|
| 01 | Skeleton (no pattern) | Tooling only; DB reachable | Done |
| 02 | Factory Method | devices (sensors) | Done |
| 03 | Abstract Factory | device_family, actuator rows | Done |
| 04 | Builder | locations, zones, configuration fields | Done |
| 05 | Adapter | sensor_readings, sampling columns on devices | Done |
| 06 | Strategy | automation_rules (one strategy per location) | Done |
| 07 | Facade | no new table (composes existing tables) | Done |
| 08 | State | actuator_states (one lifecycle state per actuator) | Done |
| 09 | Decorator | actuator_execution_log (one row per command attempt) | Done |

---

# Phase 4 Features

Phase 4 introduces the Builder Pattern for creating greenhouse configurations.

The system can now build complex greenhouse configurations step by step instead of creating objects directly.

Added features:

- Location configuration builder
- Zone configuration builder
- Location persistence
- Zone persistence
- Moisture threshold configuration
- Watering schedule configuration
- Location API endpoints
- Zone management APIs
- Device-zone assignment support
- Frontend configuration display

---

# Builder Pattern

The Builder Pattern separates the construction of complex objects from their final representation.

Instead of creating a complete greenhouse configuration manually:

---

# Phase 5 Features

Phase 5 introduces the Adapter Pattern for reading sensors.

Sensors are read through a port. Each source has its own adapter that translates into one normalized reading, and every reading is stored.

Added features:

- `SensorPort` and `ActuatorPort` in the domain
- Simulation, vendor stub and MQTT sensor adapters
- Simulation actuator adapter (stub, no GPIO)
- `sensor_readings` table with history
- `sampling_interval_seconds` and `tracking_enabled` on devices
- `ReadingIngest` as the only writer of readings
- Simulation sampler started with the API
- Read, history and sampling API endpoints
- Sensor cards with Read now, interval, tracking and source badge

Pattern note: [docs/patterns/adapter.md](../patterns/adapter.md)

Questions: [phase-05/questions.md](phase-05/questions.md)

---

# Phase 6 Features

Phase 6 introduces the Strategy Pattern for irrigation decisions.

Each location saves an automation strategy. Evaluate builds one context per zone from the zone thresholds and the latest stored moisture reading of the sensors in that zone, and the saved strategy recommends irrigate or wait.

Added features:

- `AutomationStrategy` interface with `decide(context)`
- Conservative and aggressive moisture strategies
- `LocationAutomationContext` and `Recommendation` as plain domain objects
- `automation_rules` table with one strategy per location
- `AutomationService` that builds contexts and runs the saved strategy
- Strategy list, save and evaluate API endpoints
- Strategy panel on the dashboard

Pattern note: [docs/patterns/strategy.md](../patterns/strategy.md)

Questions: [phase-06/questions.md](phase-06/questions.md)

---

# Phase 7 Features

Phase 7 introduces the Facade Pattern for the dashboard overview.

One request returns the whole state of a location. The facade combines the existing repositories and the automation service and builds one read model. No new table is needed.

Added features:

- `LocationOverviewFacade` with `get_overview(location_id)`
- `LocationOverviewDto` with location, assigned device counts, zones, strategy key and last recommendation
- Every zone with its assigned devices and their newest readings
- Newest readings of all devices loaded in one query
- Recommendation computed by evaluate on each request
- `GET /api/locations/{location_id}/overview`
- Overview panel on the dashboard

Pattern note: [docs/patterns/facade.md](../patterns/facade.md)

Questions: [phase-07/questions.md](phase-07/questions.md)

---

# Phase 8 Features

Phase 8 introduces the State Pattern for the actuator lifecycle.

Every actuator has a stored state: off, idle, running, error or maintenance. Each state is its own object that decides which commands are allowed and where they lead. Illegal moves are rejected in the domain and never saved.

Added features:

- State objects and `ActuatorContext` in the domain
- `actuator_states` table, seeded to idle for existing actuators
- `ActuatorStateService` that loads, checks and saves
- `state` and `allowed_commands` on device read models and on the overview
- `GET /api/devices/{device_id}/state` and `POST /api/devices/{device_id}/transition`
- State badges with an allowed-commands tooltip on the dashboard

Pattern note: [docs/patterns/state.md](../patterns/state.md)

Questions: [phase-08/questions.md](phase-08/questions.md)

---

# Phase 9 Features

Phase 9 introduces the Decorator Pattern around the actuator port.

Every command to an actuator goes through a stack of wrappers with the same interface: logging, then max run time, then the simulation adapter. Every attempt is stored, and an actuator that has been running for 30 minutes is blocked.

Added features:

- `ActuatorPortDecorator` base class with the same `apply` as `ActuatorPort`
- `LoggingActuatorDecorator` that writes one row for every attempt
- `MaxRunTimeActuatorDecorator` that blocks after 30 minutes in the state running
- Factory that builds the chain in one place
- `actuator_execution_log` table
- `GET /api/actuators/executions` and a demo `POST /api/actuators/{device_id}/apply`
- Execution log block on the dashboard

Pattern note: [docs/patterns/decorator.md](../patterns/decorator.md)

Questions: [phase-09/questions.md](phase-09/questions.md)
