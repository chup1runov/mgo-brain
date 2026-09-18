from .models import SignalQuality, VehicleMode, VehicleState


UNUSABLE = {SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID}


def _value(state: VehicleState, name: str, default=None):
    reading = state.signals.get(name)
    if reading is None or reading.quality in UNUSABLE:
        return default
    return reading.value


def infer_mode(state: VehicleState) -> VehicleMode:
    rpm = float(_value(state, "engine.rpm", 0) or 0)
    speed = float(_value(state, "vehicle.speed", 0) or 0)
    starter = bool(_value(state, "engine.starter_active", False))
    glow = bool(_value(state, "engine.glow_active", False))
    ignition = bool(_value(state, "electrical.ignition", False))
    acc = bool(_value(state, "electrical.acc", False))
    gear = str(_value(state, "transmission.gear", "N"))

    if starter:
        return VehicleMode.CRANKING
    if glow and rpm < 300:
        return VehicleMode.PREHEAT
    if rpm >= 400:
        if speed > 0.7:
            return VehicleMode.REVERSING if gear == "R" else VehicleMode.DRIVING
        return VehicleMode.IDLE
    if ignition:
        return VehicleMode.IGNITION
    if acc:
        return VehicleMode.ACC
    return VehicleMode.OFF
