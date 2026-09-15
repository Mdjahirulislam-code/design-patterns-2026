# Phase 1 — Skeleton: answers
A. Pattern
1. What is a design pattern? What is it not?

A design pattern is a common solution for a repeated software problem. It gives developers a clear way to organize code.

It is not a ready-made code, library, or something we copy and paste. It should only be used when it fits the problem.

2. The three GoF families
Creational: Handles how objects are created.
Structural: Handles how classes and objects are connected.
Behavioural: Handles how objects communicate and work together.

Factory Method is creational because it creates objects.
Strategy is behavioural because it changes how something works.

3. When to skip a pattern

Do not use a pattern too early. If there is no real problem, it only adds extra code and makes the project harder.

Add a pattern when the need actually appears.

B. This phase of the application
4. Why almost no business logic?

Phase 1 is about checking that all parts work together. It makes sure the backend, database, frontend, and connections are working.

Empty code does not prove anything until it runs.

5. The four backend layers
domain: Main business objects and rules.
application: Handles the main tasks and use cases.
infrastructure: Handles database and technical settings.
interfaces/api: Handles HTTP routes and user requests.

Database models and API schemas should not be inside the domain because they connect it to specific technologies.

6. /health, and Scalar instead of Swagger

The /health route checks if the API and database are working.

It returns the status of the system.

Scalar is used for API documentation. Swagger and Redoc are disabled because maintaining multiple docs is unnecessary.

7. Why Alembic before schema?

Alembic is set up first to make sure database connections and migrations work correctly.

If tables are created manually first, the database and code can become different and cause problems later.

C. Compare, contrast, and scenarios
8. Dependency direction

Dependencies should point towards the domain.

The domain should not depend on FastAPI, SQLAlchemy, or other tools because business rules should stay independent.

9. The badge is not green

I would check:

Are backend and database running?
Does /health work?
Is there a CORS problem?
Does the frontend receive the correct JSON data?

Each step helps find where the problem is.

10. What is missing after Phase 1?

Phase 1 only creates the basic structure.

Later phases will add database tables, real features, APIs, patterns, WebSockets, and security improvements.

The structure is ready so new features can be added easily later.
