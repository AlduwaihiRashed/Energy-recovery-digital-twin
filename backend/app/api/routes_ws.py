from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/stations/{station_id}")
async def station_ws(websocket: WebSocket, station_id: str):
    manager = websocket.app.state.ws_manager
    await manager.connect(station_id, websocket)
    try:
        while True:
            # Client doesn't need to send anything; just keep the socket
            # open and detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(station_id, websocket)
