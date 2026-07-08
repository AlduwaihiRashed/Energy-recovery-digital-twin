from __future__ import annotations

import json

from app.config import DB_PERSIST_EVERY_N_TICKS, SIM_TICK_INTERVAL_S, SIM_TIME_SCALE, StationConfig
from app.historian.db import Database
from app.sim import physics
from app.sim.station import StationSnapshot

# Reading rows are persisted every DB_PERSIST_EVERY_N_TICKS ticks, each tick
# advancing dt_sim_s = SIM_TICK_INTERVAL_S * SIM_TIME_SCALE simulated seconds.
# Since ticks are fixed-interval, rows are evenly spaced in simulated time,
# so cumulative energy can be approximated as sum(power_kw) * row_interval_hours
# rather than needing per-row timestamp deltas.
ROW_INTERVAL_HOURS = (SIM_TICK_INTERVAL_S * SIM_TIME_SCALE * DB_PERSIST_EVERY_N_TICKS) / 3600.0


async def upsert_station(db: Database, config: StationConfig) -> None:
    await db.conn.execute(
        """INSERT INTO stations (id, name, config_json, created_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(id) DO UPDATE SET name=excluded.name, config_json=excluded.config_json""",
        (config.id, config.name, json.dumps({"pipe_size_in": config.pipe_size_in,
                                              "inlet_pressure_psi": config.inlet_pressure_psi,
                                              "outlet_pressure_psi": config.outlet_pressure_psi})),
    )
    await db.conn.commit()


async def list_stations(db: Database) -> list[dict]:
    async with db.conn.execute("SELECT id, name, config_json FROM stations") as cursor:
        rows = await cursor.fetchall()
        columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


async def insert_reading(db: Database, snapshot: StationSnapshot) -> None:
    await db.conn.execute(
        """INSERT INTO readings (station_id, ts, pi_001_inlet_psi, fi_001_flow_sm3h,
           ti_002_preheat_temp_c, pt_003_outlet_psi, power_kw, efficiency_pct, mode)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            snapshot.station_id,
            snapshot.sim_timestamp,
            snapshot.pi_001_inlet_psi,
            snapshot.fi_001_flow_sm3h,
            snapshot.ti_002_preheat_temp_c,
            snapshot.pt_003_outlet_psi,
            snapshot.power_kw,
            snapshot.efficiency_pct,
            snapshot.mode,
        ),
    )
    await db.conn.commit()


def _rows_to_dicts(columns: list[str], rows: list[tuple]) -> list[dict]:
    return [dict(zip(columns, row)) for row in rows]


async def query_readings(
    db: Database,
    station_id: str,
    start_iso: str | None = None,
    end_iso: str | None = None,
    limit: int = 500,
) -> list[dict]:
    query = "SELECT * FROM readings WHERE station_id = ?"
    params: list = [station_id]
    if start_iso:
        query += " AND ts >= ?"
        params.append(start_iso)
    if end_iso:
        query += " AND ts <= ?"
        params.append(end_iso)
    query += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    async with db.conn.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        columns = [d[0] for d in cursor.description]
    return list(reversed(_rows_to_dicts(columns, rows)))  # chronological order


async def latest_reading(db: Database, station_id: str) -> dict | None:
    async with db.conn.execute(
        "SELECT * FROM readings WHERE station_id = ? ORDER BY ts DESC LIMIT 1", (station_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        columns = [d[0] for d in cursor.description]
    return dict(zip(columns, row))


async def insert_alarm(db: Database, station_id: str, ts: str, severity: str, tag: str, message: str) -> int:
    cursor = await db.conn.execute(
        "INSERT INTO alarms (station_id, ts, severity, tag, message, active) VALUES (?, ?, ?, ?, ?, 1)",
        (station_id, ts, severity, tag, message),
    )
    await db.conn.commit()
    return cursor.lastrowid


async def clear_alarm(db: Database, alarm_id: int, cleared_ts: str) -> None:
    await db.conn.execute("UPDATE alarms SET active = 0, cleared_ts = ? WHERE id = ?", (cleared_ts, alarm_id))
    await db.conn.commit()


async def query_alarms(
    db: Database,
    station_id: str,
    active_only: bool = False,
    since_iso: str | None = None,
    limit: int = 100,
) -> list[dict]:
    query = "SELECT * FROM alarms WHERE station_id = ?"
    params: list = [station_id]
    if active_only:
        query += " AND active = 1"
    if since_iso:
        query += " AND ts >= ?"
        params.append(since_iso)
    query += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    async with db.conn.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        columns = [d[0] for d in cursor.description]
    return _rows_to_dicts(columns, rows)


async def kpi_rollup(db: Database, station_id: str) -> dict:
    async with db.conn.execute(
        """SELECT COUNT(*), COALESCE(SUM(power_kw), 0), COALESCE(AVG(power_kw), 0), COALESCE(AVG(efficiency_pct), 0)
           FROM readings WHERE station_id = ?""",
        (station_id,),
    ) as cursor:
        count, sum_power_kw, avg_power_kw, avg_efficiency_pct = await cursor.fetchone()

    cumulative_kwh = sum_power_kw * ROW_INTERVAL_HOURS
    return {
        "station_id": station_id,
        "reading_count": count,
        "avg_power_kw": round(avg_power_kw, 2),
        "avg_efficiency_pct": round(avg_efficiency_pct, 2),
        "cumulative_energy_kwh": round(cumulative_kwh, 2),
        "cumulative_co2_avoided_kg": round(cumulative_kwh * physics.CO2_KG_PER_KWH, 2),
        "cumulative_revenue_usd": round(cumulative_kwh * physics.REVENUE_PER_KWH, 2),
    }
