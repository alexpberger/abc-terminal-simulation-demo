"""KPI calculations from a finished simulation.

Utilisation is busy time divided by capacity times makespan. Makespan is the
simulated time until the last ship departs. Busy time counts the whole time a
resource is held, so a quay crane blocked on a truck is busy, not idle.
"""

from dataclasses import dataclass

from bct.domain import (
    BOTTLENECK_NAMES,
    RESOURCE_LABELS,
    RESOURCE_ORDER,
    ContainerRecord,
    ShipRecord,
)
from bct.terminal import TrackedResource


@dataclass(frozen=True)
class ResourceStats:
    key: str
    label: str
    capacity: int
    busy_time: float
    utilisation: float
    average_wait: float
    max_queue: int
    request_count: int
    peak_in_use: int


@dataclass(frozen=True)
class Kpis:
    ships_processed: int
    containers_processed: int
    average_vessel_wait: float
    average_vessel_turnaround: float
    average_container_flow_time: float
    resources: dict[str, ResourceStats]
    interpretation: str


def resource_stats(resource: TrackedResource, makespan: float) -> ResourceStats:
    if makespan > 0:
        utilisation = resource.busy_time / (resource.capacity * makespan)
    else:
        utilisation = 0.0
    average_wait = _mean(resource.wait_times)
    return ResourceStats(
        key=resource.name,
        label=RESOURCE_LABELS[resource.name],
        capacity=resource.capacity,
        busy_time=resource.busy_time,
        utilisation=utilisation,
        average_wait=average_wait,
        max_queue=resource.max_queue,
        request_count=len(resource.wait_times),
        peak_in_use=resource.peak_in_use,
    )


def build_kpis(
    ships: list[ShipRecord],
    containers: list[ContainerRecord],
    resources: dict[str, TrackedResource],
    makespan: float,
) -> Kpis:
    stats = {key: resource_stats(resources[key], makespan) for key in RESOURCE_ORDER}
    ships_processed = sum(1 for ship in ships if ship.depart_time is not None)
    containers_processed = sum(
        1 for container in containers if container.stored_time is not None
    )
    return Kpis(
        ships_processed=ships_processed,
        containers_processed=containers_processed,
        average_vessel_wait=_mean(
            [ship.waiting_time for ship in ships if ship.waiting_time is not None]
        ),
        average_vessel_turnaround=_mean(
            [ship.turnaround_time for ship in ships if ship.turnaround_time is not None]
        ),
        average_container_flow_time=_mean(
            [container.flow_time for container in containers if container.flow_time is not None]
        ),
        resources=stats,
        interpretation=interpret(stats, ships_processed),
    )


def interpret(resources: dict[str, ResourceStats], ships_processed: int) -> str:
    """Name a possible bottleneck only when waiting and utilisation support it."""
    if ships_processed == 0:
        return "No ships arrived during this horizon, so there is no flow to compare."

    waiting = [item for item in resources.values() if item.average_wait > 1e-9]
    if not waiting:
        busiest = max(resources.values(), key=lambda item: item.utilisation)
        sentence = (
            "No resource showed meaningful waiting in this run. "
            f"The busiest resource was {BOTTLENECK_NAMES[busiest.key]} "
            f"at {busiest.utilisation:.0%}."
        )
        if busiest.utilisation < 0.5:
            sentence += " Spare capacity remained over the makespan."
        return sentence

    bottleneck = max(waiting, key=lambda item: (item.average_wait, item.utilisation))
    sentence = (
        f"Potential bottleneck: {BOTTLENECK_NAMES[bottleneck.key]}. "
        f"Requests waited {bottleneck.average_wait:.1f} minutes on average "
        f"and utilisation was {bottleneck.utilisation:.0%}."
    )
    if bottleneck.key == "trucks":
        sentence += (
            " While a container waits for a truck its quay crane stays occupied,"
            " so a truck shortage also reduces effective crane capacity."
        )
    return sentence


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
