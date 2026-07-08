from app.config import STATION_CONFIGS
from app.sim import physics

STATION = STATION_CONFIGS[0]


def _power_kw_at(std_flow_sm3h: float) -> float:
    mass_flow = physics.std_flow_to_mass_flow(std_flow_sm3h)
    t_in_k = physics.PREHEAT_SETPOINT_K
    result = physics.turboexpander_power(
        mass_flow_kg_s=mass_flow,
        t_in_k=t_in_k,
        p_in_pa=STATION.inlet_pressure_pa,
        p_out_pa=STATION.outlet_pressure_pa,
    )
    return result.electrical_power_w / 1000.0


def test_low_demand_power_in_deck_band():
    power_kw = _power_kw_at(STATION.min_std_flow_sm3h)
    assert 100 <= power_kw <= 250, f"expected ~150kW at low demand, got {power_kw:.1f}kW"


def test_nominal_demand_power_in_deck_band():
    power_kw = _power_kw_at(STATION.nominal_std_flow_sm3h)
    assert 250 <= power_kw <= 450, f"expected ~350kW at nominal demand, got {power_kw:.1f}kW"


def test_peak_demand_power_in_deck_band():
    power_kw = _power_kw_at(STATION.max_std_flow_sm3h)
    assert 450 <= power_kw <= 650, f"expected ~600kW at peak demand, got {power_kw:.1f}kW"


def test_turboexpander_outlet_temp_is_physical():
    for std_flow in (STATION.min_std_flow_sm3h, STATION.nominal_std_flow_sm3h, STATION.max_std_flow_sm3h):
        mass_flow = physics.std_flow_to_mass_flow(std_flow)
        result = physics.turboexpander_power(
            mass_flow_kg_s=mass_flow,
            t_in_k=physics.PREHEAT_SETPOINT_K,
            p_in_pa=STATION.inlet_pressure_pa,
            p_out_pa=STATION.outlet_pressure_pa,
        )
        assert result.gas_outlet_temp_k > physics.MIN_PHYSICAL_TEMP_K
        assert result.gas_outlet_temp_k < physics.PREHEAT_SETPOINT_K


def test_bypass_prv_produces_nonzero_cooling():
    # Regression guard: an ideal-gas-only model would produce zero JT cooling,
    # which contradicts the deck's own thesis (slide 3: "Joule-Thomson effect
    # in PRVs destroys recoverable enthalpy").
    result = physics.bypass_prv(
        t_in_k=physics.PREHEAT_SETPOINT_K,
        p_in_pa=STATION.inlet_pressure_pa,
        p_out_pa=STATION.outlet_pressure_pa,
    )
    delta_t = physics.PREHEAT_SETPOINT_K - result.gas_outlet_temp_k
    assert delta_t > 0
    assert result.gas_outlet_temp_k > physics.MIN_PHYSICAL_TEMP_K


def test_preheater_reaches_setpoint_at_full_effectiveness():
    t_out = physics.preheater_outlet_temp(t_inlet_k=280.0)
    assert abs(t_out - (280.0 + 0.90 * (physics.PREHEAT_SETPOINT_K - 280.0))) < 1e-6


def test_preheater_fouling_reduces_outlet_temp():
    t_out_normal = physics.preheater_outlet_temp(t_inlet_k=280.0, fouling_factor=1.0)
    t_out_fouled = physics.preheater_outlet_temp(t_inlet_k=280.0, fouling_factor=0.5)
    assert t_out_fouled < t_out_normal
