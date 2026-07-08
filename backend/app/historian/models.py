"""SQLite schema (stands in for a real OSIsoft/AVEVA historian)."""

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS stations (
        id TEXT PRIMARY KEY,
        name TEXT,
        config_json TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id TEXT NOT NULL,
        ts TEXT NOT NULL,
        pi_001_inlet_psi REAL,
        fi_001_flow_sm3h REAL,
        ti_002_preheat_temp_c REAL,
        pt_003_outlet_psi REAL,
        power_kw REAL,
        efficiency_pct REAL,
        mode TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_readings_station_ts ON readings(station_id, ts)",
    """CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id TEXT NOT NULL,
        ts TEXT NOT NULL,
        severity TEXT,
        tag TEXT,
        message TEXT,
        active INTEGER DEFAULT 1,
        cleared_ts TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_alarms_station_active ON alarms(station_id, active)",
]
