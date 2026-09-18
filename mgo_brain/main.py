from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .faults import FaultScenario
from .service import MGOBrainService

ROOT = Path(__file__).resolve().parent.parent
service = MGOBrainService(ROOT / "data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()
    yield
    await service.stop()


app = FastAPI(title="MGO Brain", version="0.3.0", lifespan=lifespan)


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0", "source": "simulator", "analytics": service.analytics.available()}


@app.get("/api/v1/state")
def state():
    return service.state


@app.get("/api/v1/events")
def events(limit: int = 100):
    return service.store.list_events(min(max(limit, 1), 500))


@app.get("/api/v1/trips")
def trips(limit: int = 100):
    return service.store.list_trips(min(max(limit, 1), 500))


@app.get("/api/v1/trips/{trip_id}/report")
def trip_report(trip_id: int):
    report = service.store.get_report(trip_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No report for trip {trip_id}")
    return report


@app.get("/api/v1/starts")
def starts(limit: int = 100):
    return service.store.list_starts(min(max(limit, 1), 500))


@app.get("/api/v1/alerts")
def alerts():
    return service.alert_snapshot()


@app.get("/api/v1/health-summary")
def health_summary():
    return service.health_summary()


@app.get("/api/v1/ai/context")
def ai_context():
    return service.ai_context()


@app.get("/api/v1/baselines")
def baselines():
    return service.baselines.summary()


@app.get("/api/v1/analytics/summary")
def analytics_summary():
    return service.analytics_summary()


@app.get("/api/v1/analytics/compare")
def compare_trips(trip_a: int, trip_b: int):
    result = service.compare_trips(trip_a, trip_b)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both trip IDs do not exist")
    return result


@app.get("/api/v1/spec/signals")
def signal_spec():
    import json
    return json.loads((ROOT / "config" / "signals-v1.json").read_text(encoding="utf-8"))


@app.get("/api/v1/spec/maintenance")
def maintenance_spec():
    import json
    return json.loads((ROOT / "config" / "maintenance-plan.json").read_text(encoding="utf-8"))


@app.get("/api/v1/simulator/faults")
def simulator_faults():
    return {"faults": service.fault_catalog()}


@app.post("/api/v1/simulator/faults/{fault_name}/enable")
def enable_fault(fault_name: str):
    try:
        FaultScenario(fault_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown fault scenario: {fault_name}") from exc
    return {"faults": service.enable_fault(fault_name)}


@app.post("/api/v1/simulator/faults/{fault_name}/disable")
def disable_fault(fault_name: str):
    try:
        FaultScenario(fault_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown fault scenario: {fault_name}") from exc
    return {"faults": service.disable_fault(fault_name)}


@app.post("/api/v1/simulator/faults/clear")
def clear_faults():
    return {"faults": service.clear_faults()}


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
