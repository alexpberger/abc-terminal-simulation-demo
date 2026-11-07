"""Assembled output of one simulation run, shared by the CLI and the UI."""

from dataclasses import dataclass

import pandas as pd

from bct.config import SimulationConfig
from bct.domain import ContainerRecord, ShipRecord, SimEvent
from bct.metrics import Kpis


@dataclass
class SimulationResults:
    config: SimulationConfig
    makespan: float
    ships: list[ShipRecord]
    containers: list[ContainerRecord]
    events: list[SimEvent]
    kpis: Kpis


def ship_table(results: SimulationResults) -> pd.DataFrame:
    rows = [
        {
            "Ship": ship.name,
            "Arrival (min)": ship.arrival_time,
            "Berthed (min)": ship.berth_assigned_time,
            "Departed (min)": ship.depart_time,
            "Wait (min)": ship.waiting_time,
            "Turnaround (min)": ship.turnaround_time,
            "Containers": len(ship.container_ids),
        }
        for ship in results.ships
    ]
    return pd.DataFrame(rows)


def resource_table(results: SimulationResults) -> pd.DataFrame:
    rows = [
        {
            "Resource": stats.label,
            "Capacity": stats.capacity,
            "Utilisation": stats.utilisation,
            "Average wait (min)": stats.average_wait,
            "Max queue": stats.max_queue,
            "Busy time (min)": stats.busy_time,
        }
        for stats in results.kpis.resources.values()
    ]
    return pd.DataFrame(rows)


def event_table(results: SimulationResults) -> pd.DataFrame:
    rows = [
        {
            "Time (min)": event.time,
            "Event": event.event_type,
            "Entity": event.entity_id,
            "Detail": event.message,
        }
        for event in results.events
    ]
    return pd.DataFrame(rows)


def throughput_series(results: SimulationResults) -> pd.DataFrame:
    """Cumulative containers stored, as a step that jumps at each completion."""
    stored_times = sorted(
        container.stored_time
        for container in results.containers
        if container.stored_time is not None
    )
    times = [0.0]
    counts = [0]
    for index, stored_at in enumerate(stored_times, start=1):
        times.append(stored_at)
        counts.append(index)
    if results.makespan > times[-1]:
        times.append(results.makespan)
        counts.append(counts[-1])
    return pd.DataFrame({"Time (min)": times, "Containers stored": counts})


def format_summary(results: SimulationResults) -> str:
    kpis = results.kpis
    lines = [
        "Berger Container Terminal",
        f"Arrival horizon: {results.config.simulation_duration:.1f} min",
        f"Makespan: {results.makespan:.1f} min",
        f"Ships processed: {kpis.ships_processed}",
        f"Containers processed: {kpis.containers_processed}",
        f"Average vessel wait: {kpis.average_vessel_wait:.1f} min",
        f"Average vessel turnaround: {kpis.average_vessel_turnaround:.1f} min",
        f"Average container flow time: {kpis.average_container_flow_time:.1f} min",
        "",
        "Resource utilisation",
    ]
    for stats in kpis.resources.values():
        lines.append(
            f"- {stats.label}: {stats.utilisation:.0%} utilised, "
            f"busy {stats.busy_time:.1f} min, "
            f"average wait {stats.average_wait:.1f} min, "
            f"max queue {stats.max_queue}"
        )
    lines.extend(["", kpis.interpretation])
    return "\n".join(lines)
