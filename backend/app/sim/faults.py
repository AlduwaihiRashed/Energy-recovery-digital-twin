"""Fault / anomaly injection.

Each FaultDefinition fires on a fixed simulated hour-of-day window, so it
recurs every simulated day (a full day completes in ~6 real minutes at the
default 240x time scale -- see app/config.py). FaultManager tracks
active/inactive transitions per fault so the engine can emit exactly one
alarm-open and one alarm-close event per occurrence, rather than re-firing
every tick while a fault is active.

The scenarios below are deliberately layered around simulated 03:00 (demand
is already at its daily trough there, per app/sim/demand_curve.py) so the
demo story is: "why did output drop at 03:00" has two contributing causes
(HX fouling reducing preheat, then the bypass valve sticking open) rather
than just low overnight demand -- something for the AI Operator Copilot to
actually investigate and explain.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SECONDS_PER_DAY = 86_400.0


@dataclass
class FaultEffects:
    fouling_factor: float = 1.0  # 1.0 = clean HX, <1.0 = fouled/reduced preheat
    forced_bypass: bool = False  # True = bypass valve stuck open, no power extraction
    power_multiplier: float = 1.0  # additional derate on turboexpander power
    sensor_bias: dict[str, float] = field(default_factory=dict)  # tag -> additive bias
    active_fault_names: list[str] = field(default_factory=list)


NO_FAULTS = FaultEffects()


@dataclass(frozen=True)
class FaultDefinition:
    name: str
    tag: str | None  # instrument tag for P&ID/alarm highlighting, or None for a station-wide fault
    trigger_hour: float  # simulated hour-of-day (0-24) when the fault begins
    duration_hours: float
    severity: str  # 'warning' | 'critical'
    message: str
    fouling_factor: float = 1.0
    forced_bypass: bool = False
    power_multiplier: float = 1.0
    sensor_bias: dict[str, float] = field(default_factory=dict)

    def is_active_at(self, hour: float) -> bool:
        end = self.trigger_hour + self.duration_hours
        if end <= 24.0:
            return self.trigger_hour <= hour < end
        return hour >= self.trigger_hour or hour < (end - 24.0)


FAULT_DEFINITIONS: list[FaultDefinition] = [
    FaultDefinition(
        name="preheat_fouling",
        tag="TI-002",
        trigger_hour=3.0,
        duration_hours=1.5,
        severity="warning",
        message="Preheater HX fouling detected -- reduced preheat effectiveness, outlet temp trending low.",
        fouling_factor=0.45,
    ),
    FaultDefinition(
        name="bypass_valve_stuck",
        tag="PT-003",
        trigger_hour=3.25,
        duration_hours=0.5,
        severity="critical",
        message="Bypass PRV valve stuck open -- turboexpander offline, zero power recovery.",
        forced_bypass=True,
    ),
    FaultDefinition(
        name="pi001_sensor_drift",
        tag="PI-001",
        trigger_hour=9.0,
        duration_hours=2.0,
        severity="warning",
        message="Inlet pressure sensor drifting -- reading bias detected, recommend recalibration.",
        sensor_bias={"PI-001": 18.0},
    ),
]


@dataclass
class AlarmEvent:
    kind: str  # 'open' | 'close'
    fault: FaultDefinition


class FaultManager:
    """Evaluates FAULT_DEFINITIONS against simulated time and emits
    open/close alarm events on state transitions."""

    def __init__(self, fault_definitions: list[FaultDefinition] = FAULT_DEFINITIONS):
        self.fault_definitions = fault_definitions
        self._active_state: dict[str, bool] = {fd.name: False for fd in fault_definitions}

    def effects_at(self, sim_seconds: float) -> tuple[FaultEffects, list[AlarmEvent]]:
        hour = (sim_seconds % SECONDS_PER_DAY) / 3600.0
        events: list[AlarmEvent] = []

        fouling_factor = 1.0
        forced_bypass = False
        power_multiplier = 1.0
        sensor_bias: dict[str, float] = {}
        active_names: list[str] = []

        for fd in self.fault_definitions:
            is_active = fd.is_active_at(hour)
            was_active = self._active_state[fd.name]

            if is_active and not was_active:
                events.append(AlarmEvent(kind="open", fault=fd))
            elif was_active and not is_active:
                events.append(AlarmEvent(kind="close", fault=fd))
            self._active_state[fd.name] = is_active

            if is_active:
                active_names.append(fd.name)
                fouling_factor *= fd.fouling_factor
                forced_bypass = forced_bypass or fd.forced_bypass
                power_multiplier *= fd.power_multiplier
                for tag, bias in fd.sensor_bias.items():
                    sensor_bias[tag] = sensor_bias.get(tag, 0.0) + bias

        effects = FaultEffects(
            fouling_factor=fouling_factor,
            forced_bypass=forced_bypass,
            power_multiplier=power_multiplier,
            sensor_bias=sensor_bias,
            active_fault_names=active_names,
        )
        return effects, events
