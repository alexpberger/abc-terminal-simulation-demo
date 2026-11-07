# Build: Berger Container Terminal (BCT) — V1 Discrete-Event Simulation Demo

## Context and overall ambition

Build a polished but deliberately understandable learning/demo application called:

**Berger Container Terminal (BCT)**

The application should simulate the flow of containers through a simplified container terminal using **Python and SimPy**.

This is a **demo-first while learning** project.

The goal is to build something that:

1. Is genuinely functional and demonstrates discrete-event simulation.
2. Is easy to understand and inspect as a learning project.
3. Has a simple but polished Streamlit UI.
4. Does not over-engineer V1.
5. Has a clean architecture that can evolve into more sophisticated future versions.

The central question the simulation should answer is:

> **"Given a terminal with X berths, Y quay cranes, Z trucks and W yard cranes, how does the flow of containers perform over time?"**

The deeper problem being modelled is:

> **"How limited resources interact under variable demand over time."**

---

# V1 scope

Build a simplified **dynamic discrete-event simulation** of container flow through Berger Container Terminal.

The basic flow is:

```text
SHIP ARRIVES
    ↓
REQUESTS BERTH
    ↓
WAITS IF NECESSARY
    ↓
BERTH ASSIGNED
    ↓
CONTAINERS ARE PROCESSED
    ↓
QUAY CRANE
    ↓
TERMINAL TRUCK
    ↓
YARD CRANE
    ↓
CONTAINER STORED IN YARD
```

The system should explicitly model:

## Entities

- Ships / vessels
- Containers

## Resources

- Berths
- Quay cranes
- Terminal trucks
- Yard cranes

## Queues

Queues should emerge naturally when demand exceeds currently available resources.

Examples include:

- Ships waiting for berths
- Containers waiting for quay cranes
- Containers waiting for trucks
- Containers waiting for yard cranes

## States

The simulation should make it possible to understand that the system state evolves over simulated time.

Examples of state include:

- Current simulation time
- Ships waiting
- Ships at berth
- Containers being processed
- Containers waiting
- Available vs busy resources
- Containers completed / stored

The application should help demonstrate the fundamental idea:

> **Simulation = "What happens now + what happens next".**

---

# Technology

Use:

- Python
- SimPy for discrete-event simulation
- Streamlit for the UI
- pandas where useful for metrics and results
- plotly for charts if useful

Use modern Python project conventions and type hints.

Keep dependencies minimal.

Use a clean and conventional Python project setup with explicit dependency management.

---

# Python environment

Create and use a **separate project-local Python virtual environment**.

The environment should not rely on globally installed packages.

Use a standard `.venv` directory in the project root.

The README must include clear setup instructions covering:

1. Creating the virtual environment.
2. Activating it on macOS/Linux.
3. Activating it on Windows.
4. Installing project dependencies.
5. Running the Streamlit application.
6. Running tests.

For example:

```bash
python -m venv .venv
```

Then activation:

### macOS/Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Choose a simple, conventional dependency-management approach and ensure the README instructions exactly match the implementation.

The `.venv` directory should be included in `.gitignore`.

---

# Important modelling philosophy

Do not attempt to model a real container terminal in full detail.

This is a simplified educational/demo simulation.

However, the simulation should represent genuine interactions between scarce resources.

For example:

- A limited number of berths means ships may queue.
- A limited number of quay cranes means containers compete for crane capacity.
- A limited number of trucks means downstream transport can become constrained.
- A limited number of yard cranes can create downstream congestion.

The model should allow queues and bottlenecks to emerge from the interaction of resources rather than manually hard-coding bottlenecks.

The V1 model should prioritise:

> **Clarity and coherent resource lifecycles over maximum realism.**

---

# Explicit V1 modelling decisions

The following decisions are intentional and should be implemented unless there is a strong technical reason not to.

## 1. Individual container processes

For V1, model containers as **individual SimPy processes**.

When a ship is berthed, its containers should enter the simulated operational flow as individual entities and compete for shared terminal resources.

Conceptually:

```text
Ship arrives
    ↓
Ship acquires berth
    ↓
Ship's containers enter operational flow

Container A ─┐
Container B ─┼──→ compete for shared resources
Container C ─┤
Container D ─┘
```

This is deliberately chosen because it makes the resource interactions, queues and discrete-event behaviour easy to understand.

Do not introduce unnecessary complexity such as sophisticated crane assignment logic or detailed equipment dispatching in V1.

---

## 2. Coherent resource lifecycle

Resource lifecycles should be understandable and reasonably coherent.

A useful simplified model is:

```text
Container requests quay crane
        ↓
Quay crane operation
        ↓
Container acquires terminal truck
        ↓
Container leaves quay
        ↓
Quay crane released
        ↓
Truck travels to yard
        ↓
Container requests yard crane
        ↓
Yard crane operation
        ↓
Container stored
        ↓
Truck becomes available again
```

