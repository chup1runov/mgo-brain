from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .faults import FaultScenario
from .service import MGOBrainService
from .runtime import RuntimeSettings
from .doctor import run_doctor
from .survey import SurveyAnalyzeRequest, SurveyParseRequest, analyze_text, parse_candump, sample_pair, summarize_records
from .commissioning_models import SurveySessionCreateRequest
from .survey_sessions import SurveySessionStore

ROOT = Path(__file__).resolve().parent.parent
settings = RuntimeSettings.from_env(ROOT)
settings.ensure_runtime_dirs()
service = MGOBrainService(
    settings.data_dir,
    source_config_path=settings.sources_path,
    signal_registry_path=settings.signal_registry_path,
)
survey_sessions = SurveySessionStore(settings.data_dir / "surveys")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()
    yield
    await service.stop()


app = FastAPI(title="MGO Brain", version="0.5.3", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def dashboard():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.5.3",
        "source": service.source.name,
        "analytics": service.analytics.available(),
        "data_dir": str(settings.data_dir),
        "config_dir": str(settings.config_dir),
    }


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(ROOT / "static" / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/service-worker.js")
def service_worker():
    return FileResponse(ROOT / "static" / "service-worker.js", media_type="application/javascript")


@app.get("/api/v1/state")
def state():
    return service.state


@app.get("/api/v1/system/doctor")
def system_doctor():
    return run_doctor(settings)


@app.get("/api/v1/sources")
def sources():
    return service.source_status()



@app.get("/api/v1/survey/sample")
def survey_sample():
    return sample_pair()


@app.post("/api/v1/survey/parse")
def survey_parse(request: SurveyParseRequest):
    records, rejected = parse_candump(request.log)
    return {
        "summary": summarize_records(records),
        "rejected": rejected,
    }


@app.post("/api/v1/survey/analyze")
def survey_analyze(request: SurveyAnalyzeRequest):
    return analyze_text(
        request.baseline,
        request.action,
        label=request.label,
        max_candidates=request.max_candidates,
    )


@app.get("/api/v1/survey/sessions")
def survey_session_list(limit: int = 100):
    return survey_sessions.list(min(max(limit, 1), 500))


@app.post("/api/v1/survey/sessions")
def survey_session_create(request: SurveySessionCreateRequest):
    return survey_sessions.create(
        label=request.label,
        baseline=request.baseline,
        action=request.action,
        notes=request.notes,
        max_candidates=request.max_candidates,
    )


@app.get("/api/v1/survey/sessions/{session_id}")
def survey_session_get(session_id: str):
    item = survey_sessions.get(session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Survey session not found")
    return item


@app.get("/api/v1/survey/sessions/{session_id}/files/{kind}")
def survey_session_file(session_id: str, kind: str):
    path = survey_sessions.file_path(session_id, kind)
    if path is None:
        raise HTTPException(status_code=404, detail="Survey session file not found")
    return FileResponse(path)


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


@app.get("/api/v1/reports")
def reports(limit: int = 100):
    return service.store.list_reports(min(max(limit, 1), 500))


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
    return json.loads(settings.signal_registry_path.read_text(encoding="utf-8"))


@app.get("/api/v1/spec/maintenance")
def maintenance_spec():
    import json
    return json.loads(settings.maintenance_path.read_text(encoding="utf-8"))


@app.get("/api/v1/simulator/faults")
def simulator_faults():
    return {"faults": service.fault_catalog(), "active": service.simulator_active}


@app.post("/api/v1/simulator/faults/{fault_name}/enable")
def enable_fault(fault_name: str):
    try:
        FaultScenario(fault_name)
        return {"faults": service.enable_fault(fault_name)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown fault scenario: {fault_name}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/simulator/faults/{fault_name}/disable")
def disable_fault(fault_name: str):
    try:
        FaultScenario(fault_name)
        return {"faults": service.disable_fault(fault_name)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown fault scenario: {fault_name}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    uvicorn.run("mgo_brain.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    run()
