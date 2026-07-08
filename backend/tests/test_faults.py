from app.sim.faults import FaultManager

SECONDS_PER_HOUR = 3600.0


def _events_over_one_day(manager: FaultManager) -> list[str]:
    events_log = []
    for hour in range(0, 24 * 4):  # 15-minute resolution
        sim_seconds = hour * SECONDS_PER_HOUR / 4
        _, events = manager.effects_at(sim_seconds)
        for event in events:
            events_log.append(f"{event.kind}:{event.fault.name}")
    return events_log


def test_each_fault_opens_and_closes_exactly_once_per_day():
    manager = FaultManager()
    events = _events_over_one_day(manager)

    for fault_name in ("preheat_fouling", "bypass_valve_stuck", "pi001_sensor_drift"):
        assert events.count(f"open:{fault_name}") == 1
        assert events.count(f"close:{fault_name}") == 1
        assert events.index(f"open:{fault_name}") < events.index(f"close:{fault_name}")


def test_faults_recur_on_a_second_day():
    manager = FaultManager()
    _events_over_one_day(manager)  # day 1
    events_day_2 = []
    for hour in range(24, 48):
        sim_seconds = hour * SECONDS_PER_HOUR
        _, events = manager.effects_at(sim_seconds)
        events_day_2.extend(f"{e.kind}:{e.fault.name}" for e in events)

    assert "open:preheat_fouling" in events_day_2
    assert "close:preheat_fouling" in events_day_2


def test_bypass_and_fouling_overlap_at_0315():
    manager = FaultManager()
    effects, _ = manager.effects_at(3.25 * SECONDS_PER_HOUR)
    assert effects.forced_bypass is True
    assert effects.fouling_factor < 1.0
    assert "preheat_fouling" in effects.active_fault_names
    assert "bypass_valve_stuck" in effects.active_fault_names


def test_no_faults_active_at_noon():
    manager = FaultManager()
    effects, events = manager.effects_at(12.0 * SECONDS_PER_HOUR)
    assert effects.active_fault_names == []
    assert effects.forced_bypass is False
    assert effects.fouling_factor == 1.0
