# Adapter pattern (Phase 5)

## Problem


Different sensors give data in different formats.

Simulation gives a simple number.
Vendor gives fields like probeSerial, statusCode, and tsEpochMs.
MQTT gives a small data message.

If we use these formats directly, the code becomes difficult to manage. Adding another vendor would also need many changes.

Solution

The Adapter changes all different sensor data into one common format called Reading.

Reading contains:

device ID
value
unit
source
recorded time

The adapter only changes the data. It does not decide things like when to water.

Main parts
Target: SensorPort
Adaptee: Sensor or vendor data
Adapter: Changes the data into Reading
Client: ReadingIngest and SimulationSampler

The adapter uses the sensor as a field instead of inheriting from it.

Where the code is
Domain: Defines SensorPort and Reading.
Application: Handles readings and sampling.
Infrastructure: Contains the different adapters.
API: Provides the sensor routes.
Frontend: Shows sensor readings.
Adapter selection

The system chooses the correct adapter for each device.

Simulation → SimulationSensorAdapter
Vendor → VendorStubSensorAdapter
MQTT → MqttSensorAdapter

MQTT devices send their own data, so the system does not pull data from them.

Simulation values
Moisture: 0.2–0.6 vwc
Light: 200–2000 lux
Storage

All readings are saved in the database. ReadingIngest is the main place that saves readings. This keeps the reading history.

API
POST /api/sensors/{id}/read → gets a reading.
GET /api/sensors/{id}/readings → shows reading history.
PATCH /api/devices/{id}/sampling → changes sampling settings.
Adding a new vendor

To add a new vendor, make a new adapter and add it to the adapter selection. The main application, database and API do not need big changes.