import pytest

from app.config import STATION_CONFIGS
from app.copilot.tools import execute_tool_safely
from app.historian.db import Database
from app.historian import repository


@pytest.fixture
async def db(tmp_path):
    database = Database(path=tmp_path / "test_historian.db")
    await database.connect()
    for cfg in STATION_CONFIGS:
        await repository.upsert_station(database, cfg)
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_unknown_station_id_returns_error(db):
    result = await execute_tool_safely(db, "get_current_state", {"station_id": "not-a-real-station"})
    assert "error" in result


@pytest.mark.asyncio
async def test_unknown_metric_returns_error(db):
    result = await execute_tool_safely(
        db,
        "query_historian",
        {"station_id": "station-1", "metric": "not_a_real_metric", "start_iso": "2026-01-01", "end_iso": "2026-01-02"},
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_unknown_tool_returns_error(db):
    result = await execute_tool_safely(db, "not_a_real_tool", {})
    assert "error" in result


@pytest.mark.asyncio
async def test_get_current_state_with_no_readings_yet(db):
    result = await execute_tool_safely(db, "get_current_state", {"station_id": "station-1"})
    assert "error" in result


@pytest.mark.asyncio
async def test_list_alarms_empty_is_not_an_error(db):
    result = await execute_tool_safely(db, "list_alarms", {"station_id": "station-1"})
    assert result == {"alarms": [], "count": 0}


@pytest.mark.asyncio
async def test_get_shift_report_data_with_no_data(db):
    result = await execute_tool_safely(
        db,
        "get_shift_report_data",
        {"station_id": "station-1", "start_iso": "2026-01-01T00:00:00", "end_iso": "2026-01-02T00:00:00"},
    )
    assert result["readings_summary"] == {"note": "no readings found in this time range"}
    assert result["alarms"] == []
    assert result["kpis"]["reading_count"] == 0
