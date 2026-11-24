# Phase 11 — Observer questions

**Pattern / focus:** Observer.

**Read first:** [Guide 11](../../materials/guides/11-observer.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example live auction bids) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the event bus, alerts, publishers, and the event feed from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Observer in plain language. What is a **one-to-many** dependency here, and why must the subject notify dependents **without** knowing their concrete classes?

> [!NOTE]
> **_Your Answer_**
>
> Observer lets one object tell many other objects that something happened, so they can react to it. One-to-many means that one event, for example a new reading, can have zero, one or many subscribers. In my project a `reading.created` event goes to the moisture threshold subscriber, and later it can also go to a WebSocket or a statistics subscriber. The subject must not know their concrete classes, because then it would have to change every time a new reaction is added. When it only knows the handler type, I can add or remove subscribers without touching the code that publishes.

2. Name the participants (**subject / event bus**, **observer / subscriber**, **concrete observers**, **event**, **publisher**). What does `subscribe` / `unsubscribe` / `publish` (or `notify`) each do? This example’s `EventBus` implements `subscribe` and `publish` only.

> [!NOTE]
> **_Your Answer_**
>
> The subject is `EventBus`. A subscriber is any handler that takes an event. The concrete observers are `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`. The events are small dataclasses like `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged` and `AlertCreated`. The publishers are `ReadingIngest`, `CommandService` and `ActuatorStateService`, and they only know the `EventPublisher` interface. `subscribe` adds a handler for one event type. `publish` sends an event to every handler of that type, in the order they subscribed. `unsubscribe` would remove a handler, but my bus does not have it, because the bus is built again for every request in `build_event_bus`.

3. When should you use Observer, and when should you skip it (only one listener forever; or you need a strict multi-step workflow with guaranteed order)?

> [!NOTE]
> **_Your Answer_**
>
> Observer is useful when one thing that happens should cause several reactions, and when the reactions can change over time without changing the code that causes them. Alerts, logging, statistics and live updates are good examples. I would skip it when there is only one listener and there will never be more, because a direct call is easier to read and to debug. I would also skip it for a strict workflow where step two must always run after step one and the result matters, like checking the state and then running a command. That should be written as normal calls in one service, so the order and the errors are clear.

## B. This phase of the application

4. Give at least two **domain events** you publish in this lab, including `reading.created` (only when `tracking_enabled` is true), a threshold-crossed event, command-failed, and `ActuatorStateChanged`. The persistence subscriber stores `state.changed` only when that state is `error`. Who publishes `reading.created`, and why do a manual read, the simulation sampler, and MQTT translation share that one ingest publish? Why must a publisher **not** import the alerts repository or the UI?

> [!NOTE]
> **_Your Answer_**
>
> I publish `reading.created`, `threshold.crossed`, `command.failed` and `state.changed`, and also `alert.created` after an alert is stored. `reading.created` is published by `ReadingIngest` after the reading row is stored, and only when the sensor has `tracking_enabled` set to true. The manual read, the simulation sampler and the MQTT translation all store their readings through `ReadingIngest.record`, so the event is published in one place. If each path published by itself, one of them could be forgotten and its readings would never create alerts. A publisher must not import the alerts repository or the UI, because then it would know who reacts to its events, and that is what Observer removes. I have a test that checks that the publisher files do not import anything about alerts.

5. What does `AlertPersistenceSubscriber` (or your equivalent) do when it handles an event? Name the three stored rows: `threshold.crossed` / `warning` / `Moisture below zone low`, `command.failed` / `warning` / the failure message, and `state.changed` / `critical` / `Actuator entered error`. Why do alerts live in the `alerts` table so the event feed still shows them after a **refresh**?

> [!NOTE]
> **_Your Answer_**
>
> It turns the event into one row in the `alerts` table with the location, the zone, the device, the severity, the message and the event type, and then it publishes `AlertCreated`. A `threshold.crossed` event gives a `warning` with `Moisture below zone low`. A `command.failed` event gives a `warning` with the failure message, for example `Max run time exceeded`. A `state.changed` event to `error` gives a `critical` alert with `Actuator entered error`, and other state changes are ignored. The alerts are stored in a table because an event only exists while the request runs. After a refresh or a restart the feed loads the alerts again from `GET /api/alerts`, so nothing is lost.

