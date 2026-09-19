from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .ai_gateway import AIGateway
from .service import MGOBrainService
from .sources.bench import BenchController, BenchRigSourceAdapter


BENCH_TIMELINE = (0.5, 2.5, 3.5, 4.5, 5.5, 6.5, 10.0, 14.0, 18.0, 20.5, 22.5)
BENCH_CHANNELS = ("can.bfi", "sensorhub.can", "smartshunt", "modbus.di", "tpms", "gnss")


def run_bench_smoke(
    *,
    data_dir: str | Path,
    signal_registry_path: str | Path | None = None,
    scenario: str = "normal",
) -> dict[str, Any]:
    controller = BenchController(scenario=scenario, time_scale=1.0)
    source = BenchRigSourceAdapter(controller=controller, time_scale=1.0, max_updates=1)
    service = MGOBrainService(
        Path(data_dir),
        source_adapter=source,
        signal_registry_path=Path(signal_registry_path) if signal_registry_path else None,
    )

    snapshots = []
    for elapsed in BENCH_TIMELINE:
        state = None
        for channel in BENCH_CHANNELS:
            update = controller.update_for(channel, elapsed)
            if update is None:
                continue
            state = service.aggregator.apply(update, now=update.timestamp)
        if state is None:
            continue
        service.process_state(state)
        health = service.health_summary()
        snapshots.append({
            "elapsed_s": elapsed,
            "mode": state.mode.value,
            "overall": health["overall"],
            "engine": _status(health, "ENGINE"),
            "cvt": _status(health, "CVT"),
            "electrical": _status(health, "ELECTRICAL"),
            "tyres": _status(health, "TYRES"),
            "brakes": _status(health, "BRAKES"),
        })

    ai = AIGateway(service, provider_name="local")
    question = "Как сейчас чувствует себя двигатель?"
    response = ai.ask(question, include_evidence=False)

    trips = service.store.list_trips(10)
    starts = service.store.list_starts(10)
    events = service.store.list_events(100)
    alerts = [
        row for row in events
        if str(row.get("code", "")).startswith("ALERT_")
    ]
    return {
        "scenario": scenario,
        "source": service.source.name,
        "snapshots": snapshots,
        "starts": starts,
        "trips": trips,
        "alerts": alerts,
        "ai": {
            "provider": response.provider,
            "answer": response.answer,
            "tools_used": response.tools_used,
            "warnings": response.warnings,
        },
        "checks": {
            "start_recorded": bool(starts),
            "trip_recorded": bool(trips),
            "trip_distance_positive": bool(trips and trips[0].get("distance_km", 0) > 0),
            "ask_mgo_answered": bool(response.answer),
            "all_primary_subsystems_seen": _all_seen(snapshots),
        },
    }


def run_temporary_bench_smoke(
    *,
    signal_registry_path: str | Path | None = None,
    scenario: str = "normal",
) -> dict[str, Any]:
    with TemporaryDirectory(prefix="mgo-bench-") as tmp:
        return run_bench_smoke(
            data_dir=tmp,
            signal_registry_path=signal_registry_path,
            scenario=scenario,
        )


def _status(summary: dict[str, Any], subsystem: str) -> str:
    for item in summary.get("subsystems", []):
        if item.get("subsystem") == subsystem:
            return str(item.get("status"))
    return "UNKNOWN"


def _all_seen(snapshots: list[dict[str, Any]]) -> bool:
    required = ("engine", "cvt", "electrical", "tyres", "brakes")
    return any(
        all(item.get(name) not in {None, "UNKNOWN"} for name in required)
        for item in snapshots
    )
