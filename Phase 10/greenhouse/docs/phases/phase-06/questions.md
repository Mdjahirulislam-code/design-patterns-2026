# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

> [!NOTE]
> ***Your Answer***
>
> Strategy puts each way of solving the same problem in its own class, so the algorithm can be changed without changing the code that uses it. The context holds one strategy and only calls its `decide` method with the data it needs. It does not know which strategy it has. Choosing and running must stay separate because then a new algorithm only needs a new class and one registry entry. The code that runs the algorithm stays the same, and each strategy can be tested alone.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

> [!NOTE]
> ***Your Answer***
>
> The strategy is the common interface, in this lab `AutomationStrategy` with `decide`. The concrete strategies are `ConservativeMoistureStrategy` and `AggressiveMoistureStrategy`. The context is `AutomationService`, which gets the strategy and gives it a `LocationAutomationContext`. The client is the API and the dashboard panel, which choose the strategy key. With `if/elif` everything is in one place, so every new policy means editing and retesting that place. The method grows bigger, the policies are mixed with HTTP or database code, and it is easy to break one policy when changing another.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

> [!NOTE]
> ***Your Answer***
>
> Use Strategy when there are several algorithms for the same job and someone chooses between them, like the irrigation policy of a location. Skip it when there is only one algorithm, because the extra interface only adds code. Also skip it when the change comes from the object moving through a lifecycle, for example idle, running and fault. That is State, because the object changes itself and nobody picks a policy.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

> [!NOTE]
> ***Your Answer***
>
> It returns a `Recommendation` with an action, `irrigate` or `wait`, a reason in plain text and an optional score. Conservative only irrigates when moisture is below the zone low threshold. Aggressive irrigates when moisture is below the zone high threshold. For example with a zone band of 0.25 to 0.45 and moisture 0.35, conservative returns wait with "Moisture 0.35 is within 0.25–0.45". Aggressive returns irrigate because 0.35 is still below 0.45, so it tops up early.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Latest moisture may already be in `sensor_readings` from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

> [!NOTE]
> ***Your Answer***
>
> The low and high values come from the `zones` table. The moisture is the newest row in `sensor_readings` from the moisture sensors whose `zone_id` is that zone. A zone without a sensor gets no value and the strategy returns wait. This phase does not add a scheduler or a broker because Phase 5 already fills `sensor_readings`, and this phase only reads the latest row. Adding another pipeline would mix two jobs and duplicate work. Strategies get a plain object so they do not depend on the database or the web framework. Then they are easy to test with a fake context and they cannot change data by accident. Thresholds come from zones because each zone has its own band and an operator can change it. If the numbers were hardcoded, every zone would get the same rule and a change would need new code.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

> [!NOTE]
> ***Your Answer***
>
> The saved key is the real setting of the location. If evaluate used a key from the request, two people or two screens could get different answers for the same location, and later phases like the overview would not know which strategy is active. Saving it also keeps the choice after a refresh or restart. After the operator saves a new strategy, the next evaluate uses the new key. With the same moisture the result can change. For example 0.35 in a 0.25 to 0.45 zone changes from wait to irrigate when the key changes from conservative to aggressive.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

> [!NOTE]
> ***Your Answer***
>
> Deciding and doing are different jobs. If the strategy started the pump, we could not show a recommendation without watering, could not test the strategy without hardware, and every strategy would need to know about actuators. Keeping it separate means we can show the result first, add checks, and change how commands are sent without touching the strategies. The action is meant to be carried out later by the actuator command flow in Phases 9 and 10. It goes through the `ActuatorPort` from Phase 5, and Phase 9 wraps that port with the Decorator pattern.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

> [!NOTE]
> ***Your Answer***
>
> In Strategy the client chooses the active object, in this lab the operator saves conservative or aggressive. The variation is a policy, which means a different way to make the same decision. In State the object usually changes its own state when something happens, for example a pump going from idle to running to fault. The variation is a lifecycle, and the allowed actions depend on where the object is in that lifecycle.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

> [!NOTE]
> ***Your Answer***
>
> Adapter translates a foreign API. In Phase 5 the vendor payload and the MQTT dict are turned into our `Reading`. Builder assembles a valid aggregate. In Phase 4 the location and its zones are built step by step and checked in `build()`. Strategy swaps an algorithm. In Phase 6 the irrigation decision can be conservative or aggressive behind the same `decide` method.

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> The mega-strategy only moves the `if/elif` into another file. The policies are still mixed, a new policy still means editing that class, and the interface does nothing useful. Each policy should be its own class. The strategy that waters directly mixes deciding with doing. It starts the pump during an evaluate, it cannot be tested without hardware, and there is no place to check or log the command first. A strategy should only return a recommendation, and the action should be sent later through the actuator side.