6. The dashboard Event feed **polls** `GET /api/alerts` every 5 seconds in this phase. `services/realtime.ts` is only a **stub**. Why is full WebSocket **not** required in this phase? What should Phase 12 plug into so you do **not** re-implement pub/sub inside socket handlers? Phase 12 subscribes a dashboard socket to this same bus, and the example publishes `AlertCreated` after each insert for that socket.

> [!NOTE]
> **_Your Answer_**
>
> The goal of this phase is the event bus and the subscribers on the backend. The alerts are already stored, so polling every 5 seconds is enough to show them, and it is simple and easy to test. A WebSocket would add connections and reconnect logic, which belongs to the next phase. In Phase 12 the socket should subscribe to the same `EventBus`, for example to `AlertCreated`, which my persistence subscriber already publishes after every insert. Then the socket handler only sends the event on to the browser, and the `subscribeRealtime` function in `realtime.ts` gets a real body. No second pub/sub system is needed.

7. Describe the must-demo path: a **tracked** low-moisture reading leads to an alert row that appears in the feed after poll. Which objects collaborate (reading pipeline → bus → subscriber → API → UI), and which object must **not** write the alert directly? What is stored, and what is not published, when `tracking_enabled` is false?

> [!NOTE]
> **_Your Answer_**
>
> A moisture sensor in Zone 1 with tracking on is read, either with Read now or by the sampler. `ReadingIngest` stores the reading and publishes `ReadingCreated` on the bus. `MoistureThresholdSubscriber` sees that the value is below the zone low and publishes `ThresholdCrossed`. `AlertPersistenceSubscriber` stores a `warning` row in `alerts` and publishes `AlertCreated`. `AlertQueryService` returns the row through `GET /api/alerts`, and the Event feed shows it at the next poll. In my test a value of 0.487 with a zone low of 0.7 gave the alert. `ReadingIngest` must not write the alert directly, it only publishes. When `tracking_enabled` is false, the reading is still stored in `sensor_readings`, but `reading.created` is not published, so no alert is created.

## C. Compare, contrast, and scenarios

8. Contrast Observer with **Facade**. Facade simplifies **calling into** a subsystem. Observer **fans out** notifications after something happened. How do both appear in this greenhouse (Phase 7 overview vs this phase)?

> [!NOTE]
> **_Your Answer_**
>
> A facade is something I call when I want an answer. The caller knows the facade and waits for the result. The Phase 7 overview facade collects the location, the zones, the devices, the readings and the recommendation into one result for one request. Observer goes the other way. The publisher does not ask for anything, it only says that something happened, and the bus sends it to whoever is listening. In this phase a new reading or a failed command is sent out to the alert subscribers. The facade pulls data together for the caller, and the observer pushes news out to many receivers.

9. Contrast Observer with **Command**. Command captures **intent to act**. Observer propagates **outcomes**. How can `execute()` publish an event without the command class knowing who persists alerts?

> [!NOTE]
> **_Your Answer_**
>
> A command is a request to do something, like `stop_pump`. It has one receiver and the caller wants to know how it ended. An event says what already happened, like `CommandFailed`, and it can have many subscribers or none. In my project the command classes do not publish anything themselves. `CommandService` runs the command through the invoker, writes the result to `command_log`, and then publishes `CommandFailed` or `ActuatorStateChanged`. It only has an `EventPublisher` that was given to it in the composition root, so it does not know that `AlertPersistenceSubscriber` exists or that alerts are stored at all.

10. One subscriber throws during `notify` / `publish` and aborts the loop, so later subscribers never run. Why is that a trap? What should the bus do so a failing alert writer does not block metrics (or later WebSocket) subscribers?

> [!NOTE]
> **_Your Answer_**
>
> It is a trap because the subscribers are supposed to be independent, but one broken subscriber would then stop all the others. The order of subscribing would decide which ones still work, and the error could also go back to the publisher, so a reading or a command could fail only because an alert could not be written. In my `EventBus` every handler is called inside its own try and except. If a handler raises, the bus logs the error, stores it in `bus.errors` and continues with the next handler. The publisher never sees the error. I have a test where the first handler raises and the second one still runs.
