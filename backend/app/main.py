import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_copilot import router as copilot_router
from app.api.routes_station import router as stations_router
from app.api.routes_ws import router as ws_router
from app.config import STATION_CONFIGS
from app.historian import repository
from app.historian.db import Database
from app.sim.engine import SimulationEngine
from app.ws.manager import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database()
    await db.connect()
    for cfg in STATION_CONFIGS:
        await repository.upsert_station(db, cfg)
    app.state.db = db

    ws_manager = ConnectionManager()
    app.state.ws_manager = ws_manager

    open_alarm_ids: dict[tuple[str, str], int] = {}

    async def persist_fn(snapshot):
        await repository.insert_reading(db, snapshot)

    async def broadcast_fn(station_id: str, payload: dict) -> None:
        await ws_manager.broadcast(station_id, payload)

    async def alarm_event_fn(station_id: str, ts: str, event) -> None:
        if event.kind == "open":
            alarm_id = await repository.insert_alarm(
                db, station_id, ts, event.fault.severity, event.fault.tag or "", event.fault.message
            )
            open_alarm_ids[(station_id, event.fault.name)] = alarm_id
        else:
            alarm_id = open_alarm_ids.pop((station_id, event.fault.name), None)
            if alarm_id is not None:
                await repository.clear_alarm(db, alarm_id, ts)

    app.state.engine = SimulationEngine(
        persist_fn=persist_fn, broadcast_fn=broadcast_fn, alarm_event_fn=alarm_event_fn
    )
    app.state.sim_task = asyncio.create_task(app.state.engine.run())
    yield
    app.state.engine.stop()
    app.state.sim_task.cancel()
    await db.close()


app = FastAPI(title="Energy Recovery Digital Twin API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stations_router)
app.include_router(ws_router)
app.include_router(copilot_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
