# Adapter pattern (Phase 5)

## Problem

Every sensor source speaks its own language.

- The simulation makes a number in code.
- The vendor stub (`AcmeProbeClient`) answers with `probeSerial`, `statusCode`, `tsEpochMs`
  and a `measurement` block in percent or kilolux.
- An MQTT device sends a small dict like `{ "value": 0.41, "unit": "vwc" }`.

If the application services used these shapes directly, vendor field names, units and status
codes would spread into the services, the API and the database. Adding one more vendor would
mean changing all of them.

## Solution

The domain defines one target interface (the port) and one normalized value type. Each source
gets its own adapter that translates into that type.

```text
POST /read  ->  ReadingIngest  ->  SensorPort.read(device)  ->  Reading  ->  sensor_readings
                                        ^
               SimulationSensorAdapter / VendorStubSensorAdapter (selected per device)

MqttSensorAdapter.translate(device, payload) -> Reading -> ReadingIngest.record (Phase 12 caller)
```

`Reading` has `device_id`, `value`, `unit`, `source` and a timezone-aware `recorded_at`.
`source` (`simulation`, `vendor` or `mqtt`) shows which adapter produced the row.

Adapters only translate. They do not decide when to water or what a threshold means.
That policy comes in Phase 6 (Strategy).

## Participants

| Role | In this project |
|------|-----------------|
| Target / port | `SensorPort`, `ActuatorPort` |
| Adaptee | the random generator, `AcmeProbeClient` (fake vendor SDK), the inbound MQTT payload dict |
| Adapter | `SimulationSensorAdapter`, `VendorStubSensorAdapter`, `MqttSensorAdapter`, `SimulationActuatorAdapter` |
| Client | `ReadingIngest` and `SimulationSampler` |

These are object adapters: `VendorStubSensorAdapter` holds a vendor client (composition), it
does not inherit from it.

## Where in the code

| Layer | File | What |
|-------|------|------|
| Domain | `backend/src/domain/sensors/ports.py` | `SensorPort` |
| Domain | `backend/src/domain/sensors/reading.py` | `Reading` |
| Domain | `backend/src/domain/sensors/errors.py` | `DeviceNotFoundError`, `SensorReadError`, `InvalidSamplingError` |
| Domain | `backend/src/domain/actuators/ports.py` | `ActuatorPort` |
| Application | `backend/src/application/readings/service.py` | `ReadingIngest` (`take_reading`, `record`, `list_readings`) |
| Application | `backend/src/application/readings/sampler.py` | `SimulationSampler.run_once(now)` |
| Application | `backend/src/application/readings/sampling.py` | `SamplingService` (interval + tracking) |
| Infrastructure | `backend/src/infrastructure/adapters/sensors/simulation.py` | simulation adapter |
| Infrastructure | `backend/src/infrastructure/adapters/sensors/vendor_stub.py` | fake vendor SDK + vendor adapter |
| Infrastructure | `backend/src/infrastructure/adapters/sensors/mqtt.py` | MQTT payload translator (no broker) |
| Infrastructure | `backend/src/infrastructure/adapters/sensors/selector.py` | adapter selection |
| Infrastructure | `backend/src/infrastructure/adapters/actuators/simulation.py` | `SimulationActuatorAdapter` |
| Infrastructure | `backend/src/infrastructure/persistence/reading_repository.py` | insert / list readings |
| Infrastructure | `backend/src/infrastructure/sampler_runner.py` | background loop started from the app lifespan |
| API | `backend/src/interfaces/api/sensors.py`, `devices.py` | read, history, sampling routes |
| Frontend | `frontend/src/features/sensors/SensorCard.tsx` | Read now, interval, tracking, source badge |

## Adapter selection rule

`select_sensor_port(device)` in `selector.py` is the only place that names adapter classes.

1. `default_config.vendor_stub` is `true` -> `VendorStubSensorAdapter` (`source` = `vendor`).
2. `default_config.protocol` is `simulation` -> `SimulationSensorAdapter` (`source` = `simulation`).
3. `default_config.protocol` is `mqtt` -> there is nothing to pull. The device pushes its
   payload, `MqttSensorAdapter.translate` turns it into a `Reading` and `ReadingIngest.record`
   stores it. `POST /read` on such a device returns 400.

The vendor stub uses its own flag (`vendor_stub`), so it never collides with the two protocol
values. A vendor sensor is created with `POST /api/sensors` and `"adapter": "vendor"`, or with
the "Add vendor moisture" button.

Migration `006` renames the Phase 3 values: `sim` -> `simulation` and `gpio-stub` -> `mqtt`.
The simulation family uses `simulation`, the edge family uses `mqtt`.

## Simulation ranges

| `device_type` | Range | Unit |
|---------------|-------|------|
| `moisture_sensor` | 0.2 to 0.6 | `vwc` |
| `light_sensor` | 200 to 2000 | `lux` |

## Storage and sampling

- `sensor_readings` is append-only, with an index on `(device_id, recorded_at DESC)`.
- `ReadingIngest` is the only writer. Manual read, the sampler and (from Phase 12) MQTT / device
  HTTP all go through it.
- `devices.sampling_interval_seconds` (default 300, minimum 5) and `devices.tracking_enabled`
  (default true) are the source of truth. `default_config.sampling_interval_seconds` is only
  copied once when a device is created.
- The sampler records a device when it is a sensor, `protocol` is `simulation`, tracking is on
  and `now - last recorded_at >= sampling_interval_seconds`. No earlier row counts as elapsed.
  It skips MQTT devices, devices with tracking off and vendor stub devices.
- `SAMPLER_ENABLED=false` turns the background loop off. `SAMPLER_TICK_SECONDS` (default 1)
  sets how often it checks.

## API

| Method | Path | Result |
|--------|------|--------|
| POST | `/api/sensors/{id}/read` | 201 + `ReadingDto`, 404 missing device, 400 adapter error |
| GET | `/api/sensors/{id}/readings?limit=20` | 200 + list, newest first, 404 missing device |
| PATCH | `/api/devices/{id}/sampling` | 200 + sampling settings, 404 missing device, 400 interval below 5 |

```json
{
  "device_id": "<uuid>",
  "value": 0.31,
  "unit": "vwc",
  "source": "simulation",
  "recorded_at": "2026-08-28T09:00:00Z"
}
```

## Extension: a third vendor

1. Write a new class in `infrastructure/adapters/sensors/` that implements `SensorPort` and
   translates the new vendor's payload into `Reading`.
2. Add one branch to `select_sensor_port` (a new flag or protocol value).
3. If the new vendor needs its own label, add it to `SOURCES` in `reading.py`.

`ReadingIngest`, the sampler, the repository, the API and the `sensor_readings` table stay
the same. The same steps work for a real actuator: implement `ActuatorPort` (GPIO, Modbus)
next to `SimulationActuatorAdapter`.
