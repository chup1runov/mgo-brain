from datetime import datetime, timedelta, timezone

from mgo_brain.alerts import AlertManager, AlertStatus
from mgo_brain.faults import FaultScenario
from mgo_brain.health import HealthEngine
from mgo_brain.models import Event, Severity, SignalQuality, SignalReading, VehicleMode, VehicleState
from mgo_brain.rules import RulesEngine
from mgo_brain.simulator import MGOSimulator


def reading(value):
    return SignalReading(value=value, quality=SignalQuality.GOOD, source="test")


def codes(state):
    return {event.code for event in RulesEngine().evaluate(state)}


def test_fault_catalog_has_expected_scenarios():
    sim = MGOSimulator()
    names = {item["name"] for item in sim.faults.catalog()}
    assert {
        "weak_battery", "starter_degradation", "glow_fault",
        "alternator_undercharge", "alternator_overvoltage",
        "low_oil_pressure", "overheating", "cvt_slip", "cvt_overheat",
    } <= names


def test_weak_battery_is_detected_at_rest_and_crank():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.WEAK_BATTERY)
    assert "BATTERY_LOW_REST" in codes(sim.snapshot_at(4.5))
    assert "CRANK_VOLTAGE_LOW" in codes(sim.snapshot_at(10.5))


def test_starter_degradation_produces_slow_crank():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.STARTER_DEGRADATION)
    state = sim.snapshot_at(11.0)
    assert state.mode == VehicleMode.CRANKING
    assert state.value("engine.rpm") < 200
    assert "STARTER_SLOW_CRANK" in codes(state)


def test_glow_fault_is_detected():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.GLOW_FAULT)
    state = sim.snapshot_at(9.0)
    assert state.mode == VehicleMode.PREHEAT
    assert "GLOW_CURRENT_LOW" in codes(state)


def test_alternator_faults_are_detected():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.ALTERNATOR_UNDERCHARGE)
    assert "CHARGING_LOW" in codes(sim.snapshot_at(20.0))
    sim.faults.clear()
    sim.faults.enable(FaultScenario.ALTERNATOR_OVERVOLTAGE)
    assert "CHARGING_OVERVOLTAGE" in codes(sim.snapshot_at(20.0))


def test_oil_pressure_and_overheat_faults_are_detected():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.LOW_OIL_PRESSURE)
    oil_codes = codes(sim.snapshot_at(20.0))
    assert "LOW_OIL_PRESSURE" in oil_codes
    assert "OEM_OIL_PRESSURE_WARNING" in oil_codes

    sim.faults.clear()
    sim.faults.enable(FaultScenario.OVERHEATING)
    hot_codes = codes(sim.snapshot_at(50.0))
    assert "OEM_OVERHEAT_WARNING" in hot_codes or "HIGH_COOLANT_TEMP" in hot_codes


def test_cvt_faults_are_detected():
    sim = MGOSimulator()
    sim.faults.enable(FaultScenario.CVT_SLIP)
    state = sim.snapshot_at(20.0)
    assert state.value("transmission.cvt_ratio_deviation") >= 18
    assert "CVT_RATIO_DRIFT" in codes(state)

    sim.faults.clear()
    sim.faults.enable(FaultScenario.CVT_OVERHEAT)
    assert "CVT_OVERHEAT" in codes(sim.snapshot_at(20.0))


def test_alert_lifecycle_active_then_cleared():
    now = datetime.now(timezone.utc)
    manager = AlertManager(clear_after_s=0.5)
    event = Event(timestamp=now, severity=Severity.WATCH, code="TEST", message="test")
    transitions = manager.update([event], now)
    assert transitions[0].transition == AlertStatus.ACTIVE
    assert len(manager.active()) == 1

    transitions = manager.update([], now + timedelta(seconds=0.6))
    assert transitions[0].transition == AlertStatus.CLEARED
    assert manager.active() == []
    assert manager.history()[0].status == AlertStatus.CLEARED


def test_health_engine_reports_unknown_for_uninstrumented_subsystems():
    state = VehicleState(mode=VehicleMode.IDLE, signals={
        "engine.rpm": reading(900),
        "engine.coolant_temp": reading(80),
        "engine.oil_pressure": reading(1.5),
        "electrical.battery_voltage": reading(14.1),
        "electrical.battery_current": reading(3.0),
        "transmission.cvt_ratio": reading(70.0),
        "transmission.cvt_temp_primary": reading(55.0),
        "transmission.cvt_temp_secondary": reading(52.0),
    })
    summary = HealthEngine().summary(state, [])
    by_name = {x["subsystem"]: x["status"] for x in summary["subsystems"]}
    assert by_name["ENGINE"] == "NORMAL"
    assert by_name["CVT"] == "NORMAL"
    assert by_name["ELECTRICAL"] == "NORMAL"
    assert by_name["TYRES"] == "UNKNOWN"
    assert by_name["BRAKES"] == "UNKNOWN"


def test_health_engine_escalates_from_active_alert():
    now = datetime.now(timezone.utc)
    manager = AlertManager(clear_after_s=1)
    manager.update([Event(timestamp=now, severity=Severity.CRITICAL, code="LOW_OIL_PRESSURE", message="low")], now)
    state = VehicleState(mode=VehicleMode.IDLE, signals={
        "engine.rpm": reading(900),
        "engine.coolant_temp": reading(80),
        "engine.oil_pressure": reading(0.4),
    })
    summary = HealthEngine().summary(state, manager.active())
    engine = next(x for x in summary["subsystems"] if x["subsystem"] == "ENGINE")
    assert engine["status"] == "CRITICAL"
    assert summary["overall"] == "CRITICAL"
