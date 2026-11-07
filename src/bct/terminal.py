"""Shared terminal resources and the log of one simulation run."""

from __future__ import annotations

import simpy

from bct.config import SimulationConfig
from bct.domain import ContainerRecord, ShipRecord, SimEvent

SHIP_NAMES: tuple[str, ...] = (
    "BCT Aurora",
    "BCT Pacific",
    "BCT Horizon",
    "BCT Meridian",
    "BCT Cascade",
    "BCT Solstice",
    "BCT Harbor",
    "BCT Northstar",
    "BCT Latitude",
    "BCT Drift",
)


class TrackedResource(simpy.Resource):
    """A SimPy resource that records queues and time in use.

    Busy time is the integral of how many units are held. It includes every
    minute a holder keeps the resource, including time spent blocked on
    something else. Quay-crane busy time therefore includes waiting for a
    truck after the lift, for as long as the container process keeps the crane.
    """

    def __init__(self, env: simpy.Environment, capacity: int, name: str) -> None:
        super().__init__(env, capacity=capacity)
        self.sim_env = env
        self.name = name
        self.busy_time = 0.0
        self.max_queue = 0
        self.wait_times: list[float] = []
        self.peak_in_use = 0
        self._in_use = 0
        self._last_change = 0.0

    def claim(self) -> ResourceClaim:
        return ResourceClaim(self)

    def observe_queue(self) -> None:
        self.max_queue = max(self.max_queue, len(self.queue))

    def mark_acquired(self, requested_at: float) -> float:
        self._touch()
        self._in_use += 1
        if self._in_use > self.capacity:
            raise RuntimeError(
                f"{self.name} has {self._in_use} units in use, "
                f"above capacity {self.capacity}"
            )
        self.peak_in_use = max(self.peak_in_use, self._in_use)
        wait = self.sim_env.now - requested_at
        self.wait_times.append(wait)
        return wait

    def mark_released(self, request: simpy.Event) -> None:
        if self._in_use < 1:
            raise RuntimeError(f"{self.name} was released while nothing was in use")
        self._touch()
        self._in_use -= 1
        super().release(request)

    def finalize(self) -> None:
        """Close the busy-time integral at the current simulation time."""
        self._touch()

    def _touch(self) -> None:
        now = self.sim_env.now
        elapsed = now - self._last_change
        self.busy_time += self._in_use * elapsed
        self._last_change = now


class ResourceClaim:
    """One attempt to take a tracked resource.

    Create the claim, ``yield claim.request``, call ``acquired``, do the work,
    then ``release``. Release is explicit so a process can hold one resource
    while it waits for another, and drop them at different moments.
    """

    def __init__(self, resource: TrackedResource) -> None:
        self.resource = resource
        # Decided before request(), and request() does not yield, so nothing
        # else can take the last free unit between the check and the queue.
        self.will_wait = resource.count >= resource.capacity
        self.requested_at = resource.sim_env.now
        self.request = resource.request()
        resource.observe_queue()
        self.wait: float | None = None

    def acquired(self) -> float:
        """Call immediately after ``yield claim.request`` returns."""
        self.wait = self.resource.mark_acquired(self.requested_at)
        return self.wait

    def release(self) -> None:
        self.resource.mark_released(self.request)


class Terminal:
    """Resources, entity records, and the event log for one run."""

    def __init__(self, env: simpy.Environment, config: SimulationConfig) -> None:
        self.env = env
        self.config = config
        self.berths = TrackedResource(env, config.n_berths, "berths")
        self.quay_cranes = TrackedResource(env, config.n_quay_cranes, "quay_cranes")
        self.trucks = TrackedResource(env, config.n_trucks, "trucks")
        self.yard_cranes = TrackedResource(env, config.n_yard_cranes, "yard_cranes")
        self.ships: list[ShipRecord] = []
        self.containers: list[ContainerRecord] = []
        self.events: list[SimEvent] = []
        self._container_seq = 0

    @property
    def resources(self) -> dict[str, TrackedResource]:
        return {
            "berths": self.berths,
            "quay_cranes": self.quay_cranes,
            "trucks": self.trucks,
            "yard_cranes": self.yard_cranes,
        }

    def create_ship(self, index: int, arrived_at: float) -> ShipRecord:
        base = SHIP_NAMES[index % len(SHIP_NAMES)]
        cycle = index // len(SHIP_NAMES)
        name = base if cycle == 0 else f"{base} {cycle + 1}"
        ship = ShipRecord(ship_id=f"ship-{index + 1}", name=name, arrival_time=arrived_at)
        self.ships.append(ship)
        return ship

    def create_container(self, ship: ShipRecord, ready_time: float) -> ContainerRecord:
        self._container_seq += 1
        container = ContainerRecord(
            container_id=f"BCT-C{self._container_seq:03d}",
            ship_id=ship.ship_id,
            ready_time=ready_time,
        )
        ship.container_ids.append(container.container_id)
        self.containers.append(container)
        return container

    def log(self, event_type: str, entity_id: str, message: str) -> None:
        self.events.append(
            SimEvent(
                time=self.env.now,
                event_type=event_type,
                entity_id=entity_id,
                message=message,
            )
        )

    def finalize(self) -> None:
        for resource in self.resources.values():
            resource.finalize()
