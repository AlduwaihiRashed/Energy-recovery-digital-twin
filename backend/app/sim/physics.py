"""Physics model for the pressure letdown / energy recovery station.

Fidelity note: an ideal gas has zero Joule-Thomson coefficient
(dT/dP|H = 0), so the isenthalpic cooling across the bypass PRV must come
from an empirical JT coefficient (a real-gas property), not from ideal-gas
relations. The turboexpander's power/temperature drop, by contrast, comes
from ideal-gas isentropic expansion work extraction, which is a standard
and defensible approximation for a prototype (a full cubic equation of
state is not worth the effort here).
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Gas properties (pipeline-quality natural gas, ~90% CH4 + heavier alkanes/N2) ---
R_UNIVERSAL = 8.314  # J/(mol*K)
GAS_MOLAR_MASS = 0.018  # kg/mol
R_SPECIFIC = R_UNIVERSAL / GAS_MOLAR_MASS  # ~461.9 J/(kg*K)
GAMMA = 1.30  # cp/cv for pipeline natural gas
CP = GAMMA * R_SPECIFIC / (GAMMA - 1)  # ~2001 J/(kg*K)

T_STD_K = 288.15  # 15 C standard temperature
P_STD_PA = 101_325.0
RHO_STD = P_STD_PA * GAS_MOLAR_MASS / (R_UNIVERSAL * T_STD_K)  # ~0.7615 kg/Sm3

# Empirical Joule-Thomson coefficient for pipeline natural gas near ambient T (~0.45 K/bar)
JT_COEFFICIENT_K_PER_PA = 4.5e-6

# Equipment efficiencies
TURBOEXPANDER_ETA = 0.82  # isentropic efficiency, radial inflow turboexpander
GENERATOR_ETA = 0.96  # mechanical shaft -> electrical conversion

PSI_TO_PA = 6894.76
PREHEAT_SETPOINT_K = 318.15  # 45 C, prevents hydrate/ice formation downstream
HX_EFFECTIVENESS = 0.90

# KPI constants
# Revenue back-derived from the pitch deck's own Base Case (slide 9): $250K/yr
# at 380kW average -> 380 * 8760 = 3,328,800 kWh/yr -> $250,000 / 3,328,800 ~= $0.075/kWh
REVENUE_PER_KWH = 0.075
# Documented assumption: typical regional grid-average emissions factor.
CO2_KG_PER_KWH = 0.45

MIN_PHYSICAL_TEMP_K = 150.0  # guard against non-physical/cryogenic results


def psi_to_pa(psi: float) -> float:
    return psi * PSI_TO_PA


def std_flow_to_mass_flow(q_sm3h: float) -> float:
    """Standard m3/h -> kg/s using standard density."""
    return (q_sm3h / 3600.0) * RHO_STD


def joule_thomson_delta_t(p_in_pa: float, p_out_pa: float) -> float:
    """Temperature DROP (K, positive) across an isenthalpic throttle (bypass PRV)."""
    return JT_COEFFICIENT_K_PER_PA * (p_in_pa - p_out_pa)


def isentropic_outlet_temp(t_in_k: float, p_in_pa: float, p_out_pa: float) -> float:
    """Ideal (eta=1) isentropic expansion outlet temperature (ideal-gas relation)."""
    return t_in_k * (p_out_pa / p_in_pa) ** ((GAMMA - 1) / GAMMA)


def preheater_outlet_temp(
    t_inlet_k: float,
    setpoint_k: float = PREHEAT_SETPOINT_K,
    effectiveness: float = HX_EFFECTIVENESS,
    fouling_factor: float = 1.0,
) -> float:
    """Controlled-setpoint HX model. fouling_factor < 1 simulates a fault
    (reduced preheat effectiveness)."""
    delta_available = setpoint_k - t_inlet_k
    return t_inlet_k + effectiveness * fouling_factor * delta_available


@dataclass
class TurboexpanderResult:
    electrical_power_w: float
    gas_outlet_temp_k: float
    overall_efficiency_pct: float


def turboexpander_power(
    mass_flow_kg_s: float,
    t_in_k: float,
    p_in_pa: float,
    p_out_pa: float,
    eta_isentropic: float = TURBOEXPANDER_ETA,
    eta_gen: float = GENERATOR_ETA,
) -> TurboexpanderResult:
    """Compute electrical power output and gas outlet temperature for the
    turboexpander + generator train."""
    t_out_isentropic = isentropic_outlet_temp(t_in_k, p_in_pa, p_out_pa)
    delta_t_isentropic = t_in_k - t_out_isentropic  # positive
    delta_t_actual = eta_isentropic * delta_t_isentropic  # actual drop is smaller
    shaft_power_w = mass_flow_kg_s * CP * delta_t_actual
    electrical_power_w = shaft_power_w * eta_gen
    t_out_actual_k = t_in_k - delta_t_actual
    return TurboexpanderResult(
        electrical_power_w=electrical_power_w,
        gas_outlet_temp_k=t_out_actual_k,
        overall_efficiency_pct=eta_isentropic * eta_gen * 100,
    )


@dataclass
class BypassResult:
    gas_outlet_temp_k: float


def bypass_prv(t_in_k: float, p_in_pa: float, p_out_pa: float) -> BypassResult:
    """Isenthalpic throttle across the bypass PRV: no power extraction, just
    Joule-Thomson cooling."""
    delta_t = joule_thomson_delta_t(p_in_pa, p_out_pa)
    return BypassResult(gas_outlet_temp_k=t_in_k - delta_t)


def kelvin_to_celsius(t_k: float) -> float:
    return t_k - 273.15
