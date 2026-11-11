"""Berger Container Terminal demo.

The simulation itself lives in the ``bct`` package. This file only collects a
scenario, runs it, and explains the result.
"""

from __future__ import annotations

from dataclasses import fields

import plotly.graph_objects as go
import streamlit as st

from bct.config import DEFAULT_TERMINAL, ONE_OF_EACH, SCENARIOS, SimulationConfig
from bct.results import (
    SimulationResults,
    event_table,
    resource_table,
    ship_table,
    throughput_series,
)
from bct.simulation import run_simulation

ABOUT = "About / Explore"
RUN = "Run Simulation"

TEAL = "#0F6E6E"
AMBER = "#C47B2B"
NAVY = "#1F4E79"


def main() -> None:
    st.set_page_config(
        page_title="Berger Container Terminal",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_styles()
    page = st.sidebar.radio("Navigation", [ABOUT, RUN])
    st.sidebar.caption("Simulated time is in minutes.")
    if page == ABOUT:
        render_about()
    else:
        render_run()


def render_about() -> None:
    st.title("Berger Container Terminal")
    st.markdown(
        "A simplified dynamic simulation of how containers flow through a "
        "container terminal. BCT is a fictional terminal, built as a learning "
        "demo rather than a model of a real site."
    )
    st.markdown(
        "> **Given a terminal with X berths, Y quay cranes, Z trucks and "
        "W yard cranes, how does the flow of containers perform over time?**"
    )
    st.markdown(
        "The deeper problem underneath that question is how **limited resources "
        "interact under variable demand over time**. V1 keeps the demand pattern "
        "fixed so the interactions are easy to follow. Later versions can add "
        "randomness."
    )

    st.subheader("The flow")
    st.markdown(
        """
A ship arrives and asks for a berth. If every berth is taken, the ship waits.
Once the ship has a berth, each container is handled separately. They all need
the same cranes and trucks, so they wait when those machines are already in use.

1. A **quay crane** lifts the container (one container at a time).
2. The container asks for a **terminal truck** while that crane is still held.
3. If no truck is free, the container waits and the **crane stays occupied**.
4. When a truck is assigned, the crane is released and can start another lift.
5. The truck drives to the yard and waits with the container for a **yard crane**.
6. The yard crane places the container. The truck is then free again.

The ship leaves only when every one of its containers has been stored. The berth
is held for that whole time.
        """
    )
    st.info(
        "A shortage of trucks is allowed to travel upstream. Cranes that are "
        "waiting for a truck are not lifting, so the terminal's effective crane "
        "capacity falls even though those cranes are still marked busy."
    )

    entities, resources = st.columns(2)
    with entities:
        st.subheader("Entities")
        st.markdown(
            """
The things moving through the system.

- **Ships** arrive on a fixed interval, take a berth, and leave when their containers are stored.
- **Containers** are individual jobs. They queue for equipment instead of being processed as one lump per ship.
            """
        )
    with resources:
        st.subheader("Resources")
        st.markdown(
            """
The limited capacity entities have to share.

- **Berths** — where a ship can work
- **Quay cranes** — lift a container off the ship
- **Terminal trucks** — carry it to the yard
- **Yard cranes** — place it into storage
            """
        )

    st.subheader("Queues")
    st.markdown(
        """
Nothing in the model inserts a queue by hand. A queue appears when an entity
asks for a resource that is already fully used.

```text
Ship        →  waiting for a berth
Container   →  waiting for a quay crane
Container   →  waiting for a truck, while its quay crane stays held
Container   →  waiting for a yard crane, while its truck stays held
```
        """
    )

    st.subheader("State")
    st.markdown(
        """
The terminal has a state at every moment of simulated time: who is waiting,
who is working, and which equipment is free. The picture below is an
illustration of that idea, not a live reading from a run.

```text
Current time: 10:35

Ships waiting: 1
Ships at berth: 2

Quay cranes:  3 busy / 1 available
Trucks:       18 busy / 2 available

Containers waiting for trucks: 12
```

A simulation step is then just: look at what is true now, and jump to the next
moment when something changes.
        """
    )
    st.markdown(
        "> **Simulation = what happens now + what happens next.**"
    )

    st.subheader("SimPy")
    st.markdown(
        """
The model is built with **SimPy**, a Python library for **discrete-event
simulation**.

Instead of stepping through every minute, the clock jumps from one meaningful
event to the next. Between those events, nothing about the decision changes,
so there is nothing to simulate.

```text
Ship arrives
    ↓
Berth becomes available
    ↓
Container lift begins
    ↓
Truck becomes available
    ↓
Container reaches the yard
```

Each ship and each container is a small process that asks for a resource,
holds it for a fixed time, and gives it back. When a request cannot be
satisfied, that process pauses. SimPy wakes it up when a matching resource is
released. The queues, and the way a truck shortage blocks a crane, fall out of
those pauses.
        """
    )

    st.subheader("What V1 deliberately leaves out")
    st.markdown(
        """
The point of this version is a coherent resource lifecycle you can read, not
a realistic terminal.

- One direction only: import containers moving from ship to yard. Nothing is loaded back out.
- Equipment is a shared pool. A quay crane is not assigned to a particular berth, and trucks have no road network.
- The yard has unlimited space. There is no dwell time and no slot to run out of.
- Service times are fixed. The same lift always takes the same number of minutes.
- A truck becomes free at the yard. It does not drive back empty before it can take another container.
- The app runs the whole horizon and then shows what happened. Stepping one event at a time is a later enhancement.

Those choices are written down in `AGENTS.md` alongside the path toward
variability, repeated runs, and a richer operational model.
        """
    )


def render_run() -> None:
    config = _sidebar_config()
    st.title("Run simulation")
    st.markdown(
        "Set the terminal and the arrival pattern, then run the model through "
        "to the last ship. Ships that arrive before the horizon always finish, "
        "so the clock can run past the horizon."
    )
    st.caption(
        "Default terminal has spare equipment, so the first run often shows "
        "little waiting. Choose One of each to see a queue. With few trucks, "
        "quay-crane busy time rises: a crane is held until a truck takes the "
        "container."
    )

    with st.container(horizontal=True, gap="small"):
        run_clicked = st.button("▶ Run simulation", type="primary")
        st.button(
            "Reset",
            help="Clear the results and restore the default scenario.",
            on_click=_reset_run,
        )
    if run_clicked:
        with st.spinner("Running the simulation to completion..."):
            st.session_state["results"] = run_simulation(config)

    results = st.session_state.get("results")
    if not isinstance(results, SimulationResults):
        st.info("Choose a scenario in the sidebar, then run the simulation.")
        return

    if results.config != config:
        st.warning(
            "The sidebar has changed since this run. These figures are from "
            "the last completed simulation."
        )
    _render_results(results)


_SCENARIO = "scenario"
_EVENT_TYPE = "event_type"
_CONTAINER = "container"
_SCENARIO_NOTES = {
    DEFAULT_TERMINAL: "A loose fleet. The first run often shows little waiting.",
    ONE_OF_EACH: (
        "One machine of each kind. The truck holds the quay crane, and the "
        "second ship waits for the berth."
    ),
}


def _apply_selected_scenario() -> None:
    """Copy the chosen scenario into the sidebar fields before those widgets are built."""
    config = SCENARIOS[st.session_state[_SCENARIO]]
    for field in fields(SimulationConfig):
        st.session_state[field.name] = getattr(config, field.name)


def _reset_run() -> None:
    """Restore the sidebar and clear results, as on the first visit to this page."""
    st.session_state[_SCENARIO] = DEFAULT_TERMINAL
    _apply_selected_scenario()
    st.session_state.pop("results", None)
    st.session_state.pop(_EVENT_TYPE, None)
    st.session_state.pop(_CONTAINER, None)


def _sidebar_config() -> SimulationConfig:
    if _SCENARIO not in st.session_state:
        st.session_state[_SCENARIO] = DEFAULT_TERMINAL
        _apply_selected_scenario()

    st.sidebar.radio(
        "Scenario",
        list(SCENARIOS),
        key=_SCENARIO,
        on_change=_apply_selected_scenario,
    )
    st.sidebar.caption(_SCENARIO_NOTES[st.session_state[_SCENARIO]])

    st.sidebar.header("Terminal")
    n_berths = int(st.sidebar.number_input("Berths", min_value=1, max_value=20, step=1, key="n_berths"))
    n_quay_cranes = int(
        st.sidebar.number_input("Quay cranes", min_value=1, max_value=40, step=1, key="n_quay_cranes")
    )
    n_trucks = int(
        st.sidebar.number_input(
            "Terminal trucks", min_value=1, max_value=200, step=1, key="n_trucks"
        )
    )
    n_yard_cranes = int(
        st.sidebar.number_input(
            "Yard cranes", min_value=1, max_value=40, step=1, key="n_yard_cranes"
        )
    )

    st.sidebar.header("Demand")
    containers_per_vessel = int(
        st.sidebar.number_input(
            "Containers per vessel", min_value=1, max_value=100, step=1, key="containers_per_vessel"
        )
    )
    ship_arrival_interval = float(
        st.sidebar.number_input(
            "Ship arrival interval (min)",
            min_value=1.0,
            max_value=1440.0,
            step=5.0,
            key="ship_arrival_interval",
        )
    )
    simulation_duration = float(
        st.sidebar.number_input(
            "Arrival horizon (min)",
            min_value=1.0,
            max_value=10080.0,
            step=30.0,
            key="simulation_duration",
            help="Ships arrive while the clock is below this time. Work already started is allowed to finish.",
        )
    )

    with st.sidebar.expander("Operation times (minutes)"):
        st.caption("Fixed for this version. Every container of a kind takes the same time.")
        quay_crane_time = float(
            st.number_input(
                "Quay crane lift", min_value=0.0, max_value=240.0, step=0.5, key="quay_crane_time"
            )
        )
        truck_travel_time = float(
            st.number_input(
                "Truck travel to the yard",
                min_value=0.0,
                max_value=240.0,
                step=0.5,
                key="truck_travel_time",
            )
        )
        yard_crane_time = float(
            st.number_input(
                "Yard crane placement",
                min_value=0.0,
                max_value=240.0,
                step=0.5,
                key="yard_crane_time",
            )
        )

    return SimulationConfig(
        n_berths=n_berths,
        n_quay_cranes=n_quay_cranes,
        n_trucks=n_trucks,
        n_yard_cranes=n_yard_cranes,
        containers_per_vessel=containers_per_vessel,
        ship_arrival_interval=ship_arrival_interval,
        simulation_duration=simulation_duration,
        quay_crane_time=quay_crane_time,
        truck_travel_time=truck_travel_time,
        yard_crane_time=yard_crane_time,
    )


def _render_results(results: SimulationResults) -> None:
    config = results.config
    kpis = results.kpis
    st.subheader("Results")
    st.markdown(_horizon_note(results))

    one, two, three, four = st.columns(4)
    one.metric("Ships processed", kpis.ships_processed)
    two.metric("Containers processed", kpis.containers_processed)
    three.metric(
        "Avg vessel wait",
        f"{kpis.average_vessel_wait:.1f} min",
        help="Average time from ship arrival until a berth is assigned.",
    )
    four.metric(
        "Avg vessel turnaround",
        f"{kpis.average_vessel_turnaround:.1f} min",
        help="Average time from ship arrival until the ship departs.",
    )
    five, six, seven, eight = st.columns(4)
    five.metric(
        "Avg container flow",
        f"{kpis.average_container_flow_time:.1f} min",
        help="Average time from the ship being berthed until the container is stored. Ship waiting for a berth is not included.",
    )
    six.metric("Makespan", f"{results.makespan:.0f} min", help="Clock time when the last ship departs.")
    seven.metric("Ships in scenario", len(results.ships))
    eight.metric(
        "Containers per ship",
        config.containers_per_vessel,
    )

    st.info(kpis.interpretation)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(_utilisation_chart(results))
    with right:
        st.plotly_chart(_wait_chart(results))

    st.plotly_chart(_throughput_chart(results))
    st.caption(
        "Utilisation is busy time divided by capacity over the makespan. "
        "Quay-crane busy time includes minutes spent waiting for a truck after "
        "the lift. Truck busy time includes the drive to the yard and the "
        "yard-crane handoff. Average wait is the mean delay per request, "
        "including requests that did not wait."
    )

    st.markdown("**Resources**")
    st.dataframe(
        resource_table(results),
        hide_index=True,
        column_config={
            "Utilisation": st.column_config.NumberColumn(format="percent"),
            "Average wait (min)": st.column_config.NumberColumn(format="%.2f"),
            "Busy time (min)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    st.markdown("**Ships**")
    st.dataframe(
        ship_table(results),
        hide_index=True,
        column_config=_minute_columns(
            "Arrival (min)",
            "Berthed (min)",
            "Departed (min)",
            "Wait (min)",
            "Turnaround (min)",
        ),
    )

    st.markdown("**Event log**")
    st.caption("Waiting events are recorded only when a request actually waited.")
    events = event_table(results)
    if events.empty:
        st.write("No events were recorded.")
        return
    event_col, container_col = st.columns(2)
    with event_col:
        choice = _select("Event type", ["All events", *list(events["Event"].unique())], _EVENT_TYPE)
    with container_col:
        container_ids = [container.container_id for container in results.containers]
        container_choice = _select("Container", ["All containers", *container_ids], _CONTAINER)
    visible = events
    if choice != "All events":
        visible = visible[visible["Event"] == choice]
    if container_choice != "All containers":
        visible = visible[visible["Entity"] == container_choice]
    st.dataframe(
        visible,
        hide_index=True,
        height=380,
        column_config={"Time (min)": st.column_config.NumberColumn(format="%.1f")},
    )


def _select(label: str, options: list[str], key: str) -> str:
    """Select among options, dropping a stored choice that this run no longer has."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    return str(st.selectbox(label, options, key=key))


def _horizon_note(results: SimulationResults) -> str:
    horizon = results.config.simulation_duration
    makespan = results.makespan
    ships = len(results.ships)
    containers = results.kpis.containers_processed
    base = (
        f"{ships} ships and {containers} containers. "
        f"Arrivals were accepted before {horizon:.0f} min."
    )
    if makespan > horizon + 1e-6:
        return (
            base + f" The last ship departed at {makespan:.0f} min, after that "
            "horizon, because work already under way was allowed to finish."
        )
    if makespan + 1e-6 < horizon:
        return (
            base + f" The last ship departed at {makespan:.0f} min. Utilisation "
            "uses that makespan, so idle time after the last departure is not "
            "counted against the equipment."
        )
    return base + f" The last ship departed at {makespan:.0f} min."


def _utilisation_chart(results: SimulationResults) -> go.Figure:
    stats = list(results.kpis.resources.values())
    values = [item.utilisation * 100 for item in stats]
    figure = go.Figure(
        go.Bar(
            x=[item.label for item in stats],
            y=values,
            marker_color=TEAL,
            text=[f"{value:.0f}%" for value in values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    figure.update_layout(
        title=dict(text="Resource utilisation", x=0, font=dict(size=16)),
        template="plotly_white",
        yaxis_title="Utilisation (%)",
        yaxis=dict(range=[0, 118]),
        height=400,
        margin=dict(l=8, r=8, t=48, b=8),
    )
    return figure


def _wait_chart(results: SimulationResults) -> go.Figure:
    stats = list(results.kpis.resources.values())
    values = [item.average_wait for item in stats]
    figure = go.Figure(
        go.Bar(
            x=[item.label for item in stats],
            y=values,
            marker_color=AMBER,
            text=[f"{value:.1f}" for value in values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    peak = max(values) if values else 0
    figure.update_layout(
        title=dict(text="Average wait per request", x=0, font=dict(size=16)),
        template="plotly_white",
        yaxis_title="Minutes",
        yaxis=dict(range=[0, max(peak * 1.25, 1)]),
        height=400,
        margin=dict(l=8, r=8, t=48, b=8),
    )
    return figure


def _throughput_chart(results: SimulationResults) -> go.Figure:
    series = throughput_series(results)
    figure = go.Figure(
        go.Scatter(
            x=series["Time (min)"],
            y=series["Containers stored"],
            mode="lines",
            line=dict(color=NAVY, width=2, shape="vh"),
        )
    )
    figure.update_layout(
        title=dict(text="Containers stored over time", x=0, font=dict(size=16)),
        template="plotly_white",
        xaxis_title="Simulated time (min)",
        yaxis_title="Containers stored",
        height=380,
        margin=dict(l=8, r=8, t=48, b=8),
    )
    return figure


def _minute_columns(*names: str) -> dict[str, st.column_config.NumberColumn]:
    return {name: st.column_config.NumberColumn(format="%.1f") for name in names}


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container { padding-top: 1.3rem; max-width: 1180px; }
            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #d3e2e4;
                border-radius: 12px;
                padding: 0.65rem 0.8rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


main()
