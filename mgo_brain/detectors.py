from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .analytics import write_row
from .models import StartEvent, TripSummary, VehicleMode, VehicleState


@dataclass
class ActiveStart:
    began_at: datetime
    ambient_temp_c: float | None
    battery_before_v: float | None
    glow_started_at: datetime | None = None
    glow_ended_at: datetime | None = None
    starter_started_at: datetime | None = None
    min_voltage_v: float | None = None
    rpm_samples: list[float] | None = None


class StartDetector:
    def __init__(self):
        self.active: ActiveStart | None = None
        self.last_mode = VehicleMode.OFF

    def update(self, state: VehicleState) -> StartEvent | None:
        mode = state.mode
        now = state.timestamp
        voltage = _float(state.value("electrical.battery_voltage"))
        rpm = _float(state.value("engine.rpm"))

        if self.active is None and mode in {VehicleMode.ACC, VehicleMode.IGNITION, VehicleMode.PREHEAT}:
            self.active = ActiveStart(
                began_at=now,
                ambient_temp_c=_float(state.value("environment.ambient_temp")),
                battery_before_v=voltage,
                rpm_samples=[],
            )

        if self.active:
            if mode == VehicleMode.PREHEAT and self.active.glow_started_at is None:
                self.active.glow_started_at = now
            if self.active.glow_started_at and mode != VehicleMode.PREHEAT and self.active.glow_ended_at is None:
                self.active.glow_ended_at = now
            if mode == VehicleMode.CRANKING and self.active.starter_started_at is None:
                self.active.starter_started_at = now
            if mode == VehicleMode.CRANKING:
                if voltage is not None:
                    self.active.min_voltage_v = voltage if self.active.min_voltage_v is None else min(self.active.min_voltage_v, voltage)
                if rpm is not None and self.active.rpm_samples is not None:
                    self.active.rpm_samples.append(rpm)

            if mode in {VehicleMode.IDLE, VehicleMode.DRIVING, VehicleMode.REVERSING} and self.active.starter_started_at:
                glow_duration = None
                if self.active.glow_started_at and self.active.glow_ended_at:
                    glow_duration = (self.active.glow_ended_at - self.active.glow_started_at).total_seconds()
                starter_duration = (now - self.active.starter_started_at).total_seconds()
                cranking_rpm = None
                if self.active.rpm_samples:
                    cranking_rpm = sum(self.active.rpm_samples) / len(self.active.rpm_samples)
                event = StartEvent(
                    started_at=self.active.began_at,
                    ambient_temp_c=self.active.ambient_temp_c,
                    battery_before_v=self.active.battery_before_v,
                    glow_duration_s=glow_duration,
                    starter_duration_s=starter_duration,
                    min_crank_voltage_v=self.active.min_voltage_v,
                    cranking_rpm=cranking_rpm,
                    time_to_idle_s=(now - self.active.began_at).total_seconds(),
                )
                self.active = None
                self.last_mode = mode
                return event

            if mode == VehicleMode.OFF and self.last_mode != VehicleMode.CRANKING:
                self.active = None

        self.last_mode = mode
        return None


class TripDetector:
    def __init__(self, trip_dir: Path):
        self.trip_dir = Path(trip_dir)
        self.active: TripSummary | None = None
        self.file = None
        self.prev_ts: datetime | None = None
        self.speed_integral_kmh_s = 0.0
        self.voltage_sum = 0.0
        self.voltage_n = 0
        self.cvt_dev_sum = 0.0
        self.cvt_dev_n = 0

    def update(self, state: VehicleState) -> TripSummary | None:
        running = state.mode in {VehicleMode.IDLE, VehicleMode.DRIVING, VehicleMode.REVERSING}
        now = state.timestamp
        speed = _float(state.value("vehicle.speed")) or 0.0

        if running and self.active is None:
            stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
            path = self.trip_dir / f"trip_{stamp}.jsonl"
            self.file = path.open("a", encoding="utf-8")
            self.active = TripSummary(started_at=now, telemetry_path=str(path))
            self.prev_ts = now
            self.speed_integral_kmh_s = 0.0
            self.voltage_sum = self.cvt_dev_sum = 0.0
            self.voltage_n = self.cvt_dev_n = 0

        if self.active is not None:
            write_row(self.file, state)
            self.file.flush()
            if self.prev_ts:
                dt = max(0.0, (now - self.prev_ts).total_seconds())
                self.active.duration_s += dt
                self.active.distance_km += speed * dt / 3600.0
                self.speed_integral_kmh_s += speed * dt
            self.prev_ts = now

            if running:
                self.active.max_speed_kmh = max(self.active.max_speed_kmh, speed)
                self.active.max_coolant_c = _max_nullable(self.active.max_coolant_c, _float(state.value("engine.coolant_temp")))
                self.active.max_oil_temp_c = _max_nullable(self.active.max_oil_temp_c, _float(state.value("engine.oil_temp")))
                self.active.min_oil_pressure_bar = _min_nullable(self.active.min_oil_pressure_bar, _float(state.value("engine.oil_pressure")))
                cvt_peak = _max_nullable(_float(state.value("transmission.cvt_temp_primary")), _float(state.value("transmission.cvt_temp_secondary")))
                self.active.max_cvt_temp_c = _max_nullable(self.active.max_cvt_temp_c, cvt_peak)

                voltage = _float(state.value("electrical.battery_voltage"))
                if voltage is not None:
                    self.voltage_sum += voltage
                    self.voltage_n += 1
                cvt_dev = _float(state.value("transmission.cvt_ratio_deviation"))
                if cvt_dev is not None:
                    self.cvt_dev_sum += abs(cvt_dev)
                    self.cvt_dev_n += 1

            if not running:
                self.active.ended_at = now
                if self.active.duration_s > 0:
                    self.active.avg_speed_kmh = self.speed_integral_kmh_s / self.active.duration_s
                if self.voltage_n:
                    self.active.avg_running_voltage_v = self.voltage_sum / self.voltage_n
                if self.cvt_dev_n:
                    self.active.avg_cvt_ratio_deviation_pct = self.cvt_dev_sum / self.cvt_dev_n
                done = self.active
                self.file.close()
                self.file = None
                self.active = None
                self.prev_ts = None
                return done
        return None


def _float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _max_nullable(a, b):
    if b is None:
        return a
    return b if a is None else max(a, b)


def _min_nullable(a, b):
    if b is None:
        return a
    return b if a is None else min(a, b)
