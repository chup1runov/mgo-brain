from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import mean, pstdev


@dataclass
class MetricBaseline:
    reference: list[float] = field(default_factory=list)
    rolling: deque[float] = field(default_factory=lambda: deque(maxlen=30))
    lock_after: int = 20

    def add(self, value: float) -> None:
        value = float(value)
        if len(self.reference) < self.lock_after:
            self.reference.append(value)
        self.rolling.append(value)

    @property
    def locked(self) -> bool:
        return len(self.reference) >= self.lock_after

    def stats(self) -> dict:
        def summarize(values):
            if not values:
                return None
            return {"n": len(values), "mean": mean(values), "std": pstdev(values) if len(values) > 1 else 0.0}
        return {"reference": summarize(self.reference), "rolling": summarize(list(self.rolling)), "locked": self.locked}

    def deviation(self, value: float) -> dict | None:
        if not self.reference:
            return None
        m = mean(self.reference)
        sd = pstdev(self.reference) if len(self.reference) > 1 else 0.0
        pct = ((value - m) / m * 100.0) if m else None
        z = ((value - m) / sd) if sd > 1e-9 else None
        return {"value": value, "reference_mean": m, "pct": pct, "z": z, "locked": self.locked}


class BaselineManager:
    def __init__(self):
        self.metrics = {
            "starter_duration_s": MetricBaseline(),
            "min_crank_voltage_v": MetricBaseline(),
        }

    def add_start(self, starter_duration_s: float | None, min_crank_voltage_v: float | None):
        if starter_duration_s is not None:
            self.metrics["starter_duration_s"].add(starter_duration_s)
        if min_crank_voltage_v is not None:
            self.metrics["min_crank_voltage_v"].add(min_crank_voltage_v)

    def summary(self):
        return {k: v.stats() for k, v in self.metrics.items()}
