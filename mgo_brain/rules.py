from __future__ import annotations

from .models import Event, Severity, VehicleMode, VehicleState


class RulesEngine:
    """Deterministic local rules. No AI is involved."""

    def evaluate(self, state: VehicleState) -> list[Event]:
        out: list[Event] = []
        running = state.mode in {VehicleMode.IDLE, VehicleMode.DRIVING, VehicleMode.REVERSING, VehicleMode.ENGINE_RUNNING}
        voltage = _num(state.value("electrical.battery_voltage"))
        coolant = _num(state.value("engine.coolant_temp"))
        oil_pressure = _num(state.value("engine.oil_pressure"))
        oil_warning = bool(state.value("engine.oil_warning", False))
        overheat_warning = bool(state.value("engine.overheat_warning", False))

        if running and oil_warning:
            out.append(Event(severity=Severity.CRITICAL, code="OEM_OIL_PRESSURE_WARNING", message="OEM low-oil-pressure warning is active while engine is running."))

        if running and oil_pressure is not None and oil_pressure < 0.8:
            out.append(Event(severity=Severity.CRITICAL, code="LOW_OIL_PRESSURE", message="Measured oil pressure is below the prototype critical threshold.", data={"oil_pressure_bar": oil_pressure}))

        if overheat_warning:
            out.append(Event(severity=Severity.CRITICAL, code="OEM_OVERHEAT_WARNING", message="OEM engine overheat warning is active."))
        elif coolant is not None and coolant >= 105:
            out.append(Event(severity=Severity.ATTENTION, code="HIGH_COOLANT_TEMP", message="Coolant temperature is unusually high.", data={"coolant_c": coolant}))

        if voltage is not None:
            if running and voltage > 15.2:
                out.append(Event(severity=Severity.ATTENTION, code="CHARGING_OVERVOLTAGE", message="System voltage is above prototype charging threshold.", data={"voltage_v": voltage}))
            if running and voltage < 12.2:
                out.append(Event(severity=Severity.WATCH, code="CHARGING_LOW", message="System voltage is low while engine is running.", data={"voltage_v": voltage}))

        return out


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
