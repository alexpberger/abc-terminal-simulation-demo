"""Scenario configuration for one Berger Container Terminal run."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Inputs for one deterministic simulation run.

    Time values are minutes. Service times stay plain fields so a later
    version can replace them with random draws without rewriting the processes.
    """

    n_berths: int = 2
    n_quay_cranes: int = 4
    n_trucks: int = 20
    n_yard_cranes: int = 4
    containers_per_vessel: int = 12
    ship_arrival_interval: float = 60.0
    simulation_duration: float = 240.0
    quay_crane_time: float = 3.0
    truck_travel_time: float = 6.0
    yard_crane_time: float = 2.0

    def __post_init__(self) -> None:
        _require_positive_int("n_berths", self.n_berths)
        _require_positive_int("n_quay_cranes", self.n_quay_cranes)
        _require_positive_int("n_trucks", self.n_trucks)
        _require_positive_int("n_yard_cranes", self.n_yard_cranes)
        _require_positive_int("containers_per_vessel", self.containers_per_vessel)
        if self.ship_arrival_interval <= 0:
            raise ValueError("ship_arrival_interval must be greater than 0 minutes")
        if self.simulation_duration < 0:
            raise ValueError("simulation_duration cannot be negative")
        for name in ("quay_crane_time", "truck_travel_time", "yard_crane_time"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an integer of at least 1")


DEFAULT_TERMINAL = "Default terminal"
ONE_OF_EACH = "One of each"

SCENARIOS: dict[str, SimulationConfig] = {
    DEFAULT_TERMINAL: SimulationConfig(),
    ONE_OF_EACH: SimulationConfig(
        n_berths=1,
        n_quay_cranes=1,
        n_trucks=1,
        n_yard_cranes=1,
        containers_per_vessel=10,
        ship_arrival_interval=60.0,
        simulation_duration=120.0,
        quay_crane_time=3.0,
        truck_travel_time=3.0,
        yard_crane_time=3.0,
    ),
}
