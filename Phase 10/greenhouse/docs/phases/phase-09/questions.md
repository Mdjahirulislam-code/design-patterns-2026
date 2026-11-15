# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** [Guide 09](../../materials/guides/09-decorator.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

> [!NOTE]
> ***Your Answer***
>
> Decorator adds extra behaviour to an object by wrapping it in another object that has the same interface. The caller uses the wrapper in the same way as the original object. With subclasses, every combination of behaviours needs its own class, so three policies already give many classes like `LoggingRetryMaxRuntimeActuator`. With wrappers, each policy is one small class, and I can stack the ones I need in any combination. Adding a new policy means one new class, not a new class for every combination.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

> [!NOTE]
> ***Your Answer***
>
> The component is `ActuatorPort` with the method `apply(device_id, command, payload)`. The concrete component is `SimulationActuatorAdapter`, which does the real work. The decorator is `ActuatorPortDecorator`, a base class that holds the wrapped port and forwards `apply` to it. The concrete decorators are `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator`. Every decorator presents the same `ActuatorPort` interface. It must match, because then the caller cannot tell if it has the adapter or a wrapper, and a wrapper can be put around another wrapper. If the interface was different, the wrappers could not be stacked.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

> [!NOTE]
> ***Your Answer***
>
> The outer wrapper runs first and sees everything the inner one does. In my project logging is around max run time. When max run time blocks a command, the error goes back through logging, so logging writes a row with `success=false`. If max run time was around logging, the block would happen before logging was reached, and the blocked attempt would leave no row at all. I have a test that shows this. With logging and retry it is similar. Logging around retry gives one row for the whole call, and retry around logging gives one row for every attempt.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

> [!NOTE]
> ***Your Answer***
>
> `ActuatorPort` is the abstract class from Phase 5 with one method, `apply`, that sends a command to an actuator. I stacked `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator` around `SimulationActuatorAdapter`. The order is logging, then max run time, then the adapter. The chain is built in the factory function `build_actuator_port`, and `dependencies.py` gives the result to `ActuatorExecutionService` as a plain `ActuatorPort`. It is not in the router because then the policies would only work for that one HTTP route. Other callers, like the Phase 10 commands, would skip them. In the factory the order is in one place and can be tested without HTTP.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

> [!NOTE]
> ***Your Answer***
>
> A blocked attempt is still something that happened, and the operator needs to see it. Without a row it would look like nobody tried to send the command, and nobody would know why the pump did not react. The row with `success=false` shows that the attempt was refused. The policy name `maxRunTime` in `policy_applied` shows which rule refused it, and the message `Max run time exceeded` gives the reason. This also helps when looking for problems later.

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

> [!NOTE]
> ***Your Answer***
>
> The decorator reads the row in `actuator_states` for the device. If the state is `running` and `updated_at` is at least 30 minutes before the current time, the actuator has been running too long and the command is blocked. `updated_at` is set when the state changes, so it shows when the actuator started running. The data must come from State because Phase 8 already owns the lifecycle. If the decorator kept its own timer or its own running flag, there would be two versions of the truth and they could disagree, for example after a restart. The decorator should only read the state and add its policy.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

> [!NOTE]
> ***Your Answer***
>
> Text in stdout is lost when the container restarts, it cannot be queried, and the dashboard cannot read it. Rows in `actuator_execution_log` stay after a restart, can be listed newest first through the API, and can be shown to the operator. After a blocked attempt and a refresh, the UI should show a new row at the top with the time, the device, a failed badge, the policies `maxRunTime` and `logging`, and the message `Max run time exceeded`.

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

> [!NOTE]
> ***Your Answer***
>
> Decorator keeps the interface and adds behaviour. In Phase 9 the logging and max run time decorators are still an `ActuatorPort`, they only add logging and a time check around `apply`. Adapter changes the interface and translates. In Phase 5 the vendor stub adapter takes the vendor payload with its own field names and units and turns it into our `Reading` behind `SensorPort`.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

> [!NOTE]
> ***Your Answer***
>
> With inheritance the policies are fixed in the class, so logging with max run time is one subclass, logging alone is another, and every new policy doubles the number of combinations. With composition each policy is its own wrapper and the chain is built in the factory. To add a policy I write one class and add one line in the factory. To remove a policy I delete that line. The other classes do not change, and the order can also be changed in the same place.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A decorator with a different signature is not the same port any more. The caller would need to know which wrapper it has, and other decorators could not wrap it, so the stack breaks. That is closer to an Adapter than to a Decorator. Ignoring the order is a trap because the order decides what is observed. If logging is inside a retry, it writes one row for every attempt, and if it is outside, it writes one row for the whole call. If logging is inside max run time, blocked attempts are not logged at all. Without knowing the order, the log cannot be trusted.
