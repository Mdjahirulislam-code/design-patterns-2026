# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

> [!NOTE]
> ***Your Answer***
>
> The State pattern lets an object change its behaviour when its state changes. Each state is its own class, and that class decides what is allowed next. With boolean flags and `if` checks, the same rules are written in many places, for example in the router, the service and the UI. It is easy to forget one check, and flags can end up in combinations that make no sense. Adding a new state means finding and changing every `if`.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

> [!NOTE]
> ***Your Answer***
>
> The context is `ActuatorContext`, which holds the current state of one actuator. The state interface is `ActuatorState` with `handle`, `command_to` and `allowed_commands`. The concrete states are `OffState`, `IdleState`, `RunningState`, `ErrorState` and `MaintenanceState`. The client is `ActuatorStateService`, and later the Phase 10 commands. When a command comes in, the context asks the current state object. If the state allows it, the state returns the next state and the context switches to it. The guards live in the state objects, because each state has its own table of commands it accepts. If a command is not in that table, the state raises `IllegalTransitionError`.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

> [!NOTE]
> ***Your Answer***
>
> `allowed_commands` is the list of commands that the current state accepts. It comes from the state object in the domain. If the UI only got the state string, it would have to know the rules itself, so the rules would be copied into React and could easily get out of sync with the backend. With `allowed_commands` the UI just shows what the backend says. If a rule changes, only the domain changes.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).

> [!NOTE]
> ***Your Answer***
>
> I implemented `off`, `idle`, `running`, `error` and `maintenance`, and a new actuator starts in `idle`. `start` moves idle to running and `stop` moves running back to idle. `report_fault` moves idle, running or maintenance to error. Out of error, `reset` goes to idle, `begin_maintenance` goes to maintenance and `power_off` goes to off. `power_on` moves off to idle and `power_off` moves idle to off. `begin_maintenance` moves idle to maintenance and `end_maintenance` moves maintenance back to idle. Everything else is illegal, for example running to maintenance, because the actuator must be stopped first.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

> [!NOTE]
> ***Your Answer***
>
> Memory is lost when the backend restarts or crashes, and with more than one backend process each one would have its own different value. The state of a pump is real information that other parts need, like the overview and later the commands. So it is stored in `actuator_states` with one row per actuator. After a restart every actuator must still have the same state as before, and `allowed_commands` must still match that state.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

> [!NOTE]
> ***Your Answer***
>
> If an illegal move was saved, the database would say the actuator is in a state it never really reached, for example maintenance while the pump is still running. Everything that reads that row would then be wrong. So the domain checks first and only a legal move is saved. I return 409 Conflict, because the request itself is valid but it conflicts with the current state of the actuator. An unknown target name returns 400. The rule must live in the domain because the API, the overview and the Phase 10 commands all need the same rule. React can be skipped by calling the API directly, so a rule only in React protects nothing.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

> [!NOTE]
> ***Your Answer***
>
> Each actuator card shows a colored badge for its state, and the tooltip of the badge lists the commands that are allowed now. The overview zone cards show the same badge. The demo control lets you pick a target state, and if the backend rejects it the reason is shown under the card. The UI does not decide anything itself. In Phase 10 each command name in `allowed_commands`, like `start` or `stop`, can become a Command object and a button. The command will check the same state before it runs and use `ActuatorContext.apply` to move to the next state.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

> [!NOTE]
> ***Your Answer***
>
> In State the object changes itself when something happens. A pump moves from idle to running when it is started, so the variation is a lifecycle. In Strategy the user or the client picks the object, and it stays until someone picks another one. In Phase 6 the operator chooses the conservative or aggressive irrigation strategy for a location, so the variation is a selectable policy.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

> [!NOTE]
> ***Your Answer***
>
> Three booleans give eight combinations, but only some of them make sense. Nothing stops code from setting `is_running` and `is_maintenance` to true at the same time, especially when different places change different flags. With state objects the actuator has exactly one state at a time, and it can only change through a transition that is in the table. So an impossible combination like running and in maintenance cannot exist.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A state class with HTTP codes or database commits mixes the domain with the web and the database. It cannot be tested without them and cannot be reused by other callers like the Phase 10 commands. It could also commit before the transition is checked. The state should only decide, the service should save, and the router should map errors. A state that changes a flag directly skips the guard, so an illegal move can happen and nothing records it. Every change must go through the transition so the rules are always checked.
