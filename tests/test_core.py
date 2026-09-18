from datetime import datetime, timezone

from mgo_brain.models import SignalReading, SignalQuality, VehicleState, VehicleMode
from mgo_brain.rules import RulesEngine
from mgo_brain.state_machine import infer_mode


def reading(v):
    return SignalReading(value=v, quality=SignalQuality.GOOD, source="test")


def test_state_machine_driving():
    s = VehicleState(signals={
        "engine.rpm": reading(2800),
        "vehicle.speed": reading(40),
        "transmission.gear": reading("D"),
        "engine.starter_active": reading(False),
        "engine.glow_active": reading(False),
        "electrical.ignition": reading(True),
    })
    assert infer_mode(s) == VehicleMode.DRIVING


def test_oil_warning_is_critical():
    s = VehicleState(mode=VehicleMode.IDLE, signals={
        "engine.oil_warning": reading(True),
        "engine.oil_pressure": reading(1.4),
        "electrical.battery_voltage": reading(14.1),
        "engine.coolant_temp": reading(80),
    })
    events = RulesEngine().evaluate(s)
    assert any(e.code == "OEM_OIL_PRESSURE_WARNING" and e.severity.value == "CRITICAL" for e in events)
