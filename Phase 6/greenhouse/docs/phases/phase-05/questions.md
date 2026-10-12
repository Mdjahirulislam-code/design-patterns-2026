# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

> [!NOTE]
> ***Your Answer***
>
> Adapter lets two things work together when their interfaces do not match. It sits between them and translates.
> If business code talks to a vendor protocol directly, the vendor's field names, units, XML and status codes end up everywhere in the code. Then one vendor change breaks many files, and adding a second vendor means writing the same logic again.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> Target / port is the interface our code wants (`SensorPort`). Adaptee is the thing with the different interface (vendor SDK, MQTT payload, simulation generator). Adapter is the class that implements the port and calls the adaptee. Client is the code that uses the port (`ReadingIngest`).
> The adapter translates names, units, timestamps and error codes into our shape. It must not decide business policy, for example when to water or what counts as too dry.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Modern code prefers the object adapter. The adapter keeps the adaptee as a field and calls it.
> Composition is more flexible: the adaptee can be swapped or faked in tests, and it works in languages without multiple inheritance. A class adapter is tied to one concrete class. In this lab `VendorStubSensorAdapter` holds a vendor client, it does not inherit from it.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
> `SensorPort` is an abstract class in the domain with one method, `read(device)`. Every adapter returns a `Reading` with `device_id`, `value`, `unit`, `source` and `recorded_at`.
> The application services depend on the port so they do not need to know which device is behind it. We can add or change adapters without touching `ReadingIngest`, and tests can use a fake. The domain also stays free from vendor code.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
> The different raw shape is the point because that is the real problem Adapter solves. The simulation makes a number in code, the vendor stub gives its own field names with percent and epoch milliseconds, and MQTT gives a small dict. All three must end as the same `Reading`.
> `source` is set by the adapter itself, so a stored row shows if it came from `simulation`, `vendor` or `mqtt`.
> The MQTT translator only turns a dict into a `Reading`. Transport is a different job from translation. If it opened a broker, tests would need a running broker and the adapter would be tied to one transport. Phase 12 can send the same dict over device HTTP or a broker and reuse the same translator, so this phase opens neither.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> If we keep only the latest value in memory, it is lost on restart or refresh. Overwriting one row loses the history. Later phases need real stored data: Phase 6 Strategy uses the latest moisture reading of a zone, and the optional Phase 13 charts read the whole history.
> One writer (`ReadingIngest`) keeps the rules in one place. Every row is saved the same way, and Phase 11 can publish `reading.created` from that one place.
> The sampler skips tracking-off devices because the user chose not to record them. It skips MQTT devices because they are real devices that send their own readings, so made-up values for them would be wrong.
> The cards poll because there is no push channel yet. The sampler writes rows in the background and the poll shows them. Phase 12 replaces the poll with WebSocket.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> Missing device is 404 because the resource does not exist. Adapter failure is 400 with a detail message, for example when an MQTT device cannot be read on demand or a payload cannot be translated.
> The router should only see `ReadingDto`. If it saw vendor-shaped types, the vendor format would leak into the public API and the frontend, and changing the vendor would break the API. Translation belongs in the adapter.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> Adapter example: `VendorStubSensorAdapter` takes the vendor payload (`statusCode`, `measurement.val` in percent) and returns our `Reading` through `SensorPort`. The interface shape changes.
> Facade example: one simple operation such as "water this zone" that inside reads the latest reading, checks the zone and sends the command to the pump. Nothing is translated, the caller just does not have to call every service itself.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> Adapter gives the client a different interface than the wrapped object has. Decorator keeps the same interface and adds behaviour around it.
> The vendor adapter turns the vendor SDK into `SensorPort`. In Phase 9 a decorator will wrap `ActuatorPort` and still be an `ActuatorPort`, only with extra behaviour such as logging.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> It is a trap because the rule would only work for that one vendor. Simulation and MQTT readings would skip it, or the rule would be copied into every adapter. Business logic would also be hidden in infrastructure, and thresholds belong to a zone, not to a vendor.
> The decision should live in a Strategy (Phase 6) that uses the zone thresholds and the latest stored reading. The adapter should only translate fields, units, timestamps and errors into a `Reading`.
