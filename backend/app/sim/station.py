from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from app.config import StationConfig
from app.sim import physics
from app.sim.demand_curve import demand_std_flow_sm3h
from app.sim.faults import NO_FAULTS, FaultEffects

AMBIENT_TEMP_K = 298.15  # ~25 C ambient inlet gas temperature baseline


@dataclass
class StationSnapshot:
    station_id: str
    sim_timestamp: str  # ISO8601
    mode: str  # 'turboexpander' | 'bypass'
    pi_001_inlet_psi: float
    fi_001_flow_sm3h: float
    ti_002_preheat_temp_c: float
    pt_003_outlet_psi: float
    power_kw: float
    efficiency_pct: float
    active_fault_names: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class Station:
    def __init__(self, config: StationConfig, start_time: datetime | None = None, seed: int | None = None):
        self.config = config
        self.sim_time_s = 0.0
        # Anchored to the most recent midnight (not "now") so that
        # sim_time_s=0 corresponds to displayed 00:00:00. Demand curve and
        # fault scheduling both key off `hour = (sim_time_s % 86400) / 3600`
        # -- anchoring here means that internal "hour" matches the hour
        # shown in sim_timestamp, so e.g. the 03:00 fault scenario actually
        # shows as 03:00 in the historian/UI, not an arbitrary wall-clock hour.
        self.sim_start = start_time or datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self._rng = random.Random(seed)
        self.last_snapshot: StationSnapshot | None = None

    def tick(self, dt_sim_s: float, fault_effects: FaultEffects | None = None) -> StationSnapshot:
        self.sim_time_s += dt_sim_s
        effects = fault_effects or NO_FAULTS

        base_flow = demand_std_flow_sm3h(self.sim_time_s, self.config)
        noisy_flow = max(0.0, base_flow * (1 + self._rng.gauss(0, 0.01)))

        inlet_temp_k = AMBIENT_TEMP_K + self._rng.gauss(0, 1.0)
        preheat_temp_k = physics.preheater_outlet_temp(inlet_temp_k, fouling_factor=effects.fouling_factor)

        mass_flow_kg_s = physics.std_flow_to_mass_flow(noisy_flow)

        if effects.forced_bypass:
            mode = "bypass"
            bypass_result = physics.bypass_prv(
                preheat_temp_k, self.config.inlet_pressure_pa, self.config.outlet_pressure_pa
            )
            power_kw = 0.0
            efficiency_pct = 0.0
        else:
            mode = "turboexpander"
            turbo_result = physics.turboexpander_power(
                mass_flow_kg_s=mass_flow_kg_s,
                t_in_k=preheat_temp_k,
                p_in_pa=self.config.inlet_pressure_pa,
                p_out_pa=self.config.outlet_pressure_pa,
            )
            power_kw = (turbo_result.electrical_power_w / 1000.0) * effects.power_multiplier
            efficiency_pct = turbo_result.overall_efficiency_pct

        inlet_pressure_reading = self.config.inlet_pressure_psi * (
            1 + self._rng.gauss(0, 0.005)
        ) + effects.sensor_bias.get("PI-001", 0.0)
        outlet_pressure_reading = self.config.outlet_pressure_psi * (
            1 + self._rng.gauss(0, 0.005)
        ) + effects.sensor_bias.get("PT-003", 0.0)
        preheat_temp_reading_c = physics.kelvin_to_celsius(preheat_temp_k) + effects.sensor_bias.get(
            "TI-002", 0.0
        )

        snapshot = StationSnapshot(
            station_id=self.config.id,
            sim_timestamp=(self.sim_start + timedelta(seconds=self.sim_time_s)).isoformat(),
            mode=mode,
            pi_001_inlet_psi=round(inlet_pressure_reading, 2),
            fi_001_flow_sm3h=round(noisy_flow, 1),
            ti_002_preheat_temp_c=round(preheat_temp_reading_c, 2),
            pt_003_outlet_psi=round(outlet_pressure_reading, 2),
            power_kw=round(power_kw, 2),
            efficiency_pct=round(efficiency_pct, 2),
            active_fault_names=list(effects.active_fault_names),
        )
        self.last_snapshot = snapshot
        return snapshot
