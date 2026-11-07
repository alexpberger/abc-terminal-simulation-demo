# AGENTS.md

Guidance for working on Berger Container Terminal (BCT), a learning demo of container flow through a fictional terminal.

## Purpose

BCT answers a small version of a real planning question:

> Given a terminal with X berths, Y quay cranes, Z trucks and W yard cranes, how does the flow of containers perform over time?

The underlying idea is how limited resources interact when demand varies over time. V1 keeps that demand deterministic so a reader can trace one container, one crane, and one truck and see why a queue appeared.

The project should stay understandable. Prefer a direct SimPy process over a framework. Do not add services, a database, an API, or authentication for the demo.

## V1 architecture

```text
src/bct/          simulation engine (no Streamlit imports)
app/streamlit_app.py
tests/
```

- `config.py` — one frozen `SimulationConfig`. Time unit is minutes. Service durations are ordinary fields so randomness can replace them later without rewriting the processes.
- `domain.py` — ship, container, and event records. No SimPy types.
- `terminal.py` — `TrackedResource` and the terminal that owns the four resources plus the event log.
- `processes.py` — ship arrival, ship berth cycle, and one process per container.
- `metrics.py` — KPIs from the finished records. This is where utilisation and the bottleneck sentence are computed.
- `simulation.py` — `run_simulation(config)`, the only entry the UI and the CLI need.
- `results.py` — tables and the text summary shared by `python -m bct` and Streamlit.

`run_simulation` schedules every ship with an arrival time strictly before the horizon, then lets those ships finish. Makespan is the clock when the last ship departs. It can be shorter or longer than the horizon. Utilisation is `busy_time / (capacity * makespan)`.

## Modelling philosophy

Clarity and a coherent resource lifecycle come before realism. Do not hard-code a bottleneck. Queues should appear because a SimPy resource is at capacity.

V1 models an import discharge only:

```text
Ship arrives
    → waits for a berth if needed
    → each container, individually:
        acquire quay crane
        lift
        request truck while the crane is still held
        release the quay crane only when the truck is assigned
        truck travels to the yard
        yard crane places the container
        release the truck
    → ship departs and releases the berth
```

This coupling is intentional. If no truck is free, the container waits and the quay crane remains occupied, so a truck shortage reduces effective crane capacity.

### Busy time must follow that lifecycle

`TrackedResource` integrates how many units are held, from acquire to release. It does not measure "service time" separately from "blocked while holding".

- Quay-crane busy time includes the lift **and** any minutes spent waiting for a truck afterwards.
- Truck busy time includes travel **and** the yard-crane handoff.
- Yard-crane busy time is the placement only. Waiting for a yard crane is queue time on the yard crane, during which the truck is still busy.
- Berth busy time is the whole time the ship is alongside.

Do not "correct" quay-crane utilisation down to pure lift time. Tests in `tests/test_lifecycles.py` lock the truck-wait case: with one crane, one truck, and two containers, quay busy time is the sum of the crane holds, which is longer than the two lifts.

### Simplifications to keep visible

Document these in the About page and the README if they change. Do not present them as realistic terminal practice.

- Shared equipment pools. No crane-to-berth assignment, no truck dispatch, no road network, no yard slots.
- Unlimited yard. No dwell, no load-out.
- Fixed service times. No distributions and no replications in V1.
- The truck is released at the yard. There is no empty return trip.
- Waiting events are written only when the wait is real. State-change events are always written.

Ship names cycle through a fixed fictional list (`BCT Aurora`, `BCT Pacific`, …). Container ids are `BCT-C001` onward.

## Design principles

1. **Prefer understandable over clever.** A reader should be able to follow `container_process` from the crane request to the truck release without a diagram beside them.
2. **Do not over-engineer V1.** No microservices, message bus, database, or authentication.
3. **Do not paint the model into a corner.** Keep the engine free of UI code, keep configuration explicit, keep metrics out of the processes, and keep an event log. When V2 adds randomness, it should be a change to how durations are drawn, not a new architecture.
4. **Keep the model honest.** If a metric is a simplified consequence of the rules above, say so in the UI caption. The bottleneck sentence is a hint from average wait (utilisation breaks ties), not a formal diagnosis. It may mention the crane-hold effect when trucks are the resource that waited.

## Testing

`pytest` from the project root, after `pip install -e ".[dev]"`.

Tests should stay small and hand-checkable:

- Capacity is respected (`peak_in_use` never exceeds capacity).
- A ship waits when the only berth is taken, and is not berthed before the previous ship departs.
- Quay-crane busy time includes post-lift waiting for a truck.
- Truck busy time covers travel and the yard handoff.
- A one-container scenario matches a timeline you can add up: lift 3 + travel 6 + yard 2.

If you change the lifecycle, update those expected numbers in the same change. Do not loosen a test to hide a shorter crane hold.

## Roadmap

### V1 — Deterministic dynamic simulation

The current implementation.

- Dynamic discrete-event simulation
- Primarily deterministic and repeatable
- One SimPy process per container
- Shared limited resources and queues that emerge from them
- Full runs, KPIs, utilisation, and a basic event log
- Streamlit for explanation, scenario inputs, and results

Interactive event-by-event stepping is **out of scope for V1**.

### Future enhancement — Simulation Explorer

Let a person advance the actual SimPy environment and inspect the state after each step.

Intended controls:

- Next event
- Run the next N events
- Run until a time
- Reset

The view should show the clock, the latest event, resource state, queues, and the ships and containers currently in the system.

This has to drive the live SimPy environment. Replaying a stored event log is not the goal, because a later version needs to be able to intervene. Build it on top of the existing processes and `TrackedResource`, not as a second model.

### V2 — Variability

Move from dynamic and deterministic to dynamic and stochastic.

- Random ship arrivals
- Variable crane and truck times
- A seed so a stochastic run can be repeated

Keep the same resource lifecycle. Replace fixed timeouts with draws from distributions stored on the config, rather than scattering `random` calls through the processes.

### V3 — Monte Carlo and scenario analysis

Repeat a scenario many times and compare scenarios.

Example: 20 trucks and 100 replications against 30 trucks and 100 replications, or a baseline against +5 trucks and against +1 yard crane.

Report means, medians, percentiles, distributions, and the chance of an undesirable outcome (for example, vessel wait above a threshold). The question moves from "what happened in this run?" to "what range of outcomes should we expect?"

Do not start V3 before V2 has a seeded stochastic run worth repeating.

### V4 — Interactive / operational simulation

A richer app: more of the terminal's geography, yard capacity, container dwell, more detailed equipment interactions, and a path toward starting from a current terminal state and simulating the next few hours.

Do not call V4 a digital twin unless real operational data is actually synchronised into the model. A scenario editor with a fictional terminal is still a simulation.
