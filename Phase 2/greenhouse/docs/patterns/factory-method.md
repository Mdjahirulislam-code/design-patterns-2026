# Factory Method — Phase 2

## Problem

In this phase, the greenhouse supports different sensor types, such as moisture and light sensors. Each sensor type has its own device type and default settings. If the API created sensors directly, the route would need to know every sensor class and contain more `if/elif` checks when new sensors are added. This would make the code harder to maintain.

## Solution

The Factory Method pattern moves sensor creation into separate creator classes.

`SensorCreator` defines the common creation method. `MoistureSensorCreator` and `LightSensorCreator` create their own sensor types and provide the correct default configurations.

The service selects the correct creator using the creator registry, then saves the created sensor through the repository. This keeps sensor creation separate from HTTP routes and database code.

## Main files

- `backend/src/domain/sensors/entity.py`
  - Contains the Sensor domain object.

- `backend/src/domain/sensors/creators.py`
  - Contains the creator classes and creator registry.

- `backend/src/application/sensors/service.py`
  - Connects the creator and repository.

- `backend/src/infrastructure/persistence/device_repository.py`
  - Handles saving and reading sensors from the database.

- `backend/src/interfaces/api/sensors.py`
  - Handles API requests and responses.

## Extension example

A new temperature sensor can be added without changing the API route.

Steps:

1. Create `TemperatureSensorCreator`.
2. Set `device_type` as `temperature_sensor`.
3. Add temperature default settings.
4. Add `"temperature"` to the creator registry.
5. Add a test for the new creator.

The API does not need to know how the temperature sensor is created.