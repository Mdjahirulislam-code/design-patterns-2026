# Current Phase

**Phase 4 — Builder Pattern**

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
