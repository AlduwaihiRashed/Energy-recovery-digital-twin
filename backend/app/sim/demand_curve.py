"""Synthetic daily gas-demand curve."""

from __future__ import annotations

import math

from app.config import StationConfig

SECONDS_PER_DAY = 86_400.0
PEAK_HOUR = 15.0  # afternoon peak
TROUGH_HOUR = 3.0  # overnight trough -- also where the demo fault scenario lives


def demand_std_flow_sm3h(sim_seconds: float, station: StationConfig) -> float:
    """Smooth daily demand curve: minimum ~03:00, maximum ~15:00 (12h apart)."""
    hour = (sim_seconds % SECONDS_PER_DAY) / 3600.0
    phase = 2 * math.pi * (hour - PEAK_HOUR) / 24.0
    shape = (math.cos(phase) + 1) / 2  # 1.0 at PEAK_HOUR, 0.0 at TROUGH_HOUR
    span = station.max_std_flow_sm3h - station.min_std_flow_sm3h
    return station.min_std_flow_sm3h + shape * span
