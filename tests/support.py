"""Small scenarios with hand-checkable timelines."""

from bct.config import SimulationConfig


def tiny_config(**overrides: object) -> SimulationConfig:
    """One of each resource, one container, and a single ship at t=0.

    Service times are quay 3, travel 6, yard 2. With a truck free immediately
    the container finishes at t=11 and the quay crane is busy only for the lift.
    """
    values: dict[str, object] = {
        "n_berths": 1,
        "n_quay_cranes": 1,
        "n_trucks": 1,
        "n_yard_cranes": 1,
        "containers_per_vessel": 1,
        "ship_arrival_interval": 60.0,
        "simulation_duration": 60.0,
        "quay_crane_time": 3.0,
        "truck_travel_time": 6.0,
        "yard_crane_time": 2.0,
    }
    values.update(overrides)
    return SimulationConfig(**values)  # type: ignore[arg-type]
