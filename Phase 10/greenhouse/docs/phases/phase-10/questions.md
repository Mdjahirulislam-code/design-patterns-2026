# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** [Guide 10](../../materials/guides/10-command.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

> [!NOTE]
> **_Your Answer_**
>
> Command turns a request into an object. The object holds everything about the request, which is the type, the device and the payload, and it has a method to carry it out. A bare `actuator.start()` call happens and is gone, and nothing is left to look at. An object can be stored, passed to another part of the program, put in a queue, written to a log, shown in a history, and sometimes undone. In my project every command is written to `command_log`, also when it is rejected.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

> [!NOTE]
> **_Your Answer_**
>
> The command is the `Command` interface with the classes `StartPumpCommand`, `StopPumpCommand` and `SetLightLevelCommand`. The receiver is the decorated `ActuatorPort`, which ends in the simulation adapter. The invoker is `CommandInvoker`. The client is `CommandService`. The service creates the command from the type string with `command_for`. The invoker triggers `execute()`. The receiver does the real work on the actuator, and the saved state is changed by the service through `ActuatorContext` after the command has completed.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

> [!NOTE]
> **_Your Answer_**
>
> It must capture the old values before it changes anything. After the change the old value is gone, so there is nothing to go back to. For example a set light level command would need to remember the previous level before it sets the new one. If it saved the value after the change, undo would only set the new level again. My commands do not support undo in this phase.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

> [!NOTE]
> **_Your Answer_**
>
> I implemented `start_pump`, `stop_pump` and `set_light_level`. The handler only passes the request to `CommandService`, which creates the command and gives it to the invoker. If the router called the adapter directly, it would skip the state check, the decorators and the command log. The rules would also be inside one HTTP route, so other callers would not get them. With a command object and a service, every command takes the same path, and a new command is one new class and one line in the registry.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

> [!NOTE]
> **_Your Answer_**
>
> First the service loads the saved state and asks for `allowed_commands()`. If the command type is not in the list, it writes a `rejected` row and stops. If it is allowed, the invoker runs the command against the decorated port. When the port completes, the service makes the transition, saves the new state if it is different, and writes `success`. When the port raises, for example `Max run time exceeded`, it writes `failed` and the state stays the same. A rejected command must not change the state, because nothing really happened on the actuator and the database would then say something false. It must not reach `apply`, because the adapter would then act on a command that the state does not allow, for example starting a pump that is in maintenance.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

> [!NOTE]
> **_Your Answer_**
>
> `success` means the command was allowed and completed, for example `start_pump` on an idle pump, which becomes running. `rejected` means the state did not allow the command, so it was never sent, for example `stop_pump` on a pump that is idle. `failed` means the command was allowed, but something stopped it on the way, for example `stop_pump` on a pump that has been running for 30 minutes gives `Max run time exceeded`. They are not the same, because a rejected command is a wrong request for the current state and the operator should choose another command. A failed command was a correct request, and the problem is in a policy or in the device, so somebody needs to look at that.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

> [!NOTE]
> **_Your Answer_**
>
> The two tables answer different questions. `command_log` records what the operator asked for and how it ended, with the command type, the payload and the status. It also has the rejected commands. `actuator_execution_log` records every attempt that reached the actuator port and which policies were applied. A rejected command never reaches the port, so it is only in `command_log`. A successful or failed command is in both. If they were one table, the operator intent and the technical attempt would be mixed and harder to read.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

> [!NOTE]
> **_Your Answer_**
>
> Strategy is a way to decide something, and it can be swapped. It only returns an answer and changes nothing. Command is a request that changes something and leaves a record. In this app the Phase 6 strategy looks at the moisture and the zone thresholds and recommends irrigate or wait. The Phase 10 command, for example `start_pump`, carries the action out, changes the actuator state and is stored in the history. The recommendation can be shown without watering, and the command can be sent by the operator when it is needed.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

> [!NOTE]
> **_Your Answer_**
>
> The command is what triggers the action, because the operator sends it. The state decides whether it is legal, because each state object has its own list of allowed commands. The command asks and the state answers. Commands must not bypass the guards, because then the actuator could end in an impossible situation, like running while it is in maintenance, and the saved state would not match what really happened.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

> [!NOTE]
> **_Your Answer_**
>
> The UI can be old or wrong. Two people can have the page open, and the state can change after the page was loaded. Somebody can also call the API directly with curl or Scalar and never use the buttons. So the backend is the only place that can really protect the rule, and the disabled buttons are only a help for the user. If a command calls the raw adapter, it skips the state guard, so illegal commands are carried out. It also skips the decorators, so the max run time is not checked and nothing is written to the execution log. The actuator would then do things that the system has no record of.
