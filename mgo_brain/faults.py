from __future__ import annotations

from enum import StrEnum


class FaultScenario(StrEnum):
    WEAK_BATTERY = "weak_battery"
    STARTER_DEGRADATION = "starter_degradation"
    GLOW_FAULT = "glow_fault"
    ALTERNATOR_UNDERCHARGE = "alternator_undercharge"
    ALTERNATOR_OVERVOLTAGE = "alternator_overvoltage"
    LOW_OIL_PRESSURE = "low_oil_pressure"
    OVERHEATING = "overheating"
    CVT_SLIP = "cvt_slip"
    CVT_OVERHEAT = "cvt_overheat"


FAULT_DESCRIPTIONS: dict[FaultScenario, str] = {
    FaultScenario.WEAK_BATTERY: "Low resting voltage and deeper crank sag.",
    FaultScenario.STARTER_DEGRADATION: "Longer crank, lower cranking RPM and higher starter current.",
    FaultScenario.GLOW_FAULT: "Abnormally low glow-plug current during preheat.",
    FaultScenario.ALTERNATOR_UNDERCHARGE: "Charging voltage remains too low with the engine running.",
    FaultScenario.ALTERNATOR_OVERVOLTAGE: "Charging voltage is excessive with the engine running.",
    FaultScenario.LOW_OIL_PRESSURE: "Measured running oil pressure falls below the safe prototype threshold.",
    FaultScenario.OVERHEATING: "Coolant temperature climbs into an over-temperature condition.",
    FaultScenario.CVT_SLIP: "Engine RPM rises relative to road speed, simulating CVT ratio drift/slip.",
    FaultScenario.CVT_OVERHEAT: "Primary and secondary CVT temperatures become abnormally high.",
}


class FaultController:
    def __init__(self):
        self._active: set[FaultScenario] = set()

    def enable(self, fault: FaultScenario | str) -> None:
        self._active.add(FaultScenario(fault))

    def disable(self, fault: FaultScenario | str) -> None:
        self._active.discard(FaultScenario(fault))

    def clear(self) -> None:
        self._active.clear()

    def replace(self, faults: list[FaultScenario | str]) -> None:
        self._active = {FaultScenario(f) for f in faults}

    def active(self, fault: FaultScenario | str) -> bool:
        return FaultScenario(fault) in self._active

    def names(self) -> list[str]:
        return sorted(f.value for f in self._active)

    def catalog(self) -> list[dict[str, str | bool]]:
        return [
            {
                "name": fault.value,
                "description": FAULT_DESCRIPTIONS[fault],
                "active": fault in self._active,
            }
            for fault in FaultScenario
        ]
