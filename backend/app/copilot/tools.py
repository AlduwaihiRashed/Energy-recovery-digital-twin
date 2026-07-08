from __future__ import annotations

from app.config import STATION_CONFIGS
from app.historian import repository
from app.historian.db import Database

_VALID_STATION_IDS = {cfg.id for cfg in STATION_CONFIGS}
_VALID_METRICS = [
    "power_kw",
    "pi_001_inlet_psi",
    "fi_001_flow_sm3h",
    "ti_002_preheat_temp_c",
    "pt_003_outlet_psi",
    "efficiency_pct",
]

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_historian",
            "description": (
                "Query time-series sensor readings for a station over a time range. "
                "Returns up to 200 points plus min/max/avg summary stats for the metric."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {"type": "string"},
                    "metric": {"type": "string", "enum": _VALID_METRICS},
                    "start_iso": {"type": "string", "description": "ISO8601 start timestamp"},
                    "end_iso": {"type": "string", "description": "ISO8601 end timestamp"},
                },
                "required": ["station_id", "metric", "start_iso", "end_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_alarms",
            "description": "List alarms for a station, optionally only active ones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {"type": "string"},
                    "active_only": {"type": "boolean"},
                    "since_iso": {
                        "type": "string",
                        "description": "ISO8601 timestamp -- only alarms at/after this time",
                    },
                },
                "required": ["station_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_efficiency",
            "description": "Compute average power output and efficiency over a time window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {"type": "string"},
                    "start_iso": {"type": "string"},
                    "end_iso": {"type": "string"},
                },
                "required": ["station_id", "start_iso", "end_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_state",
            "description": "Get the most recent live sensor reading snapshot for a station.",
            "parameters": {
                "type": "object",
                "properties": {"station_id": {"type": "string"}},
                "required": ["station_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_shift_report_data",
            "description": (
                "Convenience tool: returns a readings summary, alarms, and KPI rollup for a "
                "station in one call. Use this for shift handover reports or general "
                "'what happened' summaries instead of calling other tools separately."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {"type": "string"},
                    "start_iso": {"type": "string"},
                    "end_iso": {"type": "string"},
                },
                "required": ["station_id", "start_iso", "end_iso"],
            },
        },
    },
]


def _validate_station_id(args: dict) -> str | None:
    station_id = args.get("station_id")
    if station_id not in _VALID_STATION_IDS:
        return f"unknown station_id '{station_id}', valid ids: {sorted(_VALID_STATION_IDS)}"
    return None


def _summarize_readings(readings: list[dict]) -> dict:
    if not readings:
        return {"note": "no readings found in this time range"}
    powers = [r["power_kw"] for r in readings]
    effs = [r["efficiency_pct"] for r in readings]
    return {
        "reading_count": len(readings),
        "avg_power_kw": round(sum(powers) / len(powers), 2),
        "min_power_kw": round(min(powers), 2),
        "max_power_kw": round(max(powers), 2),
        "avg_efficiency_pct": round(sum(effs) / len(effs), 2),
    }


async def _tool_query_historian(db: Database, args: dict) -> dict:
    err = _validate_station_id(args)
    if err:
        return {"error": err}
    metric = args.get("metric")
    if metric not in _VALID_METRICS:
        return {"error": f"unknown metric '{metric}', valid metrics: {_VALID_METRICS}"}

    readings = await repository.query_readings(
        db, args["station_id"], start_iso=args.get("start_iso"), end_iso=args.get("end_iso"), limit=200
    )
    values = [r[metric] for r in readings if r.get(metric) is not None]
    if not values:
        return {"points": [], "count": 0, "note": "no readings found in this time range"}
    return {
        "points": [{"ts": r["ts"], "value": r[metric]} for r in readings],
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "avg": round(sum(values) / len(values), 2),
    }


async def _tool_list_alarms(db: Database, args: dict) -> dict:
    err = _validate_station_id(args)
    if err:
        return {"error": err}
    alarms = await repository.query_alarms(
        db,
        args["station_id"],
        active_only=bool(args.get("active_only", False)),
        since_iso=args.get("since_iso"),
        limit=50,
    )
    return {"alarms": alarms, "count": len(alarms)}


async def _tool_compute_efficiency(db: Database, args: dict) -> dict:
    err = _validate_station_id(args)
    if err:
        return {"error": err}
    readings = await repository.query_readings(
        db, args["station_id"], start_iso=args.get("start_iso"), end_iso=args.get("end_iso"), limit=500
    )
    return _summarize_readings(readings)


async def _tool_get_current_state(db: Database, args: dict) -> dict:
    err = _validate_station_id(args)
    if err:
        return {"error": err}
    reading = await repository.latest_reading(db, args["station_id"])
    if reading is None:
        return {"error": "no live state yet -- simulation still warming up"}
    return reading


async def _tool_get_shift_report_data(db: Database, args: dict) -> dict:
    err = _validate_station_id(args)
    if err:
        return {"error": err}
    station_id = args["station_id"]
    readings = await repository.query_readings(
        db, station_id, start_iso=args.get("start_iso"), end_iso=args.get("end_iso"), limit=500
    )
    alarms = await repository.query_alarms(db, station_id, since_iso=args.get("start_iso"), limit=50)
    kpis = await repository.kpi_rollup(db, station_id)
    return {"readings_summary": _summarize_readings(readings), "alarms": alarms, "kpis": kpis}


TOOL_IMPLEMENTATIONS = {
    "query_historian": _tool_query_historian,
    "list_alarms": _tool_list_alarms,
    "compute_efficiency": _tool_compute_efficiency,
    "get_current_state": _tool_get_current_state,
    "get_shift_report_data": _tool_get_shift_report_data,
}


async def execute_tool_safely(db: Database, name: str, args: dict) -> dict:
    impl = TOOL_IMPLEMENTATIONS.get(name)
    if impl is None:
        return {"error": f"unknown tool '{name}'"}
    if not isinstance(args, dict):
        return {"error": "tool arguments must be an object"}
    try:
        return await impl(db, args)
    except Exception as exc:  # feed the error back to the model rather than crashing the chat
        return {"error": f"tool execution failed: {exc}"}
