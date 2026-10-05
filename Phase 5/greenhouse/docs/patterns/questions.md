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
> An adapter helps two systems work together when their interfaces are different. It translates the data, so the main code does not need to depend on one vendor.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> An adapter connects different interfaces by translating the data. The target is what our code wants, the adaptee is the different system, and the adapter connects them without adding business rules.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Modern code usually uses an object adapter because it is more flexible. The adapter keeps the adaptee as a field and uses it instead of inheriting from it.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
>SensorPort defines how the system reads sensors, and adapters return the same Reading format. This keeps vendor code out of the main application and makes testing easier.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
>Different inputs are used to show the real Adapter problem. The adapter changes them all into the same Reading format, while transport and translation stay separate.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> Keeping only the latest value means data can be lost after restart. Saving every reading keeps the history, and ReadingIngest keeps all the saving rules in one place. The sampler skips tracking-off and MQTT devices, while the cards use polling until WebSocket is added.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> A missing device gives a 404 error, while an adapter problem gives a 400 error. The router only uses ReadingDto, so vendor data stays inside the adapter.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> Adapter: It changes the vendor data into our Reading format.
> Facade: It gives one simple operation that handles many steps inside, so the caller has less work.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> An adapter changes the interface, while a decorator keeps the same interface and adds extra behavior. The adapter makes the vendor SDK work with SensorPort, while the decorator adds things like logging to ActuatorPort.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> This rule would only work for one vendor and could cause the business logic to be repeated. The adapter should only translate the data, while the Strategy handles the zone rules and thresholds.