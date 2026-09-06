# Phase order

Phases are implemented in numerical order. Course completion is at Phase 12;
phases 13–14 are optional enrichment.

| Phase | Pattern / focus | Database (cumulative) | Status |
|------:|-----------------|-----------------------|--------|
| 01 | Skeleton (no pattern) | Tooling only; DB reachable | ✅ done |
| 02 | Factory Method | `devices` (sensors) | |
| 03 | Abstract Factory | `device_family`, actuator rows | |
| 04 | Builder | `locations`, `zones`, config fields | |
| 05 | Adapter | `sensor_readings` | |
| 06 | Strategy | `automation_rules` | |
| 07 | Facade | no schema change | |
| 08 | State | `actuator_states` | |
| 09 | Decorator | `actuator_execution_log` | |
| 10 | Command | `command_log` | |
| 11 | Observer | `alerts` | |
| 12 | API + WebSocket + hardening | indexes, FKs, seeds | |
| 13 | Dashboard polish (optional) | — | |
| 14 | Tests and documentation (optional) | — | |

Migration discipline: one or more numbered migrations per phase when the schema
changes. Applied migrations are never edited; a new revision is added instead.
