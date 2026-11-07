"""Ship arrivals and the container flow through the terminal.

Container lifecycle, kept coherent on purpose:

1. The container acquires a quay crane and is lifted.
2. It then requests a truck while that quay crane is still held.
3. If no truck is free, the container waits and the crane stays occupied.
4. Once a truck is assigned, the quay crane is released.
5. The truck stays occupied through the trip to the yard and the yard-crane
   handoff, and is released when the container is stored.

A shortage of trucks can therefore propagate upstream and reduce the number
of quay cranes that are actually moving containers.
"""

from collections.abc import Iterator

import simpy

from bct.config import SimulationConfig
from bct.domain import ContainerRecord, EventType, ShipRecord
from bct.terminal import Terminal


def arrival_process(
    terminal: Terminal, config: SimulationConfig
) -> Iterator[simpy.Event]:
    """Arrive a ship at t=0 and then every fixed interval, while t < horizon."""
    env = terminal.env
    next_arrival = 0.0
    index = 0
    while next_arrival < config.simulation_duration:
        if next_arrival > env.now:
            yield env.timeout(next_arrival - env.now)
        ship = terminal.create_ship(index, arrived_at=env.now)
        env.process(ship_process(terminal, config, ship))
        index += 1
        next_arrival += config.ship_arrival_interval


def ship_process(
    terminal: Terminal, config: SimulationConfig, ship: ShipRecord
) -> Iterator[simpy.Event]:
    """Take a berth, unload every container, then depart and free the berth."""
    env = terminal.env
    terminal.log(EventType.SHIP_ARRIVED, ship.name, f"{ship.name} arrived")

    berth = terminal.berths.claim()
    if berth.will_wait:
        terminal.log(
            EventType.SHIP_WAITING_FOR_BERTH,
            ship.name,
            f"{ship.name} waiting for a berth",
        )
    yield berth.request
    berth.acquired()

    ship.berth_assigned_time = env.now
    terminal.log(EventType.SHIP_BERTH_ASSIGNED, ship.name, f"{ship.name} berthed")

    container_runs: list[simpy.Process] = []
    for _ in range(config.containers_per_vessel):
        container = terminal.create_container(ship, ready_time=env.now)
        container_runs.append(
            env.process(container_process(terminal, config, ship, container))
        )
    yield simpy.AllOf(env, container_runs)

    ship.depart_time = env.now
    terminal.log(EventType.SHIP_DEPARTED, ship.name, f"{ship.name} departed")
    berth.release()


def container_process(
    terminal: Terminal,
    config: SimulationConfig,
    ship: ShipRecord,
    container: ContainerRecord,
) -> Iterator[simpy.Event]:
    """Move one container from the quay into the yard."""
    if container.ship_id != ship.ship_id:
        raise RuntimeError(f"{container.container_id} does not belong to {ship.name}")
    env = terminal.env
    container_id = container.container_id

    crane = terminal.quay_cranes.claim()
    container.quay_wait_start = env.now
    if crane.will_wait:
        terminal.log(
            EventType.CONTAINER_WAITING_FOR_QUAY_CRANE,
            container_id,
            f"{container_id} waiting for a quay crane",
        )
    yield crane.request
    crane.acquired()

    container.quay_start = env.now
    terminal.log(
        EventType.CONTAINER_QUAY_OPERATION_STARTED,
        container_id,
        f"{container_id} quay crane operation started",
    )
    yield env.timeout(config.quay_crane_time)
    container.quay_end = env.now
    terminal.log(
        EventType.CONTAINER_QUAY_OPERATION_COMPLETED,
        container_id,
        f"{container_id} quay crane operation completed",
    )

    # The crane is still held. Time spent here is quay-crane busy time.
    truck = terminal.trucks.claim()
    container.truck_wait_start = env.now
    if truck.will_wait:
        terminal.log(
            EventType.CONTAINER_WAITING_FOR_TRUCK,
            container_id,
            f"{container_id} waiting for a terminal truck",
        )
    yield truck.request
    truck.acquired()
    container.truck_assigned_time = env.now
    terminal.log(EventType.TRUCK_ASSIGNED, container_id, f"{container_id} truck assigned")

    container.crane_released_time = env.now
    crane.release()

    container.departed_to_yard_time = env.now
    terminal.log(
        EventType.TRUCK_DEPARTED_TO_YARD,
        container_id,
        f"{container_id} departed for the yard",
    )
    yield env.timeout(config.truck_travel_time)
    container.arrived_yard_time = env.now

    yard = terminal.yard_cranes.claim()
    container.yard_wait_start = env.now
    if yard.will_wait:
        terminal.log(
            EventType.CONTAINER_WAITING_FOR_YARD_CRANE,
            container_id,
            f"{container_id} waiting for a yard crane",
        )
    yield yard.request
    yard.acquired()

    container.yard_start = env.now
    terminal.log(
        EventType.CONTAINER_YARD_OPERATION_STARTED,
        container_id,
        f"{container_id} yard crane operation started",
    )
    yield env.timeout(config.yard_crane_time)

    container.stored_time = env.now
    terminal.log(
        EventType.CONTAINER_STORED,
        container_id,
        f"{container_id} stored in the yard",
    )
    yard.release()

    container.truck_released_time = env.now
    truck.release()
