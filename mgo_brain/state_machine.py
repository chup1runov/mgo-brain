from .models import VehicleMode, VehicleState


def infer_mode(state: VehicleState) -> VehicleMode:
    rpm = state.value("engine.rpm")
    speed = state.value("vehicle.speed")
    starter = state.value("engine.starter_active")
    glow = state.value("engine.glow_active")
    ignition = state.value("electrical.ignition")
    acc = state.value("electrical.acc")
    gear = state.value("transmission.gear")
    # Unknown inputs are not evidence that the engine is OFF.
    if all(x is None for x in (rpm, starter, glow, ignition, acc)):
        return VehicleMode.UNKNOWN
    if starter is True:
        return VehicleMode.CRANKING
    if glow is True and (rpm is None or rpm < 300):
        return VehicleMode.PREHEAT
    if isinstance(rpm, (float, int)) and not isinstance(rpm, bool) and rpm >= 400:
        if isinstance(speed, (float, int)) and speed > 0.7:
            return VehicleMode.REVERSING if gear == "R" else VehicleMode.DRIVING
        return VehicleMode.IDLE if speed is not None else VehicleMode.ENGINE_RUNNING
    if ignition is True:
        return VehicleMode.IGNITION
    if acc is True:
        return VehicleMode.ACC
    return VehicleMode.OFF if ignition is False or rpm == 0 else VehicleMode.UNKNOWN
