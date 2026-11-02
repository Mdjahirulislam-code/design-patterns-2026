# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** [Guide 07](../../materials/guides/07-facade.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> Facade gives one simple entry point to a group of classes that would otherwise all need to be called one by one. The caller asks for the result and the facade does the steps inside. If every handler or screen repeats the same steps, the same code is copied in many places. Each copy can make small mistakes, for example counting unassigned devices or forgetting an empty zone. When the steps change, every copy has to be fixed, and the handlers become long and hard to test.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> The facade should only call other parts in the right order and put the results together. It should not become a god object that also decides irrigation, translates sensor data and writes to the database. The irrigation policy stays in the strategy classes and is reached through `AutomationService.evaluate`. Sensor translation stays in the Phase 5 adapters. Persistence stays in the repositories. My `LocationOverviewFacade` only reads from those parts and builds the overview DTO.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> Use Facade when one use case needs several subsystems and many callers need the same combined result, like the overview that needs locations, devices, readings and the strategy. Skip it when one repository call already gives what the caller needs, because then the facade only adds an extra layer. Also skip it when the real problem is that an interface does not match what we expect. That needs an Adapter, not a Facade.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> It returns one `LocationOverviewDto`. It has the `location` with id and name, `device_counts` with the number of assigned sensors and actuators, and a list of `zones`. Every zone has its name, its low and high moisture thresholds, its assigned `devices` and its `latest_readings`. A reading has the value, unit and time, and also `tracking_enabled` and `sampling_interval_seconds`, which are copied from the device. At the end there is the saved `strategy_key` and the `last_recommendation` with action and reason. Both are null when no strategy is saved. The readings can come from the sampler or MQTT because all of them are written to the same `sensor_readings` table by the same ingest path. The overview only wants the newest row, not where it came from. It is scoped by `location_id` because zones, device assignment and the saved strategy all belong to a location in this system.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> The overview is only a view of data that is already stored, so it needs no new table. Phase 2 and 3 have the `devices` table, Phase 4 has `locations`, `zones` and the device zone assignment, Phase 5 has `sensor_readings` and the sampling columns, and Phase 6 has `automation_rules`. The facade reads these through the existing repositories and calls the existing evaluate service. The recommendation is computed on each request and is not saved.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> If the handler called the repositories itself, the overview logic would live in the HTTP layer and could not be reused or tested without HTTP. With only the facade, the handler just maps the result and the not found error. In tests I can give the facade fake repositories and test all the rules without a database, and I can replace the whole facade in the API test. If I later change the queries, for example to load the newest readings in one query, only the facade or the repository changes and the handler stays the same.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> If React made several calls and merged them, the business rules would be copied into the frontend, for example which devices count as assigned. The answers could also come from different moments, so the page could show a mix of old and new data. It would also mean more requests. With one fetch the backend builds the whole snapshot at the same time and the page only shows it. A new reading or a new saved strategy is already in the database, and the facade reads the database on every request. So the next overview fetch or a click on Refresh shows it without any extra code in React.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> Adapter makes an existing interface usable by translating it to the interface we want. In Phase 5 the vendor stub adapter turns the vendor payload into our `Reading`, and the MQTT adapter turns a payload dict into a `Reading`. Facade makes a subsystem simpler to call. In Phase 7 `LocationOverviewFacade` gives one `get_overview` method over locations, devices, readings and the automation service. Nothing is translated there, the parts are only combined.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> N+1 means one query to get the list of devices and then one more query for each device to get its latest reading. With 50 devices that is 51 queries, and it gets slower as the greenhouse grows. In my version the facade first loads all assigned devices of the location in one query. Then it calls `latest_for_devices` in the reading repository, which gets the newest reading for all those device ids in one query with `DISTINCT ON`. The SQL stays in the repository and the router does not know about it.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> The facade sits in front of many parts, so it is easy to catch everything in one place and return one message. But then the client cannot react correctly. A missing location should be a 404 so the user can pick another location. A database outage is a server problem and should be a 500 that shows up in the logs. A strategy error points to bad saved data. With one generic message nobody knows which problem happened, and it is much harder to debug. The facade should let each error keep its own meaning and only map the ones it understands, like not found.
