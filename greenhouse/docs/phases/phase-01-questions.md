# Phase 1 — Skeleton: answers

## A. Pattern

**1. What is a design pattern? What is it not?**

A design pattern is a common solution to a problem that shows up again and again in
software design. It gives the solution a name and describes how the classes should be
arranged, so two developers can say "Factory Method" and picture the same thing.

It is not a library or code you copy and paste. It is not a class you import, and it is
not a rule you must follow to write good code. Using a pattern where it does not fit just
makes the code harder to read.

**2. The three GoF families**

- Creational — about how objects are made, so the calling code does not need to know the
  exact class or how to build it.
- Structural — about how classes and objects are put together into bigger structures,
  like wrapping or adapting something.
- Behavioural — about how objects talk to each other and who is responsible for an
  algorithm or a decision.

Factory Method is creational, because it decides which object to create.
Strategy is behavioural, because it decides how something behaves and can be swapped.

**3. When to skip a pattern**

Skip it when the thing the pattern handles does not exist yet. If we only have one sensor
type and no plan for another, a factory adds an extra layer for nothing. A normal
constructor is better until there is a second case.

If you add a pattern too early you pay the cost without getting the benefit: more files,
more indirection, and harder tests. And since you are guessing what the second case will
look like, the abstraction often turns out wrong, so later you have to remove it as well
as add the new feature. It is easier to add the pattern once the second case is real.

## B. This phase of the application

**4. Why almost no business logic?**

Because the parts that usually break are the connections between the tiers, not the logic
itself. Phase 1 makes every connection prove itself once: the backend reaches PostgreSQL,
Alembic runs against that same database, the browser gets past CORS, and the frontend
displays the answer.

Empty folders of unwritten classes prove nothing, because none of it has ever run. The
database URL could be wrong or CORS could block everything and you would not know. If you
only find out later, you are debugging the setup and your new feature at the same time.
Running it first gives you a working starting point to compare against.

**5. The four backend layers**

- `domain` — the greenhouse things themselves and the rules about them, for example what
  a sensor is and what counts as a valid reading. Plain Python only.
- `application` — the use cases that use the domain, like "register a device". It
  coordinates steps but knows nothing about the web or the database.
- `infrastructure` — the technical outside world: settings from the .env file, the
  SQLAlchemy engine and session, and the database check.
- `interfaces/api` — the HTTP part: FastAPI routers and response models. In this phase
  that is the `/health` route.

A SQLAlchemy model or a Pydantic HTTP schema must not go in `domain`. They tie the rules
to one database library and one way of sending data, so the rules could not be used or
tested without them.

**6. `/health`, and Scalar instead of Swagger**

It returns `{"status": "ok", "db": "ok"}`. `status` is `ok` or `degraded`, and `db` is
`ok` or `fail`. It runs `SELECT 1` against Postgres and reports what happened.

It checks the database because an API that is running but cannot reach its database cannot
actually do anything useful. If health only said "the process is alive", a monitoring tool
would think a broken server was fine and keep sending requests to it.

Scalar is the one API reference for this course, so `/docs` and `/redoc` are turned off
with `docs_url=None` and `redoc_url=None`. Two documentation pages for the same schema
just means two things to maintain. Both read the same `/openapi.json`, so nothing is lost.

**7. Why Alembic before there is any schema?**

Because the migration tool can be set up wrong, and it is much easier to find that out
when the migration is empty than when you are also writing your first tables. Running the
baseline proves Alembic uses the same `DATABASE_URL` as the app, can connect, and creates
its `alembic_version` table. It also sets the habit early: schema changes come as
migrations.

If you made tables by hand and added migrations later, the database and the code would not
match. Nobody else could recreate your schema, because the `CREATE TABLE` commands only
exist on your machine. The first migration would then have to be written against a
database that already has those tables, so it would fail on a clean setup. That is the
classic "works on my machine" problem.

## C. Compare, contrast, and scenarios

**8. Dependency direction**

The arrows point inwards, towards the domain.

- `domain` imports nothing from the other layers.
- `application` may import `domain`.
- `infrastructure` may import `domain` and `application`.
- `interfaces/api` may import all of them.

Domain code must not import FastAPI, SQLAlchemy or Pydantic HTTP schemas, because those
are choices about how data is delivered and stored, not about the greenhouse. If a rule
imports FastAPI, you can only test it by starting a web server, and swapping the framework
or the database would mean editing business rules that did not actually change.

**9. The badge is not green**

This has nothing to do with patterns, because there are no patterns in Phase 1. It is a
plumbing problem. I would check in this order:

1. Is everything running? Backend on port 8000, and `docker compose ps` showing Postgres
   as healthy.
2. Does the API answer on its own? Open `http://localhost:8000/health`. If it says
   `"db": "fail"`, the problem is the database or the `DATABASE_URL`, not the frontend.
3. Can the browser reach it? If the URL works but the page does not, check the browser
   console for a CORS error, and make sure `CORS_ORIGINS` includes
   `http://localhost:5173`.
4. Does the JSON match? The frontend expects the fields `status` and `db`.

Each step checks one connection, and the result tells you which side to look at next.

**10. What is missing after Phase 1?**

Everything that makes it a real greenhouse system: the actual tables like `devices`,
`sensor_readings` and `alerts`, the entities and use cases, the ten patterns from Phases 2
to 11, the real API endpoints, WebSockets, and the hardening in Phase 12. Right now the
dashboard has six empty cards and `domain` and `application` are empty packages.

Later phases can add all of that without rebuilding anything, because the places to put it
already exist. Entities go in `domain`, use cases in `application`, routers in
`interfaces/api`, every schema change is a new Alembic revision on top of the baseline,
and each dashboard section gets mounted into the placeholder id that is already there
(`sensors`, `config`, `automation`, `overview`, `controls`, `events`). That is the reason
Phase 1 insists on the empty folders and the migration tooling.