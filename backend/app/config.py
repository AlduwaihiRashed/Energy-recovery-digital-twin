"""Station configuration and simulation-wide settings.

Calibration note: the pitch deck states inlet flow of "~2,900 m3/h" as a
single indicative figure (deck slide 8 marks all such values as "indicative
estimates... subject to change"). To land power output in the deck's
stated 200-600 kW band using this project's physics model (see
app/sim/physics.py), the demand curve is deliberately driven over a wider
~4,800-19,000 Sm3/h range (at a fixed ~700 psia -> 165 psia pressure ratio)
rather than pinned to the single 2,900 m3/h figure. Worked calibration:

    demand level | std flow (Sm3/h) | mass flow (kg/s) | electrical power
    low          | ~4,800            | ~1.01             | ~150 kW
    nominal      | ~11,200           | ~2.36             | ~350 kW
    peak         | ~19,150           | ~4.05             | ~600 kW
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.sim.physics import psi_to_pa


@dataclass(frozen=True)
class StationConfig:
    id: str
    name: str
    pipe_size_in: float
    inlet_pressure_psi: float
    outlet_pressure_psi: float
    inlet_pressure_pa: float = field(init=False)
    outlet_pressure_pa: float = field(init=False)
    min_std_flow_sm3h: float = 4_800.0
    nominal_std_flow_sm3h: float = 11_200.0
    max_std_flow_sm3h: float = 19_150.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "inlet_pressure_pa", psi_to_pa(self.inlet_pressure_psi))
        object.__setattr__(self, "outlet_pressure_pa", psi_to_pa(self.outlet_pressure_psi))


STATION_CONFIGS: list[StationConfig] = [
    StationConfig(
        id="station-1",
        name="Downtown Letdown Station",
        pipe_size_in=16.0,
        inlet_pressure_psi=700.0,
        outlet_pressure_psi=165.0,
    ),
]

# 1 real second = SIM_TIME_SCALE simulated seconds. At 240x, a 24h simulated
# demand cycle completes in 6 real minutes -- fast enough to be visible in a
# live demo walkthrough.
SIM_TIME_SCALE = 240.0
SIM_TICK_INTERVAL_S = 1.0
DB_PERSIST_EVERY_N_TICKS = 3
