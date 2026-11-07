"""Run the terminal simulation from the command line.

Example::

    python -m bct --trucks 2 --containers 8
"""

import argparse

from bct.config import SimulationConfig
from bct.results import format_summary
from bct.simulation import run_simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Berger Container Terminal simulation"
    )
    parser.add_argument("--berths", type=int, default=2)
    parser.add_argument("--quay-cranes", type=int, default=4)
    parser.add_argument("--trucks", type=int, default=20)
    parser.add_argument("--yard-cranes", type=int, default=4)
    parser.add_argument("--containers", type=int, default=12)
    parser.add_argument("--interval", type=float, default=60.0, help="Minutes between ships")
    parser.add_argument(
        "--duration",
        type=float,
        default=240.0,
        help="Arrival horizon in minutes. Ships already working finish after this.",
    )
    parser.add_argument("--quay-time", type=float, default=3.0)
    parser.add_argument("--travel-time", type=float, default=6.0)
    parser.add_argument("--yard-time", type=float, default=2.0)
    return parser


def config_from_args(args: argparse.Namespace) -> SimulationConfig:
    return SimulationConfig(
        n_berths=args.berths,
        n_quay_cranes=args.quay_cranes,
        n_trucks=args.trucks,
        n_yard_cranes=args.yard_cranes,
        containers_per_vessel=args.containers,
        ship_arrival_interval=args.interval,
        simulation_duration=args.duration,
        quay_crane_time=args.quay_time,
        truck_travel_time=args.travel_time,
        yard_crane_time=args.yard_time,
    )


def main() -> None:
    args = build_parser().parse_args()
    print(format_summary(run_simulation(config_from_args(args))))


if __name__ == "__main__":
    main()
