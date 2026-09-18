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
        rpm = _num(state.value("engine.rpm"))
        glow_current = _num(state.value("engine.glow_current"))
        cvt_dev = _num(state.value("transmission.cvt_ratio_deviation"))
        cvt_primary = _num(state.value("transmission.cvt_temp_primary"))
        cvt_secondary = _num(state.value("transmission.cvt_temp_secondary"))

        if state.mode in {VehicleMode.OFF, VehicleMode.ACC, VehicleMode.IGNITION} and voltage is not None and voltage < 12.0:
            out.append(Event(severity=Severity.WATCH, code="BATTERY_LOW_REST", message="Resting battery voltage is low.", data={"voltage_v": voltage}))

        if state.mode == VehicleMode.CRANKING:
            if voltage is not None and voltage < 9.3:
                out.append(Event(severity=Severity.ATTENTION, code="CRANK_VOLTAGE_LOW", message="Battery voltage sags excessively during cranking.", data={"voltage_v": voltage}))
            if rpm is not None and rpm < 200:
                out.append(Event(severity=Severity.ATTENTION, code="STARTER_SLOW_CRANK", message="Cranking RPM is abnormally low.", data={"rpm": rpm}))

        if state.mode == VehicleMode.PREHEAT and glow_current is not None and glow_current < 15:
            out.append(Event(severity=Severity.ATTENTION, code="GLOW_CURRENT_LOW", message="Glow-plug current is abnormally low during preheat.", data={"glow_current_a": glow_current}))

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

        if running and cvt_dev is not None and abs(cvt_dev) >= 12:
            severity = Severity.ATTENTION if abs(cvt_dev) >= 18 else Severity.WATCH
            out.append(Event(severity=severity, code="CVT_RATIO_DRIFT", message="CVT RPM/speed ratio deviates from the healthy simulator baseline.", data={"deviation_pct": cvt_dev}))

        hottest_cvt = max(v for v in (cvt_primary, cvt_secondary) if v is not None) if any(v is not None for v in (cvt_primary, cvt_secondary)) else None
        if running and hottest_cvt is not None and hottest_cvt >= 100:
            severity = Severity.CRITICAL if hottest_cvt >= 120 else Severity.ATTENTION
            out.append(Event(severity=severity, code="CVT_OVERHEAT", message="CVT temperature is abnormally high.", data={"max_temp_c": hottest_cvt}))

        return out


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
