from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.historian.models import SCHEMA_STATEMENTS

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "historian.db"


class Database:
    """Owns the single SQLite connection. WAL mode + one writer (the
    simulation engine) -- API read handlers only SELECT."""

    def __init__(self, path: Path = DEFAULT_DB_PATH):
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._conn.commit()
        for statement in SCHEMA_STATEMENTS:
            await self._conn.execute(statement)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected -- call connect() first")
        return self._conn
