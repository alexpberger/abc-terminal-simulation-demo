"""Resource holds follow the quay -> truck -> yard lifecycle."""

import pytest

from bct.domain import EventType
from bct.simulation import run_simulation

from support import tiny_config


def test_single_container_timeline_when_nothing_queues() -> None:
    results = run_simulation(tiny_config())
    container = results.containers[0]
    ship = results.ships[0]

    assert container.container_id == "BCT-C001"
    assert ship.name == "BCT Aurora"
    assert container.quay_start == pytest.approx(0)
    assert container.quay_end == pytest.approx(3)
    assert container.truck_assigned_time == pytest.approx(3)
    assert container.crane_released_time == pytest.approx(3)
    assert container.departed_to_yard_time == pytest.approx(3)
    assert container.arrived_yard_time == pytest.approx(9)
    assert container.yard_start == pytest.approx(9)
    assert container.stored_time == pytest.approx(11)
    assert container.truck_released_time == pytest.approx(11)
    assert ship.depart_time == pytest.approx(11)
    assert results.makespan == pytest.approx(11)

    # Truck free at the end of the lift, so the crane is busy for the lift only.
    assert container.quay_hold == pytest.approx(3)
    assert container.truck_hold == pytest.approx(8)

    waiting_types = {
        EventType.SHIP_WAITING_FOR_BERTH,
        EventType.CONTAINER_WAITING_FOR_QUAY_CRANE,
        EventType.CONTAINER_WAITING_FOR_TRUCK,
        EventType.CONTAINER_WAITING_FOR_YARD_CRANE,
    }
    assert not any(event.event_type in waiting_types for event in results.events)


def test_quay_crane_busy_time_includes_wait_for_truck() -> None:
    """One crane and one truck, two containers on one ship.

    The first container holds the crane for the lift only (3), because the
    truck is free, then holds that truck for travel + yard (8), releasing it
    at t=11.

    The second container waits out the first lift, so it gets the crane at
    t=3. It lifts until t=6 and then holds the crane until the truck is free
    at t=11. That hold is 8 minutes: 3 of lift and 5 of waiting for the truck.

    Quay-crane busy time is 3 + 8 = 11, not the 6 minutes of lifting alone.
    """
    results = run_simulation(tiny_config(containers_per_vessel=2))
    first, second = results.containers
    quay = results.kpis.resources["quay_cranes"]
    trucks = results.kpis.resources["trucks"]

    assert first.quay_start == pytest.approx(0)
    assert first.quay_end == pytest.approx(3)
    assert first.crane_released_time == pytest.approx(3)
    assert first.truck_wait == pytest.approx(0)
    assert first.stored_time == pytest.approx(11)

    assert second.quay_wait == pytest.approx(3)
    assert second.quay_start == pytest.approx(3)
    assert second.quay_end == pytest.approx(6)
    assert second.truck_assigned_time == pytest.approx(11)
    assert second.crane_released_time == pytest.approx(second.truck_assigned_time)
    assert second.truck_wait == pytest.approx(5)
    assert second.quay_hold == pytest.approx(8)
    assert second.stored_time == pytest.approx(19)

    assert quay.busy_time == pytest.approx(11)
    assert quay.busy_time == pytest.approx(sum(c.quay_hold for c in results.containers))
    assert trucks.busy_time == pytest.approx(16)
    assert trucks.busy_time == pytest.approx(sum(c.truck_hold for c in results.containers))
    assert first.truck_hold == pytest.approx(8)
    assert second.truck_hold == pytest.approx(8)

    truck_waits = [
        event
        for event in results.events
        if event.event_type == EventType.CONTAINER_WAITING_FOR_TRUCK
    ]
    assert len(truck_waits) == 1
    assert truck_waits[0].entity_id == second.container_id
    assert truck_waits[0].time == pytest.approx(6)


def test_truck_stays_busy_through_travel_and_yard_handoff() -> None:
    results = run_simulation(tiny_config())
    container = results.containers[0]
    trucks = results.kpis.resources["trucks"]
    yard = results.kpis.resources["yard_cranes"]

    assert container.truck_hold == pytest.approx(6 + 2)
    assert trucks.busy_time == pytest.approx(container.truck_hold)
    # Yard busy time is the placement itself, not the truck's travel.
    assert yard.busy_time == pytest.approx(2)
    assert container.truck_released_time == pytest.approx(container.stored_time)


def test_event_log_contains_the_main_transitions() -> None:
    results = run_simulation(tiny_config())
    types = [event.event_type for event in results.events]
    for expected in (
        EventType.SHIP_ARRIVED,
        EventType.SHIP_BERTH_ASSIGNED,
        EventType.CONTAINER_QUAY_OPERATION_STARTED,
        EventType.CONTAINER_QUAY_OPERATION_COMPLETED,
        EventType.TRUCK_ASSIGNED,
        EventType.TRUCK_DEPARTED_TO_YARD,
        EventType.CONTAINER_YARD_OPERATION_STARTED,
        EventType.CONTAINER_STORED,
        EventType.SHIP_DEPARTED,
    ):
        assert expected in types

    stored = next(
        event for event in results.events if event.event_type == EventType.CONTAINER_STORED
    )
    departed = next(
        event for event in results.events if event.event_type == EventType.SHIP_DEPARTED
    )
    assert stored.time == pytest.approx(11)
    assert departed.time == pytest.approx(11)
    assert stored.time <= departed.time
