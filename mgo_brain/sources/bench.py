from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate
from .mux import SourceMux


BENCH_SCENARIOS = (
    "normal",
    "weak_battery",
    "undercharge",
    "low_oil_pressure",
    "overheat",
    "cvt_overheat",
    "sensorhub_dropout",
)


@dataclass(frozen=True)
class BenchPhase:
    name: str
    start: float
    end: float


PHASES = (
    BenchPhase("off", 0.0, 2.0),
    BenchPhase("acc", 2.0, 3.0),
    BenchPhase("ignition", 3.0, 4.0),
    BenchPhase("preheat", 4.0, 5.0),
    BenchPhase("crank", 5.0, 6.0),
    BenchPhase("idle", 6.0, 9.0),
    BenchPhase("drive", 9.0, 20.0),
    BenchPhase("cooldown", 20.0, 22.0),
    BenchPhase("off_end", 22.0, 24.0),
)

CYCLE_S = 24.0


class BenchController:
    """Shared deterministic virtual vehicle used by independent bench sources."""

    def __init__(
        self,
        *,
        scenario: str = "normal",
        time_scale: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        if scenario not in BENCH_SCENARIOS:
            raise ValueError(f"Unknown bench scenario: {scenario}")
        if time_scale <= 0:
            raise ValueError("time_scale must be > 0")
        self._scenario = scenario
        self.time_scale = float(time_scale)
        self.clock = clock
        self.started = clock()
        self.wall_started = datetime.now(timezone.utc)

    @property
    def scenario(self) -> str:
        return self._scenario

    def set_scenario(self, scenario: str) -> None:
        if scenario not in BENCH_SCENARIOS:
            raise ValueError(f"Unknown bench scenario: {scenario}")
        self._scenario = scenario

    def reset(self) -> None:
        self.started = self.clock()
        self.wall_started = datetime.now(timezone.utc)

    def virtual_elapsed(self) -> float:
        return max(0.0, (self.clock() - self.started) * self.time_scale)

    def cycle_time(self, elapsed: float | None = None) -> float:
        value = self.virtual_elapsed() if elapsed is None else float(elapsed)
        return value % CYCLE_S

    def phase(self, elapsed: float | None = None) -> str:
        t = self.cycle_time(elapsed)
        for phase in PHASES:
            if phase.start <= t < phase.end:
                return phase.name
        return "off"

    def status(self) -> dict:
        return {
            "active": True,
            "scenario": self.scenario,
            "available_scenarios": list(BENCH_SCENARIOS),
            "time_scale": self.time_scale,
            "cycle_s": CYCLE_S,
            "phase": self.phase(),
        }

    def update_for(self, channel: str, elapsed: float | None = None) -> SourceUpdate | None:
        t = self.cycle_time(elapsed)
        phase = self.phase(t)
        virtual_elapsed = self.virtual_elapsed() if elapsed is None else float(elapsed)
        now = self.wall_started + timedelta(seconds=virtual_elapsed)

        if channel == "can.bfi":
            values = self._factory_can(t, phase)
        elif channel == "sensorhub.can":
            if self.scenario == "sensorhub_dropout" and 11.0 <= t < 18.0:
                return None
            values = self._sensorhub(t, phase)
        elif channel == "smartshunt":
            values = self._smartshunt(t, phase)
        elif channel == "modbus.di":
            values = self._modbus(t, phase)
        elif channel == "tpms":
            values = self._tpms(t, phase)
        elif channel == "gnss":
            values = self._gnss(t, phase)
        else:
            raise KeyError(channel)

        return SourceUpdate(
            source=channel,
            timestamp=now,
            signals={
                name: SignalReading(
                    value=value,
                    unit=unit,
                    quality=SignalQuality.GOOD,
                    source=source,
                    timestamp=now,
                )
                for name, (value, unit, source) in values.items()
            },
        )

    def _kinematics(self, t: float, phase: str) -> tuple[float, float, str]:
        if phase == "crank":
            return 0.0, 285.0, "N"
        if phase in {"idle", "cooldown"}:
            return 0.0, 930.0, "N" if phase == "idle" else "D"
        if phase != "drive":
            return 0.0, 0.0, "N"

        x = t - 9.0
        if x < 3.0:
            speed = x * 12.0
        elif x < 8.0:
            speed = 36.0 + 6.0 * math.sin((x - 3.0) / 1.7)
        else:
            speed = max(0.0, 40.0 - (x - 8.0) * 13.0)
        rpm = 950.0 + speed * 48.0 + (300.0 if x < 3.0 else 0.0)
        return max(0.0, speed), max(0.0, rpm), "D"

    def _factory_can(self, t: float, phase: str):
        speed, rpm, gear = self._kinematics(t, phase)
        acc = phase not in {"off", "off_end"}
        ignition = phase in {"ignition", "preheat", "crank", "idle", "drive", "cooldown"}
        glow = phase == "preheat"
        starter = phase == "crank"
        return {
            "electrical.acc": (acc, None, "digital.oem"),
            "electrical.ignition": (ignition, None, "digital.oem"),
            "vehicle.speed": (round(speed, 2), "km/h", "can.bfi"),
            "engine.rpm": (round(rpm, 0), "rpm", "can.bfi"),
            "transmission.gear": (gear, None, "can.bfi"),
            "fuel.level": (63.0, "%", "can.bfi"),
            "body.driver_door": (phase == "off" and t < 1.0, None, "can.bfi"),
            "engine.glow_active": (glow, None, "digital.oem"),
            "engine.starter_active": (starter, None, "digital.oem"),
            "engine.oil_warning": (
                self.scenario == "low_oil_pressure" and phase in {"idle", "drive", "cooldown"},
                None,
                "digital.oem",
            ),
            "engine.overheat_warning": (
                self.scenario == "overheat" and phase in {"drive", "cooldown"} and t >= 16.0,
                None,
                "digital.oem",
            ),
        }

    def _sensorhub(self, t: float, phase: str):
        speed, rpm, _ = self._kinematics(t, phase)
        running = phase in {"idle", "drive", "cooldown"}
        warm = max(0.0, t - 6.0)
        coolant = min(84.0, 25.0 + warm * 5.0) if running else 22.0
        oil_temp = min(88.0, 24.0 + warm * 4.7) if running else 22.0
        if self.scenario == "overheat" and running:
            coolant = min(116.0, 86.0 + max(0.0, t - 12.0) * 4.0)

        if phase == "crank":
            oil_pressure = 0.15
        elif running:
            oil_pressure = max(1.35, 3.4 - oil_temp * 0.018 + rpm / 4200.0)
        else:
            oil_pressure = 0.0
        if self.scenario == "low_oil_pressure" and running:
            oil_pressure = 0.42

        ratio = rpm / speed if speed > 2 else None
        ratio_dev = 0.8 * math.sin(t) if ratio is not None else None
        cvt_primary = 45.0 + speed * 0.45 if running else 22.0
        cvt_secondary = 42.0 + speed * 0.38 if running else 22.0
        if self.scenario == "cvt_overheat" and running:
            cvt_primary, cvt_secondary = 112.0, 106.0

        return {
            "engine.coolant_temp": (round(coolant, 1), "°C", "sensor.coolant"),
            "engine.oil_temp": (round(oil_temp, 1), "°C", "sensor.oil"),
            "engine.oil_pressure": (round(oil_pressure, 2), "bar", "sensor.oil"),
            "engine.glow_current": (28.0 if phase == "preheat" else 0.0, "A", "hall.current"),
            "engine.starter_current": (145.0 if phase == "crank" else 0.0, "A", "hall.current"),
            "transmission.cvt_ratio": (round(ratio, 2) if ratio is not None else None, "rpm/(km/h)", "derived"),
            "transmission.cvt_ratio_deviation": (
                round(ratio_dev, 2) if ratio_dev is not None else None,
                "%",
                "derived",
            ),
            "transmission.cvt_temp_primary": (round(cvt_primary, 1), "°C", "sensor.temp"),
            "transmission.cvt_temp_secondary": (round(cvt_secondary, 1), "°C", "sensor.temp"),
        }

    def _smartshunt(self, t: float, phase: str):
        running = phase in {"idle", "drive", "cooldown"}
        if phase == "crank":
            voltage, current = 10.4, -145.0
        elif phase == "preheat":
            voltage, current = 11.7, -28.0
        elif running:
            voltage, current = 14.15, 4.0
        else:
            voltage, current = 12.62, -0.1

        if self.scenario == "weak_battery":
            if phase == "crank":
                voltage = 8.8
            elif not running:
                voltage = 11.82
        if self.scenario == "undercharge" and running:
            voltage, current = 11.95, -4.0

        return {
            "electrical.battery_voltage": (voltage, "V", "smartshunt"),
            "electrical.battery_current": (current, "A", "smartshunt"),
            "electrical.battery_soc": (38.0 if self.scenario == "weak_battery" else 82.0, "%", "smartshunt"),
            "electrical.alternator_voltage": (voltage if running else None, "V", "smartshunt"),
        }

    def _modbus(self, t: float, phase: str):
        braking = phase == "cooldown"
        parking = phase in {"off", "acc", "ignition", "preheat", "off_end"}
        return {
            "controls.brake": (braking, None, "digital.oem"),
            "controls.parking_brake": (parking, None, "digital.oem"),
            "brakes.fl.temp": (46.0 if braking else 31.0, "°C", "modbus.ai"),
            "brakes.fr.temp": (45.0 if braking else 31.0, "°C", "modbus.ai"),
            "brakes.rl.temp": (36.0 if braking else 28.0, "°C", "modbus.ai"),
            "brakes.rr.temp": (35.0 if braking else 28.0, "°C", "modbus.ai"),
        }

    def _tpms(self, t: float, phase: str):
        return {
            "tyres.fl.pressure": (1.62, "bar", "tpms"),
            "tyres.fr.pressure": (1.61, "bar", "tpms"),
            "tyres.rl.pressure": (1.58, "bar", "tpms"),
            "tyres.rr.pressure": (1.59, "bar", "tpms"),
            "tyres.fl.temp": (25.0, "°C", "tpms"),
            "tyres.fr.temp": (25.5, "°C", "tpms"),
            "tyres.rl.temp": (24.0, "°C", "tpms"),
            "tyres.rr.temp": (24.5, "°C", "tpms"),
        }

    def _gnss(self, t: float, phase: str):
        speed, _, _ = self._kinematics(t, phase)
        return {
            "vehicle.speed_gps": (round(speed * 0.985, 2), "km/h", "gnss"),
            "position.latitude": (57.7000, "deg", "gnss"),
            "position.longitude": (12.0000, "deg", "gnss"),
            "position.altitude": (35.0, "m", "gnss"),
            "motion.accel_x": (0.2 if phase == "drive" else 0.0, "m/s²", "autopi.imu"),
            "motion.accel_y": (0.0, "m/s²", "autopi.imu"),
            "motion.accel_z": (9.81, "m/s²", "autopi.imu"),
            "environment.ambient_temp": (8.0, "°C", "sensor.ambient"),
        }


class BenchChannelAdapter(SourceAdapter):
    def __init__(
        self,
        controller: BenchController,
        channel: str,
        *,
        hz: float,
        max_updates: int | None = None,
    ):
        self.controller = controller
        self.channel = channel
        self.name = channel
        self.hz = float(hz)
        self.max_updates = max_updates

    async def stream(self):
        emitted = 0
        interval = 1.0 / (self.hz * self.controller.time_scale)
        while self.max_updates is None or emitted < self.max_updates:
            update = self.controller.update_for(self.channel)
            if update is not None:
                emitted += 1
                yield update
            await asyncio.sleep(interval)


class BenchRigSourceAdapter(SourceMux):
    name = "bench-rig"

    def __init__(
        self,
        *,
        scenario: str = "normal",
        time_scale: float = 4.0,
        max_updates: int | None = None,
        controller: BenchController | None = None,
    ):
        self.controller = controller or BenchController(
            scenario=scenario,
            time_scale=time_scale,
        )
        adapters = [
            BenchChannelAdapter(self.controller, "can.bfi", hz=5.0, max_updates=max_updates),
            BenchChannelAdapter(self.controller, "sensorhub.can", hz=2.0, max_updates=max_updates),
            BenchChannelAdapter(self.controller, "smartshunt", hz=2.0, max_updates=max_updates),
            BenchChannelAdapter(self.controller, "modbus.di", hz=2.0, max_updates=max_updates),
            BenchChannelAdapter(self.controller, "tpms", hz=1.0, max_updates=max_updates),
            BenchChannelAdapter(self.controller, "gnss", hz=2.0, max_updates=max_updates),
        ]
        super().__init__(adapters)
        self.name = "bench-rig"

    def status(self) -> dict:
        return self.controller.status()
