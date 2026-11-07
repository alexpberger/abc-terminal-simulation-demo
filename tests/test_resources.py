"""Resource capacity and the queues that appear when capacity is short."""

import pytest

from bct.config import SimulationConfig
from bct.domain import EventType
from bct.simulation import run_simulation

from support import tiny_config


def test_config_rejects_zero_capacity() -> None:
    with pytest.raises(ValueError, match="n_trucks"):
        SimulationConfig(n_trucks=0)


def test_in_use_never_exceeds_capacity() -> None:
    results = run_simulation(
        tiny_config(
            n_berths=2,
            n_quay_cranes=2,
            n_trucks=3,
            n_yard_cranes=2,
            containers_per_vessel=8,
            ship_arrival_interval=10,
            simulation_duration=40,
        )
    )
    assert results.kpis.containers_processed == 4 * 8
    for stats in results.kpis.resources.values():
        assert stats.peak_in_use <= stats.capacity
        assert 0.0 <= stats.utilisation <= 1.0


def test_ship_waits_when_the_only_berth_is_taken() -> None:
    # One container takes 3 + 6 + 2 = 11 minutes. The second ship arrives at
    # t=5, so it waits until the first ship releases the berth at t=11.
    results = run_simulation(
        tiny_config(ship_arrival_interval=5, simulation_duration=10)
    )
    first, second = results.ships

    assert first.arrival_time == pytest.approx(0)
    assert first.waiting_time == pytest.approx(0)
    assert first.depart_time == pytest.approx(11)

    assert second.arrival_time == pytest.approx(5)
    assert second.berth_assigned_time == pytest.approx(first.depart_time)
    assert second.waiting_time == pytest.approx(6)
    assert second.depart_time == pytest.approx(22)

    waiting = [
        event
        for event in results.events
        if event.event_type == EventType.SHIP_WAITING_FOR_BERTH
    ]
    assert len(waiting) == 1
    assert waiting[0].entity_id == second.name
    assert waiting[0].time == pytest.approx(5)
    assert results.kpis.resources["berths"].max_queue == 1
    assert results.kpis.resources["berths"].peak_in_use == 1


def test_second_container_waits_one_lift_when_a_truck_is_free() -> None:
    results = run_simulation(tiny_config(n_trucks=2, containers_per_vessel=2))
    first, second = results.containers

    assert first.quay_wait == pytest.approx(0)
    assert second.quay_wait == pytest.approx(3)
    assert first.truck_wait == pytest.approx(0)
    assert second.truck_wait == pytest.approx(0)
    assert results.kpis.resources["quay_cranes"].busy_time == pytest.approx(6)
    assert results.kpis.resources["quay_cranes"].max_queue == 1
    assert results.kpis.resources["quay_cranes"].peak_in_use == 1
