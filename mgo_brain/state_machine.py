from .models import VehicleMode, VehicleState


def infer_mode(state: VehicleState) -> VehicleMode:
    rpm = float(state.value("engine.rpm", 0) or 0)
    speed = float(state.value("vehicle.speed", 0) or 0)
    starter = bool(state.value("engine.starter_active", False))
    glow = bool(state.value("engine.glow_active", False))
    ignition = bool(state.value("electrical.ignition", False))
    acc = bool(state.value("electrical.acc", False))
    gear = str(state.value("transmission.gear", "N"))

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
