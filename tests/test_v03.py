from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from mgo_brain.analytics import HistoricalAnalytics
from mgo_brain.baseline import BaselineManager
from mgo_brain.detectors import TripDetector
from mgo_brain.models import PostTripReport, SignalQuality, SignalReading, TripSummary, VehicleMode, VehicleState
from mgo_brain.reports import PostTripReportEngine
from mgo_brain.service import MGOBrainService


def reading(v):
    return SignalReading(value=v, quality=SignalQuality.GOOD, source="test")


def state(ts, mode, rpm=900, speed=0, oil=1.5, coolant=80, voltage=14.1, cvt_dev=0, cvt_temp=55):
    return VehicleState(timestamp=ts, mode=mode, signals={
        "engine.rpm": reading(rpm),
        "vehicle.speed": reading(speed),
        "vehicle.speed_gps": reading(speed),
        "engine.oil_pressure": reading(oil),
        "engine.oil_temp": reading(82),
        "engine.coolant_temp": reading(coolant),
        "electrical.battery_voltage": reading(voltage),
        "electrical.battery_current": reading(3.0),
        "electrical.battery_soc": reading(80),
        "transmission.cvt_ratio": reading(rpm / speed if speed else None),
        "transmission.cvt_ratio_deviation": reading(cvt_dev if speed else None),
        "transmission.cvt_temp_primary": reading(cvt_temp),
        "transmission.cvt_temp_secondary": reading(cvt_temp - 2),
        "fuel.level": reading(60),
        "environment.ambient_temp": reading(8),
    })


def make_trip(value=80.0, eligible=True):
    now = datetime.now(timezone.utc)
    return TripSummary(
        started_at=now,
        ended_at=now + timedelta(minutes=10),
        duration_s=600,
        distance_km=5,
        max_speed_kmh=45,
        avg_speed_kmh=30,
        max_coolant_c=value,
        max_oil_temp_c=88,
        min_oil_pressure_bar=1.4,
        avg_running_voltage_v=14.1,
        avg_cvt_ratio_deviation_pct=1.0,
        max_cvt_temp_c=62,
        baseline_eligible=eligible,
    )


def test_trip_detector_does_not_include_stopped_zero_oil_pressure(tmp_path):
    detector = TripDetector(tmp_path)
    t0 = datetime.now(timezone.utc)
    assert detector.update(state(t0, VehicleMode.IDLE, oil=1.5)) is None
    assert detector.update(state(t0 + timedelta(seconds=1), VehicleMode.DRIVING, rpm=2800, speed=40, oil=2.2)) is None
    done = detector.update(state(t0 + timedelta(seconds=2), VehicleMode.OFF, rpm=0, speed=0, oil=0))
    assert done is not None
    assert done.min_oil_pressure_bar == pytest.approx(1.5)
    assert done.avg_running_voltage_v == pytest.approx(14.1)


def test_reference_baseline_qualification_and_unhealthy_exclusion():
    b = BaselineManager(qualification_samples=3, rolling_samples=3)
    for value in (79.0, 80.0, 81.0):
        b.add_trip(make_trip(value=value, eligible=True))
    metric = b.metrics["max_coolant_c"]
    assert metric.qualified is True
    assert len(metric.reference) == 3

    unhealthy = make_trip(value=110.0, eligible=False)
    anomalies = b.trip_anomalies(unhealthy)
    coolant = next(a for a in anomalies if a["metric"] == "max_coolant_c")
    assert coolant["status"] == "ATTENTION"
    assert coolant["score"] >= 60

    b.add_trip(unhealthy)
    assert len(metric.reference) == 3
    assert list(metric.rolling)[-1] == 110.0


def test_unqualified_baseline_is_explicit():
    b = BaselineManager(qualification_samples=3)
    b.add_trip(make_trip(80))
    anomaly = next(a for a in b.trip_anomalies(make_trip(90)) if a["metric"] == "max_coolant_c")
    assert anomaly["status"] == "UNQUALIFIED"
    assert anomaly["qualified"] is False


def test_post_trip_report_preserves_diagnostic_status():
    trip = make_trip(82, eligible=False)
    trip.id = 7
    trip.diagnostic_status = "CRITICAL"
    report = PostTripReportEngine().generate(trip, [], False)
    assert report.trip_id == 7
    assert report.status == "CRITICAL"
    assert report.eligible_for_baseline is False
    assert any("excluded" in finding.lower() for finding in report.findings)


def test_compare_trip_api_core(tmp_path):
    service = MGOBrainService(tmp_path)
    a = make_trip(80)
    b = make_trip(90)
    a.id = service.store.add_trip(a)
    b.id = service.store.add_trip(b)
    result = service.compare_trips(a.id, b.id)
    assert result is not None
    assert result["comparison"]["max_coolant_c"]["delta"] == pytest.approx(10)
    assert result["comparison"]["max_coolant_c"]["delta_pct"] == pytest.approx(12.5)


def test_store_report_roundtrip(tmp_path):
    service = MGOBrainService(tmp_path)
    trip = make_trip()
    trip.id = service.store.add_trip(trip)
    report = PostTripReport(trip_id=trip.id, status="NORMAL", findings=["ok"])
    service.store.add_report(report)
    loaded = service.store.get_report(trip.id)
    assert loaded is not None
    assert loaded["trip_id"] == trip.id
    assert loaded["findings"] == ["ok"]


def test_parquet_roundtrip_with_duckdb(tmp_path):
    pytest.importorskip("duckdb")
    analytics = HistoricalAnalytics(tmp_path)
    path = tmp_path / "trip_test.jsonl"
    rows = [
        {
            "timestamp": "2026-09-18T10:00:00+00:00", "mode": "DRIVING",
            "vehicle_speed_kmh": 40, "vehicle_speed_gps_kmh": 39,
            "engine_rpm": 2800, "coolant_temp_c": 80, "oil_temp_c": 85,
            "oil_pressure_bar": 2.1, "battery_voltage_v": 14.1, "battery_current_a": 3,
            "battery_soc_pct": 80, "cvt_ratio": 70, "cvt_ratio_deviation_pct": 1.5,
            "cvt_temp_primary_c": 60, "cvt_temp_secondary_c": 57,
            "fuel_level_pct": 60, "ambient_temp_c": 8,
        },
        {
            "timestamp": "2026-09-18T10:00:01+00:00", "mode": "DRIVING",
            "vehicle_speed_kmh": 42, "vehicle_speed_gps_kmh": 41,
            "engine_rpm": 2900, "coolant_temp_c": 82, "oil_temp_c": 87,
            "oil_pressure_bar": 2.0, "battery_voltage_v": 14.2, "battery_current_a": 2,
            "battery_soc_pct": 81, "cvt_ratio": 69, "cvt_ratio_deviation_pct": 2.0,
            "cvt_temp_primary_c": 62, "cvt_temp_secondary_c": 58,
            "fuel_level_pct": 59, "ambient_temp_c": 8,
        },
    ]
    path.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
    result = analytics.finalize_trip(path)
    assert result is not None and result.endswith(".parquet")
    assert not path.exists()
    metrics = analytics.inspect_trip(result)
    assert metrics["samples"] == 2
    assert metrics["max_coolant_c"] == pytest.approx(82)
    summary = analytics.summary()
    assert summary["trip_files"] == 1
    assert summary["samples"] == 2
