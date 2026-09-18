from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone

from .faults import FaultController, FaultScenario
from .models import SignalQuality, SignalReading, VehicleState
from .state_machine import infer_mode


BASE_DURATIONS = {
    "off": 4.0,
    "acc": 2.0,
    "ignition": 2.0,
    "glow": 2.0,
    "crank": 1.4,
    "idle": 4.6,
    "drive": 41.0,
    "cooldown": 4.0,
    "off_end": 6.0,
}


class MGOSimulator:
    """Synthetic Progress-ACT-like drive cycle with injectable faults.

    This is a deterministic diagnostic test bench, not a physical model of the car.
    """

    source = "simulator"

    def __init__(self, hz: float = 5.0):
        self.hz = hz
        self.t0 = time.monotonic()
        self._soc = 82.0
        self.faults = FaultController()

    async def stream(self):
        while True:
            yield self.snapshot()
            await asyncio.sleep(1.0 / self.hz)

    def snapshot(self) -> VehicleState:
        elapsed = time.monotonic() - self.t0
        cycle = self.cycle_length()
        return self.snapshot_at(elapsed % cycle)

    def snapshot_at(self, t: float) -> VehicleState:
        phase, phase_t = self._phase_at(t)
        speed, rpm, gear = self._motion(phase, phase_t)

        running = rpm >= 400
        glow = phase == "glow"
        starter = phase == "crank"
        ignition = phase in {"ignition", "glow", "crank", "idle", "drive", "cooldown"}
        acc = ignition or phase == "acc"

        ambient = 8.0 + 0.4 * math.sin(t / 10.0)
        weak_battery = self.faults.active(FaultScenario.WEAK_BATTERY)
        starter_fault = self.faults.active(FaultScenario.STARTER_DEGRADATION)
        glow_fault = self.faults.active(FaultScenario.GLOW_FAULT)
        undercharge = self.faults.active(FaultScenario.ALTERNATOR_UNDERCHARGE)
        overvoltage = self.faults.active(FaultScenario.ALTERNATOR_OVERVOLTAGE)
        low_oil = self.faults.active(FaultScenario.LOW_OIL_PRESSURE)
        overheating = self.faults.active(FaultScenario.OVERHEATING)
        cvt_slip = self.faults.active(FaultScenario.CVT_SLIP)
        cvt_overheat = self.faults.active(FaultScenario.CVT_OVERHEAT)

        if cvt_slip and speed > 2:
            rpm *= 1.20

        if running:
            drive_age = max(0.0, t - 9.0)
            coolant = min(84.0, 20.0 + drive_age * 1.8)
            if t > 45:
                coolant = 82.0 + 2.0 * math.sin(t)
            if overheating:
                coolant = min(116.0, 90.0 + max(0.0, drive_age - 12.0) * 1.15)

            oil_temp = min(90.0, 18.0 + drive_age * 1.65)
            oil_pressure = max(1.35, 4.2 - oil_temp * 0.025 + rpm / 3000.0)
            if low_oil:
                oil_pressure = 0.45 + 0.04 * math.sin(t)

            voltage = 14.15 + 0.08 * math.sin(t * 1.7)
            current = 7.0 if t < 18 else 2.0 + 1.5 * math.sin(t / 3)
            if undercharge:
                voltage = 11.95 + 0.05 * math.sin(t)
                current = -4.0
            if overvoltage:
                voltage = 15.65 + 0.08 * math.sin(t)
                current = 9.0
        elif starter:
            coolant = 18.5
            oil_temp = 18.5
            oil_pressure = 0.15
            if weak_battery:
                voltage = 8.75 + 0.05 * math.sin(t * 7)
            elif starter_fault:
                voltage = 9.10 + 0.06 * math.sin(t * 7)
            else:
                voltage = 10.35 + 0.05 * math.sin(t * 7)
            current = -195.0 if starter_fault else -145.0
        elif glow:
            coolant = 18.0
            oil_temp = 18.0
            oil_pressure = 0.0
            voltage = 10.95 if weak_battery else 11.65
            current = -12.0 if glow_fault else -28.0
        else:
            coolant = 18.0
            oil_temp = 18.0
            oil_pressure = 0.0
            voltage = 11.82 if weak_battery else 12.62
            current = -0.08 if phase in {"off", "off_end"} else -1.2

        glow_current = 0.0
        if glow:
            glow_current = 8.0 if glow_fault else 28.0
        starter_current = abs(current) if starter else 0.0

        cvt_ratio = rpm / speed if speed > 2 else None
        normal_ratio = None
        ratio_deviation = None
        if speed > 2:
            normal_rpm = self._motion(phase, phase_t, ignore_faults=True)[1]
            normal_ratio = normal_rpm / speed if speed else None
            if normal_ratio:
                ratio_deviation = (cvt_ratio / normal_ratio - 1.0) * 100.0

        primary_temp = 46.0 + (speed / 45.0) * 18.0 if running else ambient
        secondary_temp = 42.0 + (speed / 45.0) * 16.0 if running else ambient
        if cvt_overheat and running:
            primary_temp = 112.0
            secondary_temp = 106.0

        fuel = max(8.0, 68.0 - (time.monotonic() - self.t0) / 1800.0)
        if weak_battery:
            self._soc = min(self._soc, 38.0)
        self._soc = max(0.0, min(100.0, self._soc + current * (1 / self.hz) / 3600 / 42 * 100))

        oil_warning = low_oil and running and oil_pressure < 0.5
        overheat_warning = overheating and running and coolant >= 109.0

        values = {
            "electrical.acc": (acc, None),
            "electrical.ignition": (ignition, None),
            "vehicle.speed": (round(speed, 2), "km/h"),
            "vehicle.speed_gps": (round(max(0.0, speed * 0.974), 2), "km/h"),
            "engine.rpm": (round(rpm, 0), "rpm"),
            "engine.coolant_temp": (round(coolant, 1), "°C"),
            "engine.oil_temp": (round(oil_temp, 1), "°C"),
            "engine.oil_pressure": (round(oil_pressure, 2), "bar"),
            "engine.oil_warning": (oil_warning, None),
            "engine.overheat_warning": (overheat_warning, None),
            "engine.glow_active": (glow, None),
            "engine.glow_current": (round(glow_current, 1), "A"),
            "engine.starter_active": (starter, None),
            "engine.starter_current": (round(starter_current, 1), "A"),
            "electrical.battery_voltage": (round(voltage, 2), "V"),
            "electrical.battery_current": (round(current, 1), "A"),
            "electrical.battery_soc": (round(self._soc, 1), "%"),
            "electrical.alternator_voltage": (round(voltage, 2) if running else None, "V"),
            "transmission.gear": (gear, None),
            "transmission.cvt_ratio": (round(cvt_ratio, 2) if cvt_ratio else None, "rpm/(km/h)"),
            "transmission.cvt_ratio_deviation": (round(ratio_deviation, 1) if ratio_deviation is not None else None, "%"),
            "transmission.cvt_temp_primary": (round(primary_temp, 1), "°C"),
            "transmission.cvt_temp_secondary": (round(secondary_temp, 1), "°C"),
            "fuel.level": (round(fuel, 1), "%"),
            "body.driver_door": (phase == "off" and phase_t < 2.0, None),
            "controls.brake": (phase == "cooldown", None),
            "controls.parking_brake": (phase in {"off", "acc", "ignition", "glow"}, None),
            "environment.ambient_temp": (round(ambient, 1), "°C"),
        }
        now = datetime.now(timezone.utc)
        signals = {
            name: SignalReading(value=value, unit=unit, quality=SignalQuality.GOOD, source=self.source, timestamp=now)
            for name, (value, unit) in values.items()
        }
        state = VehicleState(timestamp=now, signals=signals)
        state.mode = infer_mode(state)
        return state

    def cycle_length(self) -> float:
        return sum(duration for _, duration in self._timeline())

    def _timeline(self) -> list[tuple[str, float]]:
        durations = dict(BASE_DURATIONS)
        if self.faults.active(FaultScenario.STARTER_DEGRADATION):
            durations["crank"] = 3.2
        return list(durations.items())

    def _phase_at(self, t: float) -> tuple[str, float]:
        cursor = 0.0
        for phase, duration in self._timeline():
            if t < cursor + duration:
                return phase, t - cursor
            cursor += duration
        return "off_end", 0.0

    def _motion(self, phase: str, phase_t: float, ignore_faults: bool = False):
        if phase == "crank":
            if not ignore_faults and self.faults.active(FaultScenario.STARTER_DEGRADATION):
                return 0.0, 165.0, "N"
            return 0.0, 285.0, "N"
        if phase in {"idle", "cooldown"}:
            return 0.0, 930.0 + 25 * math.sin(phase_t * 2), "N" if phase == "idle" else "D"
        if phase != "drive":
            return 0.0, 0.0, "N"

        x = phase_t
        if x < 9:
            speed = min(43.0, x * 5.0)
        elif x < 29:
            speed = 42.0 + 2.0 * math.sin(x / 3)
        else:
            speed = max(0.0, 43.0 - (x - 29) * 3.6)
        rpm = 900 + speed * 48 + (350 if x < 9 else 0) + 80 * math.sin(x * 1.2)
        return speed, rpm, "D"
