from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mgo_brain.bench_smoke import run_bench_smoke
from mgo_brain.service import MGOBrainService
from mgo_brain.sources.bench import BENCH_SCENARIOS, BenchController, BenchRigSourceAdapter
from mgo_brain.sources.config import SourceFactory, load_source_config
from mgo_brain.sources.factory import register_standard_hardware_builders


ROOT = Path(__file__).resolve().parent.parent


def test_bench_controller_exposes_independent_sources():
    controller = BenchController(time_scale=1)
    expected = {
        "can.bfi",
        "sensorhub.can",
        "smartshunt",
        "modbus.di",
        "tpms",
        "gnss",
    }
    found = set()
    for channel in expected:
        update = controller.update_for(channel, 12.0)
        assert update is not None
        found.add(update.source)
    assert found == expected


def test_bench_source_uses_source_mux():
    async def run():
        source = BenchRigSourceAdapter(time_scale=100.0, max_updates=1)
        stream = source.stream()
        updates = []
        try:
            for _ in range(6):
                updates.append(await asyncio.wait_for(anext(stream), timeout=1.0))
        finally:
            await stream.aclose()
        return {x.source for x in updates}

    sources = asyncio.run(run())
    assert sources == {
        "can.bfi",
        "sensorhub.can",
        "smartshunt",
        "modbus.di",
        "tpms",
        "gnss",
    }


def test_factory_builds_bench_from_config(tmp_path):
    config_path = tmp_path / "sources.json"
    config_path.write_text(json.dumps({
        "stale_after_s": 3,
        "sources": [{
            "type": "bench",
            "enabled": True,
            "options": {"scenario": "normal", "time_scale": 10},
        }],
    }), encoding="utf-8")
    factory = SourceFactory()
    register_standard_hardware_builders(factory)
    source = factory.build(load_source_config(config_path))
    assert source.name == "bench-rig"
    assert source.controller.scenario == "normal"


def test_normal_bench_smoke_runs_full_pipeline(tmp_path):
    report = run_bench_smoke(
        data_dir=tmp_path,
        signal_registry_path=ROOT / "config" / "signals-v1.json",
        scenario="normal",
    )
    assert report["source"] == "bench-rig"
    assert all(report["checks"].values())
    assert report["starts"]
    assert report["trips"]
    assert report["trips"][0]["distance_km"] > 0
    assert report["ai"]["answer"]
    assert report["ai"]["provider"] == "local"


def test_low_oil_scenario_reaches_deterministic_alert(tmp_path):
    report = run_bench_smoke(
        data_dir=tmp_path,
        signal_registry_path=ROOT / "config" / "signals-v1.json",
        scenario="low_oil_pressure",
    )
    codes = {x["code"] for x in report["alerts"]}
    assert "ALERT_ACTIVE:LOW_OIL_PRESSURE" in codes
    assert any(x["engine"] == "CRITICAL" for x in report["snapshots"])


def test_undercharge_scenario_reaches_electrical_health(tmp_path):
    report = run_bench_smoke(
        data_dir=tmp_path,
        signal_registry_path=ROOT / "config" / "signals-v1.json",
        scenario="undercharge",
    )
    codes = {x["code"] for x in report["alerts"]}
    assert "ALERT_ACTIVE:CHARGING_LOW" in codes
    assert any(x["electrical"] == "WATCH" for x in report["snapshots"])


def test_sensorhub_dropout_becomes_unknown_not_normal(tmp_path):
    report = run_bench_smoke(
        data_dir=tmp_path,
        signal_registry_path=ROOT / "config" / "signals-v1.json",
        scenario="sensorhub_dropout",
    )
    during_dropout = next(x for x in report["snapshots"] if x["elapsed_s"] == 14.0)
    assert during_dropout["engine"] == "UNKNOWN"
    assert during_dropout["cvt"] == "UNKNOWN"


def test_bench_service_reports_and_changes_scenario(tmp_path):
    source = BenchRigSourceAdapter(time_scale=10)
    service = MGOBrainService(
        tmp_path,
        source_adapter=source,
        signal_registry_path=ROOT / "config" / "signals-v1.json",
    )
    assert service.bench_active is True
    assert service.bench_status()["scenario"] == "normal"
    assert service.set_bench_scenario("cvt_overheat")["scenario"] == "cvt_overheat"
    assert service.source_status()["bench_active"] is True


def test_bench_scenarios_are_stable_contract():
    assert set(BENCH_SCENARIOS) == {
        "normal",
        "weak_battery",
        "undercharge",
        "low_oil_pressure",
        "overheat",
        "cvt_overheat",
        "sensorhub_dropout",
    }
