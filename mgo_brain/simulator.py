from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone

from .models import SignalQuality, SignalReading, VehicleState
from .state_machine import infer_mode


class MGOSimulator:
    """Synthetic Progress-ACT-like drive cycle. It is not a physics model."""

    source = "simulator"

    def __init__(self, hz: float = 5.0):
        self.hz = hz
        self.t0 = time.monotonic()
        self._soc = 82.0

    async def stream(self):
        while True:
            yield self.snapshot()
            await asyncio.sleep(1.0 / self.hz)

    def snapshot(self) -> VehicleState:
        t = (time.monotonic() - self.t0) % 67.0
        phase = _phase(t)
        speed, rpm, gear = _motion(t, phase)
        running = rpm >= 400
        glow = phase == "glow"
        starter = phase == "crank"
        ignition = phase in {"ignition", "glow", "crank", "idle", "drive", "cooldown"}
        acc = ignition or phase == "acc"

        ambient = 8.0 + 0.4 * math.sin(t / 10.0)
        if running:
            coolant = min(84.0, 20.0 + (t - 9.0) * 1.8) if t < 45 else 82 + 2 * math.sin(t)
            oil_temp = min(90.0, 18.0 + max(0.0, t - 9.0) * 1.65)
            oil_pressure = max(1.35, 4.2 - oil_temp * 0.025 + rpm / 3000.0)
            voltage = 14.15 + 0.08 * math.sin(t * 1.7)
            current = 7.0 if t < 18 else 2.0 + 1.5 * math.sin(t / 3)
        elif starter:
            coolant = 18.5
            oil_temp = 18.5
            oil_pressure = 0.15
            voltage = 10.35 + 0.05 * math.sin(t * 7)
            current = -145.0
        elif glow:
            coolant = 18.0
            oil_temp = 18.0
            oil_pressure = 0.0
            voltage = 11.65
            current = -28.0
        else:
            coolant = 18.0
            oil_temp = 18.0
            oil_pressure = 0.0
            voltage = 12.62
            current = -0.08 if phase == "off" else -1.2

        cvt_ratio = rpm / speed if speed > 2 else None
        fuel = max(8.0, 68.0 - (time.monotonic() - self.t0) / 1800.0)
        self._soc = max(0.0, min(100.0, self._soc + current * (1 / self.hz) / 3600 / 42 * 100))

        values = {
            "electrical.acc": (acc, None),
            "electrical.ignition": (ignition, None),
            "vehicle.speed": (round(speed, 2), "km/h"),
            "vehicle.speed_gps": (round(max(0.0, speed * 0.974), 2), "km/h"),
            "engine.rpm": (round(rpm, 0), "rpm"),
            "engine.coolant_temp": (round(coolant, 1), "°C"),
            "engine.oil_temp": (round(oil_temp, 1), "°C"),
            "engine.oil_pressure": (round(oil_pressure, 2), "bar"),
            "engine.oil_warning": (False, None),
            "engine.overheat_warning": (False, None),
            "engine.glow_active": (glow, None),
            "engine.starter_active": (starter, None),
            "electrical.battery_voltage": (round(voltage, 2), "V"),
            "electrical.battery_current": (round(current, 1), "A"),
            "electrical.battery_soc": (round(self._soc, 1), "%"),
            "transmission.gear": (gear, None),
            "transmission.cvt_ratio": (round(cvt_ratio, 2) if cvt_ratio else None, "rpm/(km/h)"),
            "fuel.level": (round(fuel, 1), "%"),
            "body.driver_door": (phase == "off" and t < 2.0, None),
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


def _phase(t: float) -> str:
    if t < 4: return "off"
    if t < 6: return "acc"
    if t < 8: return "ignition"
    if t < 10: return "glow"
    if t < 11.4: return "crank"
    if t < 16: return "idle"
    if t < 57: return "drive"
    if t < 61: return "cooldown"
    return "off"


def _motion(t: float, phase: str):
    if phase == "crank":
        return 0.0, 285.0, "N"
    if phase in {"idle", "cooldown"}:
        return 0.0, 930.0 + 25 * math.sin(t * 2), "N" if phase == "idle" else "D"
    if phase != "drive":
        return 0.0, 0.0, "N"
    x = t - 16
    if x < 9:
        speed = min(43.0, x * 5.0)
    elif x < 29:
        speed = 42.0 + 2.0 * math.sin(x / 3)
    else:
        speed = max(0.0, 43.0 - (x - 29) * 3.6)
    rpm = 900 + speed * 48 + (350 if x < 9 else 0) + 80 * math.sin(t * 1.2)
    return speed, rpm, "D"
