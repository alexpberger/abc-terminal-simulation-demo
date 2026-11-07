"""Run one full Berger Container Terminal simulation."""

import simpy

from bct.config import SimulationConfig
from bct.metrics import build_kpis
from bct.processes import arrival_process
from bct.results import SimulationResults
from bct.terminal import Terminal


def run_simulation(config: SimulationConfig | None = None) -> SimulationResults:
    """Simulate every ship that arrives before the horizon, then let them finish.

    The run does not stop at the horizon if a berthed ship still has containers
    in progress. Makespan is the clock when the last of those ships departs.
    """
    config = config if config is not None else SimulationConfig()
    env = simpy.Environment()
    terminal = Terminal(env, config)
    env.process(arrival_process(terminal, config))
    env.run()
    terminal.finalize()
    makespan = float(env.now)
    kpis = build_kpis(
        terminal.ships,
        terminal.containers,
        terminal.resources,
        makespan,
    )
    return SimulationResults(
        config=config,
        makespan=makespan,
        ships=list(terminal.ships),
        containers=list(terminal.containers),
        events=list(terminal.events),
        kpis=kpis,
    )
