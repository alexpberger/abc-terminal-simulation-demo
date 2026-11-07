# Berger Container Terminal

A discrete-event simulation of a fictional container terminal. Ships and containers compete for a small set of shared resources — berths, quay cranes, terminal trucks, and yard cranes — and queues appear when those resources are busy.

The core question:

> **Given a terminal with X berths, Y quay cranes, Z trucks and W yard cranes, how does the flow of containers perform over time?**

Underneath that is a more general question: how limited resources interact under variable demand over time. This first version keeps demand deterministic so the interactions are easy to inspect.

## Technology

- Python 3.11 or newer
- [SimPy](https://simpy.readthedocs.io/) for the discrete-event simulation
- [Streamlit](https://streamlit.io/) for the demo interface
- pandas and Plotly for the result tables and charts

## Prerequisites

Python 3.11 or newer. Check with:

```bash
python --version
```

On some systems the command is `python3`.

## Setup

Open this project directory (or clone it, then open that directory). Create a virtual environment in the project so the demo does not depend on globally installed packages.

```bash
python -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Install the project and its dependencies, including the test runner:

```bash
python -m pip install -e ".[dev]"
```

## Run locally

From the project root, with the virtual environment active:

```bash
streamlit run app/streamlit_app.py
```

The app opens in a browser. **About / Explore** explains the model. **Run Simulation** accepts a scenario and runs it to completion.

To run the same engine without the interface:

```bash
python -m bct
```

Pass `--trucks`, `--quay-cranes`, `--containers`, and the other flags listed by `python -m bct --help` to try a different scenario.

## Run tests

From the project root, with the virtual environment active:

```bash
pytest
```

## Architecture

The simulation engine and the interface are separate.

- `src/bct/` is the model: configuration, SimPy processes, resource tracking, metrics, and `run_simulation()`.
- `app/streamlit_app.py` collects inputs, calls `run_simulation()`, and displays the returned records.
- `python -m bct` calls the same function and prints a text summary.

Nothing in the engine imports Streamlit. A run with the same configuration is repeatable.

## Modelling assumptions

V1 is a learning model of an import move (ship to yard), not a model of a real terminal.

- Containers are individual SimPy processes. When a ship is berthed, its containers compete for one shared pool of equipment. Cranes are not assigned to a berth, and trucks have no road network.
- A container holds its quay crane for the lift **and** for any wait for a truck afterwards. The crane is released only once a truck is assigned. A truck shortage therefore reduces how many cranes are actually lifting. Quay-crane busy time includes that wait, not just the lift.
- The truck stays occupied for the drive to the yard and the yard-crane handoff. It is released when the container is stored. There is no empty drive back to the quay.
- The ship holds its berth until every container is stored, then departs.
- The yard has unlimited space. Nothing is loaded back onto the ship. Service times are fixed.
- Ships arrive at a fixed interval from time 0 up to, but not including, the arrival horizon. Ships already in the system finish even if that runs past the horizon. Utilisation divides busy time by capacity times that completion time (the makespan), so trailing idle time after the last departure is not treated as part of the working window.

## Roadmap

- **V1 — this demo.** Deterministic discrete-event simulation, one container per process, shared resources, natural queues, a full run, KPIs, and an event log.
- **Simulation Explorer (later).** Step the real SimPy environment one event at a time and inspect the state. Not part of V1, and not a replay of a saved log.
- **V2 — variability.** Random arrivals and service times, with a seed so a run can be repeated.
- **V3 — Monte Carlo.** Many replications of a scenario, then means, medians, percentiles, and comparisons such as a baseline against extra trucks or an extra yard crane.
- **V4 — operational simulation.** Richer geography, yard capacity, and eventually a start from a current terminal state. That only becomes a digital twin if it is actually fed by live data.

`AGENTS.md` describes these stages in more detail for anyone changing the code.
