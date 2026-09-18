from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .service import MGOBrainService

ROOT = Path(__file__).resolve().parent.parent
service = MGOBrainService(ROOT / "data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()
    yield
    await service.stop()


app = FastAPI(title="MGO Brain", version="0.1.0", lifespan=lifespan)


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "source": "simulator"}


@app.get("/api/v1/state")
def state():
    return service.state


@app.get("/api/v1/events")
def events(limit: int = 100):
    return service.store.list_events(min(max(limit, 1), 500))


@app.get("/api/v1/trips")
def trips(limit: int = 100):
    return service.store.list_trips(min(max(limit, 1), 500))


@app.get("/api/v1/starts")
def starts(limit: int = 100):
    return service.store.list_starts(min(max(limit, 1), 500))


@app.get("/api/v1/health-summary")
def health_summary():
    return service.health_summary()


@app.get("/api/v1/ai/context")
def ai_context():
    return service.ai_context()


@app.get("/api/v1/spec/signals")
def signal_spec():
    import json
    return json.loads((ROOT / "config" / "signals-v1.json").read_text(encoding="utf-8"))


@app.get("/api/v1/spec/maintenance")
def maintenance_spec():
    import json
    return json.loads((ROOT / "config" / "maintenance-plan.json").read_text(encoding="utf-8"))


@app.websocket("/ws/live")
async def live(websocket: WebSocket):
    await websocket.accept()
    q = service.subscribe()
    try:
        while True:
            payload = await q.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        service.unsubscribe(q)


def run():
    uvicorn.run("mgo_brain.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    run()