The truck should remain occupied during its relevant transport and handoff lifecycle.

Do not immediately release resources in a way that produces obviously nonsensical operational behaviour.

However, do not over-model physical details such as:

- Individual road networks
- Exact yard positions
- Detailed crane dispatching

The goal is a simplified but logically coherent operational flow.

---

# Simulation design

## Simulation environment

Use a SimPy environment.

Use a clear simulated time unit, preferably **minutes**.

The application should clearly communicate simulated time to the user.

---

## Ships

Ships should:

1. Arrive at the terminal.
2. Request a berth.
3. Wait if no berth is available.
4. Once berthed, initiate processing of their containers.
5. Depart when all relevant containers have been processed for V1.

Use a manageable default number of containers per ship so the simulation runs quickly.

Use fictional BCT naming consistently.

For example:

- BCT Aurora
- BCT Pacific
- BCT Horizon

Containers can use IDs such as:

```text
BCT-C001
BCT-C002
BCT-C003
```

The application should feel like one coherent fictional terminal demo.

---

## Containers

Containers should move through the simplified process:

```text
WAIT / READY
    ↓
QUAY CRANE OPERATION
    ↓
TERMINAL TRUCK TRANSPORT
    ↓
YARD CRANE OPERATION
    ↓
STORED / COMPLETED
```

Containers should compete for shared resources.

Track timestamps and waiting times where practical.

---

## Resources

Use SimPy resources to represent:

- Berths
- Quay cranes
- Terminal trucks
- Yard cranes

Resource capacities should be configurable.

The default scenario could use something like:

```text
Berths:       2
Quay cranes:  4
Trucks:       20
Yard cranes:  4
```

These values should be easy to change later.

---

# Deterministic V1

For V1, keep the base simulation primarily deterministic and understandable.

For example:

```text
Ship arrival interval: fixed
Quay crane operation time: fixed
Truck travel time: fixed
Yard crane operation time: fixed
```

The architecture should make it straightforward for future versions to introduce stochastic/random behaviour.

Do not build Monte Carlo functionality yet.

V1 should be reproducible and easy to debug.

Given the same configuration, the simulation should produce understandable and repeatable behaviour.

---

# Simulation metrics / KPIs

After running the full simulation, show useful KPIs.

At minimum:

## Terminal throughput

- Ships processed
- Containers processed

## Vessel performance

- Average vessel waiting time
- Average vessel turnaround time

## Container performance

Where feasible:

- Average container flow time
- Waiting time by stage/resource

## Resource utilisation

For:

- Berths
- Quay cranes
- Trucks
- Yard cranes

Do not fake utilisation metrics.

Implement actual tracking of resource busy time, or otherwise calculate utilisation in a technically sound and understandable way.

## Queue / congestion metrics

Where feasible:

- Maximum queue sizes
- Average waiting times

The UI should help identify potential bottlenecks, but avoid pretending that a simplistic heuristic is definitive.

It is fine to highlight something like:

> **Potential bottleneck: terminal trucks**

when supported by utilisation and waiting-time metrics.

---

# Simulation observability and event logging

Build basic observability into the simulation from the beginning.

The system should make it possible to inspect:

- Current simulation time
- Important events
- Resource usage
- Queue/waiting behaviour

Create a simple event logging mechanism.

Examples:

```text
SHIP_ARRIVED
SHIP_WAITING_FOR_BERTH
SHIP_BERTH_ASSIGNED

CONTAINER_WAITING_FOR_QUAY_CRANE
CONTAINER_QUAY_OPERATION_STARTED
CONTAINER_QUAY_OPERATION_COMPLETED

CONTAINER_WAITING_FOR_TRUCK
TRUCK_ASSIGNED
TRUCK_DEPARTED_TO_YARD

CONTAINER_WAITING_FOR_YARD_CRANE
CONTAINER_STORED
```

Do not necessarily implement every one of these as a rigid enterprise event architecture.

The purpose is simply to make the simulation behaviour inspectable and understandable.

The event log can also support debugging and future development.

---

# Streamlit application

Build a simple, polished Streamlit application.

The application should focus on:

1. Explaining the simulation.
2. Allowing the user to configure a scenario.
3. Running the full simulation.
4. Presenting results clearly.

Suggested structure:

```text
Sidebar
    ├── Navigation
    └── Simulation parameters

Main area
    ├── About / explanation
    ├── Simulation controls
    └── Results / KPIs
```

The app should have at least two main modes/pages:

1. **About / Explore**
2. **Run Simulation**

This can be implemented using Streamlit navigation, tabs or another simple UX pattern.

Keep it clean, visually understandable and intentionally educational.

---

# ABOUT / EXPLORE PAGE

