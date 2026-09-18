from __future__ import annotations

from .alerts import AlertRecord
from .models import HealthItem, Severity, SignalQuality, VehicleState


STATUS_ORDER = {"UNKNOWN": -1, "NORMAL": 0, "WATCH": 1, "ATTENTION": 2, "CRITICAL": 3}

SUBSYSTEM_CODES: dict[str, set[str]] = {
    "ENGINE": {
        "OEM_OIL_PRESSURE_WARNING", "LOW_OIL_PRESSURE", "OEM_OVERHEAT_WARNING",
        "HIGH_COOLANT_TEMP", "GLOW_CURRENT_LOW", "STARTER_SLOW_CRANK",
    },
    "CVT": {"CVT_RATIO_DRIFT", "CVT_OVERHEAT"},
    "ELECTRICAL": {
        "BATTERY_LOW_REST", "CRANK_VOLTAGE_LOW", "STARTER_SLOW_CRANK",
        "GLOW_CURRENT_LOW", "CHARGING_LOW", "CHARGING_OVERVOLTAGE",
    },
    "TYRES": {"TYRE_PRESSURE_LOW", "TYRE_TEMP_HIGH"},
    "BRAKES": {"BRAKE_TEMP_IMBALANCE", "BRAKE_TEMP_HIGH"},
}

READINESS_SIGNALS: dict[str, tuple[str, ...]] = {
    "ENGINE": ("engine.rpm", "engine.coolant_temp", "engine.oil_pressure"),
    "CVT": ("transmission.cvt_ratio", "transmission.cvt_temp_primary", "transmission.cvt_temp_secondary"),
    "ELECTRICAL": ("electrical.battery_voltage", "electrical.battery_current"),
    "TYRES": ("tyres.fl.pressure", "tyres.fr.pressure", "tyres.rl.pressure", "tyres.rr.pressure"),
    "BRAKES": ("brakes.fl.temp", "brakes.fr.temp", "brakes.rl.temp", "brakes.rr.temp"),
}

SEVERITY_STATUS = {
    Severity.INFO: "NORMAL",
    Severity.WATCH: "WATCH",
    Severity.ATTENTION: "ATTENTION",
    Severity.CRITICAL: "CRITICAL",
}

UNUSABLE_QUALITY = {SignalQuality.STALE, SignalQuality.MISSING, SignalQuality.INVALID}


def _usable(state: VehicleState, name: str) -> bool:
    reading = state.signals.get(name)
    return (
        reading is not None
        and reading.value is not None
        and reading.quality not in UNUSABLE_QUALITY
    )


class HealthEngine:
    def evaluate(self, state: VehicleState, alerts: list[AlertRecord]) -> list[HealthItem]:
        items: list[HealthItem] = []
        for subsystem, codes in SUBSYSTEM_CODES.items():
            ready = all(_usable(state, name) for name in READINESS_SIGNALS[subsystem])
            relevant = [a for a in alerts if a.code in codes]
            if not ready and not relevant:
                items.append(
                    HealthItem(
                        subsystem=subsystem,
                        status="UNKNOWN",
                        reasons=["Required live sensor set is missing or stale."],
                    )
                )
                continue

            status = "NORMAL"
            reasons: list[str] = []
            for alert in relevant:
                candidate = SEVERITY_STATUS[alert.severity]
                if STATUS_ORDER[candidate] > STATUS_ORDER[status]:
                    status = candidate
                reasons.append(f"{alert.code}: {alert.message}")
            if not ready:
                reasons.append("One or more required sensor signals are stale or unavailable.")
                if STATUS_ORDER["WATCH"] > STATUS_ORDER[status]:
                    status = "WATCH"
            items.append(HealthItem(subsystem=subsystem, status=status, reasons=reasons))
        return items

    def summary(self, state: VehicleState, alerts: list[AlertRecord]) -> dict:
        items = self.evaluate(state, alerts)
        known = [item for item in items if item.status != "UNKNOWN"]
        overall = "NORMAL"
        for item in known:
            if STATUS_ORDER[item.status] > STATUS_ORDER[overall]:
                overall = item.status
        return {
            "overall": overall,
            "subsystems": [item.model_dump() for item in items],
        }
