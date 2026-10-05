# Current Phase

**Phase 5 — Adapter Pattern**

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
