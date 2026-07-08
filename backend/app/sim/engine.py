from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Iterable

from app.config import DB_PERSIST_EVERY_N_TICKS, SIM_TICK_INTERVAL_S, SIM_TIME_SCALE, STATION_CONFIGS
from app.config import StationConfig
from app.sim.faults import AlarmEvent, FaultManager
from app.sim.station import Station, StationSnapshot

logger = logging.getLogger("sim.engine")

BroadcastFn = Callable[[str, dict], Awaitable[None]]
PersistFn = Callable[[StationSnapshot], Awaitable[None]]
AlarmEventFn = Callable[[str, str, AlarmEvent], Awaitable[None]]


class SimulationEngine:
    """Owns 1..N stations, ticks them on a wall-clock interval, and fans out
    each snapshot to an optional broadcast hook (WebSocket), an optional
    persist hook (historian), and an optional alarm-event hook (fired on
    fault open/close transitions). All three are injected so the engine is
    fully runnable and testable (console-logging snapshots) before the
    WebSocket layer or the database exist.
    """

    def __init__(
        self,
        station_configs: Iterable[StationConfig] = STATION_CONFIGS,
        broadcast_fn: BroadcastFn | None = None,
        persist_fn: PersistFn | None = None,
        alarm_event_fn: AlarmEventFn | None = None,
        tick_interval_s: float = SIM_TICK_INTERVAL_S,
        time_scale: float = SIM_TIME_SCALE,
        persist_every_n_ticks: int = DB_PERSIST_EVERY_N_TICKS,
    ):
        self.stations: dict[str, Station] = {cfg.id: Station(cfg) for cfg in station_configs}
        self.fault_managers: dict[str, FaultManager] = {cfg.id: FaultManager() for cfg in station_configs}
        self.broadcast_fn = broadcast_fn
        self.persist_fn = persist_fn
        self.alarm_event_fn = alarm_event_fn
        self.tick_interval_s = tick_interval_s
        self.time_scale = time_scale
        self.persist_every_n_ticks = persist_every_n_ticks
        self._tick_count = 0
        self._running = False

    async def run(self) -> None:
        self._running = True
        logger.info(
            "simulation engine started: %d station(s), tick=%.1fs, time_scale=%.0fx",
            len(self.stations),
            self.tick_interval_s,
            self.time_scale,
        )
        while self._running:
            await self.tick_once()
            await asyncio.sleep(self.tick_interval_s)

    async def tick_once(self) -> dict[str, StationSnapshot]:
        dt_sim_s = self.tick_interval_s * self.time_scale
        self._tick_count += 1
        should_persist = self._tick_count % self.persist_every_n_ticks == 0

        snapshots: dict[str, StationSnapshot] = {}
        for station_id, station in self.stations.items():
            effects, alarm_events = self.fault_managers[station_id].effects_at(station.sim_time_s)
            snapshot = station.tick(dt_sim_s, fault_effects=effects)
            snapshots[station_id] = snapshot

            if self.broadcast_fn:
                await self.broadcast_fn(station_id, snapshot.to_dict())
            else:
                logger.info("tick station=%s %s", station_id, snapshot.to_dict())

            if self.persist_fn and should_persist:
                await self.persist_fn(snapshot)

            if self.alarm_event_fn:
                for event in alarm_events:
                    await self.alarm_event_fn(station_id, snapshot.sim_timestamp, event)

        return snapshots

    def stop(self) -> None:
        self._running = False
