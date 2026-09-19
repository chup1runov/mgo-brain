from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SignalQuality(StrEnum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    UNVERIFIED = "UNVERIFIED"


class VehicleMode(StrEnum):
    UNKNOWN = "UNKNOWN"
    OFF = "OFF"
    ACC = "ACC"
    IGNITION = "IGNITION"
    PREHEAT = "PREHEAT"
    CRANKING = "CRANKING"
    ENGINE_RUNNING = "ENGINE_RUNNING"
    IDLE = "IDLE"
    DRIVING = "DRIVING"
    REVERSING = "REVERSING"
    FAULT = "FAULT"


class Severity(StrEnum):
    INFO = "INFO"
    WATCH = "WATCH"
    ATTENTION = "ATTENTION"
    CRITICAL = "CRITICAL"


class SignalReading(BaseModel):
    value: Any = None
    unit: str | None = None
    quality: SignalQuality = SignalQuality.UNVERIFIED
    source: str = "unknown"
    timestamp: datetime = Field(default_factory=utcnow)

    @field_validator("timestamp")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Signal timestamps must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def finite_scalar(self):
        # Keep the failure as evidence without poisoning JSON, rules or baselines.
        if isinstance(self.value, float) and not math.isfinite(self.value):
            self.value = None
            self.quality = SignalQuality.INVALID
        elif self.value is not None and not isinstance(self.value, (str, int, float, bool)):
            self.value = None
            self.quality = SignalQuality.INVALID
        return self

    @property
    def usable(self) -> bool:
        return self.quality == SignalQuality.GOOD and self.value is not None and not (
            isinstance(self.value, float) and not math.isfinite(self.value)
        )


class VehicleState(BaseModel):
    timestamp: datetime = Field(default_factory=utcnow)
    mode: VehicleMode = VehicleMode.UNKNOWN
    signals: dict[str, SignalReading] = Field(default_factory=dict)

    def value(self, name: str, default: Any = None) -> Any:
        """Value for computation. Inspect .signals for raw diagnostic evidence."""
        reading = self.signals.get(name)
        return reading.value if reading is not None and reading.usable else default


class Event(BaseModel):
    id: int | None = None
    timestamp: datetime = Field(default_factory=utcnow)
    severity: Severity
    code: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class StartEvent(BaseModel):
    id: int | None = None
    started_at: datetime
    ambient_temp_c: float | None = None
    battery_before_v: float | None = None
    glow_duration_s: float | None = None
    starter_duration_s: float | None = None
    min_crank_voltage_v: float | None = None
    cranking_rpm: float | None = None
    time_to_idle_s: float | None = None
    baseline_eligible: bool = True


class TripSummary(BaseModel):
    id: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_s: float = 0.0
    distance_km: float = 0.0
    max_speed_kmh: float = 0.0
    avg_speed_kmh: float = 0.0
    max_coolant_c: float | None = None
    max_oil_temp_c: float | None = None
    min_oil_pressure_bar: float | None = None
    avg_running_voltage_v: float | None = None
    avg_cvt_ratio_deviation_pct: float | None = None
    max_cvt_temp_c: float | None = None
    diagnostic_status: str = "NORMAL"
    baseline_eligible: bool = True
    telemetry_path: str | None = None


class PostTripReport(BaseModel):
    generated_at: datetime = Field(default_factory=utcnow)
    trip_id: int | None = None
    status: str = "NORMAL"
    eligible_for_baseline: bool = True
    metrics: dict[str, Any] = Field(default_factory=dict)
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class HealthItem(BaseModel):
    subsystem: str
    status: str
    reasons: list[str] = Field(default_factory=list)


class AIContext(BaseModel):
    generated_at: datetime = Field(default_factory=utcnow)
    current_state: VehicleState
    active_alerts: list[Event]
    recent_trip: TripSummary | None = None
    baseline_deviations: list[dict[str, Any]] = Field(default_factory=list)
    maintenance_due: list[dict[str, Any]] = Field(default_factory=list)
