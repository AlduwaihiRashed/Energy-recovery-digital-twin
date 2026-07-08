from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger("ws.manager")


class ConnectionManager:
    """Tracks active WebSocket connections per station id and broadcasts
    snapshots to all of them, dropping sockets that error out."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, station_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[station_id].add(websocket)
        logger.info("ws connected station=%s total=%d", station_id, len(self._connections[station_id]))

    def disconnect(self, station_id: str, websocket: WebSocket) -> None:
        self._connections[station_id].discard(websocket)
        logger.info("ws disconnected station=%s total=%d", station_id, len(self._connections[station_id]))

    async def broadcast(self, station_id: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(station_id, ()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(station_id, ws)
