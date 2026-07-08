from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.config import STATION_CONFIGS
from app.historian import repository

router = APIRouter(prefix="/api/stations", tags=["stations"])

_CONFIG_BY_ID = {cfg.id: cfg for cfg in STATION_CONFIGS}


def _require_known_station(station_id: str) -> None:
    if station_id not in _CONFIG_BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown station_id '{station_id}'")


@router.get("")
async def list_stations(request: Request):
    db = request.app.state.db
    stations = await repository.list_stations(db)
    return {"stations": stations}


@router.get("/{station_id}/state")
async def get_state(station_id: str, request: Request):
    _require_known_station(station_id)
    engine = request.app.state.engine
    station = engine.stations.get(station_id)
    if station is None or station.last_snapshot is None:
        raise HTTPException(status_code=404, detail="no live state yet -- simulation still warming up")
    return station.last_snapshot.to_dict()


@router.get("/{station_id}/history")
async def get_history(
    station_id: str,
    request: Request,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    limit: int = Query(default=500, le=5000),
):
    _require_known_station(station_id)
    db = request.app.state.db
    readings = await repository.query_readings(db, station_id, start_iso=start, end_iso=end, limit=limit)
    return {"station_id": station_id, "readings": readings}


@router.get("/{station_id}/alarms")
async def get_alarms(
    station_id: str,
    request: Request,
    active_only: bool = Query(default=False),
    limit: int = Query(default=100, le=1000),
):
    _require_known_station(station_id)
    db = request.app.state.db
    alarms = await repository.query_alarms(db, station_id, active_only=active_only, limit=limit)
    return {"station_id": station_id, "alarms": alarms}


@router.get("/{station_id}/kpis")
async def get_kpis(station_id: str, request: Request):
    _require_known_station(station_id)
    db = request.app.state.db
    return await repository.kpi_rollup(db, station_id)
