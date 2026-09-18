from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev

from .models import StartEvent, TripSummary


@dataclass
class MetricBaseline:
    reference: list[float] = field(default_factory=list)
    rolling: deque[float] = field(default_factory=lambda: deque(maxlen=30))
    qualification_samples: int = 20

    def add(self, value: float, eligible_for_reference: bool = True) -> None:
        value = float(value)
        if eligible_for_reference and len(self.reference) < self.qualification_samples:
            self.reference.append(value)
        self.rolling.append(value)

    @property
    def qualified(self) -> bool:
        return len(self.reference) >= self.qualification_samples

    def stats(self) -> dict:
        def summarize(values):
            if not values:
                return None
            return {
                "n": len(values),
                "mean": mean(values),
                "std": pstdev(values) if len(values) > 1 else 0.0,
            }
        return {
            "reference": summarize(self.reference),
            "rolling": summarize(list(self.rolling)),
            "qualified": self.qualified,
            "qualification_samples": self.qualification_samples,
        }

    def deviation(self, value: float) -> dict | None:
        if not self.reference:
            return None
        value = float(value)
        m = mean(self.reference)
        sd = pstdev(self.reference) if len(self.reference) > 1 else 0.0
        pct = ((value - m) / abs(m) * 100.0) if abs(m) > 1e-12 else None
        z = ((value - m) / sd) if sd > 1e-9 else None
        z_component = min(abs(z) / 5.0, 1.0) if z is not None else 0.0
        pct_component = min(abs(pct) / 25.0, 1.0) if pct is not None else 0.0
        score = round(100.0 * max(z_component, pct_component), 1)
        if not self.qualified:
            status = "UNQUALIFIED"
        elif score >= 60:
            status = "ATTENTION"
        elif score >= 35:
            status = "WATCH"
        else:
            status = "NORMAL"
        return {
            "value": value,
            "reference_mean": m,
            "rolling_mean": mean(self.rolling) if self.rolling else None,
            "pct": pct,
            "z": z,
            "score": score,
            "status": status,
            "qualified": self.qualified,
        }


class BaselineManager:
    START_METRICS = {
        "starter_duration_s": lambda x: x.starter_duration_s,
        "min_crank_voltage_v": lambda x: x.min_crank_voltage_v,
        "cranking_rpm": lambda x: x.cranking_rpm,
    }
    TRIP_METRICS = {
        "max_coolant_c": lambda x: x.max_coolant_c,
        "max_oil_temp_c": lambda x: x.max_oil_temp_c,
        "min_oil_pressure_bar": lambda x: x.min_oil_pressure_bar,
        "avg_running_voltage_v": lambda x: x.avg_running_voltage_v,
        "avg_cvt_ratio_deviation_pct": lambda x: x.avg_cvt_ratio_deviation_pct,
        "max_cvt_temp_c": lambda x: x.max_cvt_temp_c,
    }

    def __init__(self, qualification_samples: int = 20, rolling_samples: int = 30):
        names = [*self.START_METRICS, *self.TRIP_METRICS]
        self.metrics = {
            name: MetricBaseline(rolling=deque(maxlen=rolling_samples), qualification_samples=qualification_samples)
            for name in names
        }

    def add_start_event(self, start: StartEvent) -> None:
        for name, getter in self.START_METRICS.items():
            value = getter(start)
            if value is not None:
                self.metrics[name].add(value, eligible_for_reference=start.baseline_eligible)

    def add_start(self, starter_duration_s: float | None, min_crank_voltage_v: float | None, eligible_for_reference: bool = True):
        if starter_duration_s is not None:
            self.metrics["starter_duration_s"].add(starter_duration_s, eligible_for_reference)
        if min_crank_voltage_v is not None:
            self.metrics["min_crank_voltage_v"].add(min_crank_voltage_v, eligible_for_reference)

    def add_trip(self, trip: TripSummary) -> None:
        for name, getter in self.TRIP_METRICS.items():
            value = getter(trip)
            if value is not None:
                self.metrics[name].add(value, eligible_for_reference=trip.baseline_eligible)

    def trip_anomalies(self, trip: TripSummary) -> list[dict]:
        out = []
        for name, getter in self.TRIP_METRICS.items():
            value = getter(trip)
            if value is None:
                continue
            deviation = self.metrics[name].deviation(value)
            if deviation is not None:
                out.append({"metric": name, **deviation})
        return out

    def start_anomalies(self, start: StartEvent) -> list[dict]:
        out = []
        for name, getter in self.START_METRICS.items():
            value = getter(start)
            if value is None:
                continue
            deviation = self.metrics[name].deviation(value)
            if deviation is not None:
                out.append({"metric": name, **deviation})
        return out

    def rebuild(self, starts: list[dict], trips: list[dict]) -> None:
        for row in reversed(starts):
            self.add_start_event(StartEvent.model_validate(row))
        for row in reversed(trips):
            self.add_trip(TripSummary.model_validate(row))

    def summary(self):
        return {k: v.stats() for k, v in self.metrics.items()}
