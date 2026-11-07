"""KPIs against timelines that can be checked by hand."""

import pytest

from bct.config import SimulationConfig
from bct.results import format_summary
from bct.simulation import run_simulation

from support import tiny_config


def test_single_container_kpis() -> None:
    # Berth and the whole flow: 11 minutes.
    # Quay held for the lift only: 3. Truck held for travel + yard: 8. Yard: 2.
    results = run_simulation(tiny_config())
    kpis = results.kpis
    makespan = 11

    assert results.makespan == pytest.approx(makespan)
    assert kpis.ships_processed == 1
    assert kpis.containers_processed == 1
    assert kpis.average_vessel_wait == pytest.approx(0)
    assert kpis.average_vessel_turnaround == pytest.approx(makespan)
    assert kpis.average_container_flow_time == pytest.approx(makespan)

    assert kpis.resources["berths"].busy_time == pytest.approx(makespan)
    assert kpis.resources["berths"].utilisation == pytest.approx(1)
    assert kpis.resources["quay_cranes"].busy_time == pytest.approx(3)
    assert kpis.resources["quay_cranes"].utilisation == pytest.approx(3 / makespan)
    assert kpis.resources["trucks"].busy_time == pytest.approx(8)
    assert kpis.resources["trucks"].utilisation == pytest.approx(8 / makespan)
    assert kpis.resources["yard_cranes"].busy_time == pytest.approx(2)
    assert kpis.resources["yard_cranes"].utilisation == pytest.approx(2 / makespan)

    for stats in kpis.resources.values():
        assert stats.average_wait == pytest.approx(0)
        assert stats.max_queue == 0

    assert "No resource showed meaningful waiting" in kpis.interpretation


def test_truck_shortage_kpis_count_crane_blockage_as_busy() -> None:
    results = run_simulation(tiny_config(containers_per_vessel=2))
    kpis = results.kpis
    makespan = 19

    assert results.makespan == pytest.approx(makespan)
    assert kpis.containers_processed == 2
    assert kpis.average_container_flow_time == pytest.approx((11 + 19) / 2)
    assert kpis.average_vessel_turnaround == pytest.approx(makespan)
    assert kpis.average_vessel_wait == pytest.approx(0)

    quay = kpis.resources["quay_cranes"]
    trucks = kpis.resources["trucks"]
    assert quay.average_wait == pytest.approx(1.5)  # waits of 0 and 3
    assert trucks.average_wait == pytest.approx(2.5)  # waits of 0 and 5
    assert quay.utilisation == pytest.approx(11 / makespan)
    assert trucks.utilisation == pytest.approx(16 / makespan)
    assert "Potential bottleneck: terminal trucks" in kpis.interpretation
    assert "quay crane stays occupied" in kpis.interpretation

    summary = format_summary(results)
    assert "Ships processed: 1" in summary
    assert "Containers processed: 2" in summary
    assert "Potential bottleneck: terminal trucks" in summary


def test_two_ships_share_one_berth_in_the_vessel_averages() -> None:
    results = run_simulation(
        tiny_config(ship_arrival_interval=5, simulation_duration=10)
    )
    kpis = results.kpis
    # Waits are 0 and 6. Turnarounds are 11 and 17 (5 + 6 wait + 11 working).
    assert kpis.ships_processed == 2
    assert kpis.average_vessel_wait == pytest.approx(3)
    assert kpis.average_vessel_turnaround == pytest.approx((11 + 17) / 2)
    assert kpis.resources["berths"].utilisation == pytest.approx(1)
    assert "Potential bottleneck: berths" in kpis.interpretation


def test_same_config_is_repeatable() -> None:
    config = SimulationConfig()
    first = run_simulation(config)
    second = run_simulation(config)
    assert [(event.time, event.event_type, event.entity_id) for event in first.events] == [
        (event.time, event.event_type, event.entity_id) for event in second.events
    ]
    assert first.kpis.containers_processed == second.kpis.containers_processed == 48


def test_zero_horizon_processes_nothing() -> None:
    results = run_simulation(tiny_config(simulation_duration=0))
    assert results.ships == []
    assert results.kpis.ships_processed == 0
    assert results.kpis.containers_processed == 0
    assert results.makespan == pytest.approx(0)
    assert "No ships arrived" in results.kpis.interpretation