This page is educational.

Explain clearly what the application does.

Suggested opening:

## Berger Container Terminal (BCT)

A simplified dynamic simulation of how containers flow through a container terminal.

Include the key question:

> **"Given a terminal with X berths, Y quay cranes, Z trucks and W yard cranes, how does the flow of containers perform over time?"**

Explain that the underlying problem is:

> **"How limited resources interact under variable demand over time."**

Explain the key components.

## Entities

The things moving through the simulated system.

- Ships
- Containers

## Resources

The limited operational capacity that entities must compete for.

- Berths
- Quay cranes
- Terminal trucks
- Yard cranes

## Queues

Queues emerge when entities require resources that are currently busy.

For example:

```text
Ship → waiting for berth
Container → waiting for truck
Container → waiting for yard crane
```

## State

Explain that the simulated terminal has a state at every point in simulated time.

For example:

```text
Current time: 10:35

Ships waiting: 1
Ships at berth: 2

Quay cranes:
3 busy / 1 available

Trucks:
18 busy / 2 available

Containers waiting for trucks:
12
```

Explain the key mental model:

> **Simulation = "What happens now + what happens next".**

Then explain SimPy.

## SimPy

The simulation is built using the Python library **SimPy**, which is used for **discrete-event simulation**.

Explain discrete-event simulation in plain language:

> Instead of simulating every single second, the model moves from one important event to the next.

Examples:

```text
Ship arrives
↓
Berth becomes available
↓
Container unloading begins
↓
Truck becomes available
↓
Container reaches the yard
```

Keep the explanation accessible and not overly academic.

---

# RUN FULL SIMULATION

The application should have a clear button such as:

## ▶ Run Simulation

When clicked:

1. Create/reset the simulation.
2. Run the simulation to completion for the configured simulation horizon.
3. Store results.
4. Display KPIs and charts.

The user should be able to configure at least:

- Number of berths
- Number of quay cranes
- Number of terminal trucks
- Number of yard cranes
- Number of containers per vessel
- Ship arrival interval
- Simulation duration

Use sensible defaults.

The results page should show:

- KPI cards
- Resource utilisation
- Relevant charts/tables
- A concise interpretation of results
- A view of the event log, where useful

Potential charts include:

- Resource utilisation comparison
- Queue/waiting-time comparison
- Throughput over simulated time

Do not overcomplicate the visualisation in V1.

---

# Important architecture requirement

Keep the simulation logic separate from the Streamlit UI.

A suggested structure is:

```text
abc-terminal-simulation-demo/
│
├── README.md
├── AGENTS.md
├── pyproject.toml
├── .gitignore
│
├── docs/
│   └── bct-v1-implementation-prompt.md
│
├── src/
│   └── bct/
│       ├── __init__.py
│       ├── config.py
│       ├── domain.py
│       ├── terminal.py
│       ├── processes.py
│       ├── metrics.py
│       ├── simulation.py
│       └── results.py
│
├── app/
│   └── streamlit_app.py
│
└── tests/
```

This structure is a suggestion rather than a rigid requirement.

Use a similarly clean architecture if a better simple structure is appropriate.

The important separation is:

```text
SIMULATION DOMAIN / ENGINE
            ≠
STREAMLIT UI
```

The simulation should be executable independently from the UI.

A simple CLI/script-based run should ideally be possible for development and testing.

---

# AGENTS.md

Create an `AGENTS.md` file explaining:

1. The purpose of the project.
2. The V1 architecture and modelling philosophy.
3. Important design principles.
4. The intended roadmap.

The roadmap should explicitly describe the following future ambitions.

---

## V1 — Deterministic dynamic simulation

The current implementation.

Key characteristics:

- Dynamic
- Discrete-event
- Primarily deterministic
- Individual container processes
- Shared limited resources
- Natural queues
- Full simulation runs
- KPI and utilisation analysis
- Basic event logging

---

## Future enhancement — Simulation Explorer

A future enhancement should make it possible to interactively inspect the simulation as it evolves.

The intended capability is:

> Advance the actual SimPy environment event by event and inspect the resulting state.

Potential controls:

- Next Event
- Run Next N Events
- Run Until Time
- Reset

The user should be able to inspect:

- Current simulation time
- Latest event
- Resource utilisation/state
- Queues
- Ships and containers in the system

Important:

> This should eventually advance the actual SimPy simulation environment, rather than simply replaying a precomputed event log.

This is deliberately **out of scope for the initial V1 implementation**.

---

## V2 — Variability

Introduce stochastic behaviour.

Potential additions:

- Random ship arrival patterns
- Variable container processing times
- Variable truck travel times
- Operational variability

Use appropriate random distributions and reproducible random seeds.

The goal is to move from:

```text
DYNAMIC + DETERMINISTIC
```

