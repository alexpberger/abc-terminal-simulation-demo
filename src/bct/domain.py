"""Records produced by a simulation run.

Processes fill these in as simulated time advances. They are plain data:
no SimPy objects live here, so metrics and the UI can use them after the run.
"""

from dataclasses import dataclass, field


class EventType:
    """Names of the transitions written to the event log."""

    SHIP_ARRIVED = "SHIP_ARRIVED"
    SHIP_WAITING_FOR_BERTH = "SHIP_WAITING_FOR_BERTH"
    SHIP_BERTH_ASSIGNED = "SHIP_BERTH_ASSIGNED"
    SHIP_DEPARTED = "SHIP_DEPARTED"
    CONTAINER_WAITING_FOR_QUAY_CRANE = "CONTAINER_WAITING_FOR_QUAY_CRANE"
    CONTAINER_QUAY_OPERATION_STARTED = "CONTAINER_QUAY_OPERATION_STARTED"
    CONTAINER_QUAY_OPERATION_COMPLETED = "CONTAINER_QUAY_OPERATION_COMPLETED"
    CONTAINER_WAITING_FOR_TRUCK = "CONTAINER_WAITING_FOR_TRUCK"
    TRUCK_ASSIGNED = "TRUCK_ASSIGNED"
    TRUCK_DEPARTED_TO_YARD = "TRUCK_DEPARTED_TO_YARD"
    CONTAINER_WAITING_FOR_YARD_CRANE = "CONTAINER_WAITING_FOR_YARD_CRANE"
    CONTAINER_YARD_OPERATION_STARTED = "CONTAINER_YARD_OPERATION_STARTED"
    CONTAINER_STORED = "CONTAINER_STORED"


RESOURCE_LABELS: dict[str, str] = {
    "berths": "Berths",
    "quay_cranes": "Quay cranes",
    "trucks": "Terminal trucks",
    "yard_cranes": "Yard cranes",
}

# Short names used in the "potential bottleneck" sentence.
BOTTLENECK_NAMES: dict[str, str] = {
    "berths": "berths",
    "quay_cranes": "quay cranes",
    "trucks": "terminal trucks",
    "yard_cranes": "yard cranes",
}

RESOURCE_ORDER: tuple[str, ...] = (
    "berths",
    "quay_cranes",
    "trucks",
    "yard_cranes",
)


@dataclass
class ShipRecord:
    ship_id: str
    name: str
    arrival_time: float
    berth_assigned_time: float | None = None
    depart_time: float | None = None
    container_ids: list[str] = field(default_factory=list)

    @property
    def waiting_time(self) -> float | None:
        """Minutes from arrival until a berth is assigned."""
        if self.berth_assigned_time is None:
            return None
        return self.berth_assigned_time - self.arrival_time

    @property
    def turnaround_time(self) -> float | None:
        """Minutes from arrival until the ship departs."""
        if self.depart_time is None:
            return None
        return self.depart_time - self.arrival_time


@dataclass
class ContainerRecord:
    """One container moving from a berthed ship into the yard.

    Quay-crane hold is ``quay_start`` to ``crane_released_time``. That span
    includes the lift and any wait for a truck afterwards. The truck hold is
    ``truck_assigned_time`` to ``truck_released_time``, which includes travel
    and the yard-crane handoff.
    """

    container_id: str
    ship_id: str
    ready_time: float
    quay_wait_start: float | None = None
    quay_start: float | None = None
    quay_end: float | None = None
    truck_wait_start: float | None = None
    truck_assigned_time: float | None = None
    crane_released_time: float | None = None
    departed_to_yard_time: float | None = None
    arrived_yard_time: float | None = None
    yard_wait_start: float | None = None
    yard_start: float | None = None
    stored_time: float | None = None
    truck_released_time: float | None = None

    @property
    def flow_time(self) -> float | None:
        """Minutes from becoming ready at the berth until stored."""
        if self.stored_time is None:
            return None
        return self.stored_time - self.ready_time

    @property
    def quay_wait(self) -> float | None:
        if self.quay_start is None or self.quay_wait_start is None:
            return None
        return self.quay_start - self.quay_wait_start

    @property
    def truck_wait(self) -> float | None:
        if self.truck_assigned_time is None or self.truck_wait_start is None:
            return None
        return self.truck_assigned_time - self.truck_wait_start

    @property
    def yard_wait(self) -> float | None:
        if self.yard_start is None or self.yard_wait_start is None:
            return None
        return self.yard_start - self.yard_wait_start

    @property
    def quay_hold(self) -> float | None:
        if self.crane_released_time is None or self.quay_start is None:
            return None
        return self.crane_released_time - self.quay_start

    @property
    def truck_hold(self) -> float | None:
        if self.truck_released_time is None or self.truck_assigned_time is None:
            return None
        return self.truck_released_time - self.truck_assigned_time


@dataclass(frozen=True)
class SimEvent:
    time: float
    event_type: str
    entity_id: str
    message: str