towards:

```text
DYNAMIC + STOCHASTIC
```

---

## V3 — Monte Carlo and scenario analysis

Add repeated simulation runs.

For example:

```text
Scenario A
20 trucks
100 simulation replications

Scenario B
30 trucks
100 simulation replications
```

Analyse:

- Mean outcomes
- Median outcomes
- Percentiles
- Distributions
- Probability of undesirable outcomes

Make it possible to compare scenarios.

For example:

```text
Baseline
vs
+5 trucks
vs
+1 yard crane
```

The purpose is to move from:

> "What happened in this one simulation?"

towards:

> "What range of outcomes should we expect under uncertainty?"

---

## V4 — Interactive / operational simulation

Move towards a more sophisticated application.

Potential capabilities:

- Interactive scenario configuration
- Richer visualisation
- More realistic terminal topology
- Yard capacity and container dwell time
- More detailed resource interactions
- Potentially real or current operational data

A possible longer-term concept is:

```text
CURRENT TERMINAL STATE
        ↓
INITIALISE SIMULATION
        ↓
SIMULATE NEXT X HOURS
        ↓
EXPLORE LIKELY OUTCOMES
```

This begins moving conceptually towards an operational simulation or digital-twin-style application.

Do not call V4 a real digital twin unless the necessary data integration and real-world synchronisation actually exist.

---

# Engineering principles

Follow these principles.

## 1. Prefer understandable over clever

This is a learning project.

The code should be readable.

Use clear names.

Avoid unnecessary abstraction.

---

## 2. Do not over-engineer V1

Do not build:

- Microservices
- Databases unless genuinely needed
- Message queues
- APIs unless needed
- Authentication
- Cloud infrastructure

This is a local Python/Streamlit simulation demo.

---

## 3. Do not paint us into a corner

Keep:

- Simulation logic separate from UI
- Configuration explicit
- Metrics separated from processes where practical
- Event logging/observability available
- Randomness easy to introduce later

---

## 4. Make the model honest

Document simplifications.

Do not present simplified assumptions as realistic terminal behaviour.

Clearly distinguish between:

- Modelled behaviour
- Simplified assumptions
- Future potential improvements

---

# Testing

Add a small but meaningful test suite.

Test important behaviour such as:

- Resource capacities are respected.
- Ships wait when no berth is available.
- Containers cannot exceed available resource capacity.
- Basic metrics are calculated correctly.
- Important resource lifecycles behave as expected.

Tests should be understandable and not excessive.

---

# README

Create a good README.

Include:

## What is this?

A concise explanation of Berger Container Terminal.

## The core question

> **"Given a terminal with X berths, Y quay cranes, Z trucks and W yard cranes, how does the flow of containers perform over time?"**

## Core concept

> **"How limited resources interact under variable demand over time."**

## Technology

- Python
- SimPy
- Streamlit

## Prerequisites

State the required Python version.

## Setup

Provide exact instructions for:

1. Opening or cloning the repository.
2. Creating the local `.venv`.
3. Activating the environment.
4. Installing dependencies.

Include instructions for both macOS/Linux and Windows where appropriate.

## Run locally

Provide the exact command to start the Streamlit application.

## Run tests

Provide the exact command for running tests.

## Architecture

Briefly explain the separation between the simulation engine and UI.

## Modelling assumptions

Clearly document the intentional simplifications in V1.

## Roadmap

Briefly explain V1–V4.

---

# Acceptance criteria

The implementation is successful when I can:

1. Set up a separate local `.venv` using the README instructions.
2. Install the project dependencies without relying on global Python packages.
3. Start the Streamlit application locally.
4. Read an understandable explanation of discrete-event simulation and the terminal model.
5. Configure the number of berths, cranes, trucks and yard cranes.
6. Run the complete simulation with one button.
7. See meaningful KPIs after the simulation.
8. See resource utilisation and queue/waiting behaviour.
9. Inspect a meaningful event log.
10. Read an AGENTS.md explaining how the project could evolve through future versions.
11. Read the simulation code and understand how the main entities, resources and processes interact.
12. Run a small but meaningful automated test suite.

---

# Final instruction

Before writing large amounts of code:

1. Inspect the existing repository.
2. Propose the final project structure.
3. Explain the important modelling decisions.
4. Create a clear implementation plan.
5. Then implement V1.

If there is ambiguity, prefer a simple, explicit modelling choice and document it rather than overcomplicating the implementation.

The goal is not a perfect container-terminal simulator.

The goal is a **real, inspectable, dynamic discrete-event simulation that is educational, visually understandable and a strong foundation for future versions.**

The primary goal of V1 is the simulation engine and a simple interface for configuring and running it.

**Interactive event-by-event stepping is explicitly out of scope for the initial V1 implementation and should remain a future enhancement.**