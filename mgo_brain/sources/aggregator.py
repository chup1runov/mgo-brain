from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timezone

from ..models import SignalQuality, SignalReading, VehicleState
from ..state_machine import infer_mode
from .base import SourceUpdate

QUALITY_RANK = {SignalQuality.INVALID:0, SignalQuality.MISSING:1, SignalQuality.STALE:2,
                SignalQuality.UNVERIFIED:3, SignalQuality.SUSPECT:4, SignalQuality.GOOD:5}


class StateAggregator:
    """Latest reading per signal AND source; failures supersede old healthy readings."""
    def __init__(self, *, stale_after_s: float = 3.0,
                 preferred_sources: Mapping[str, list[str] | tuple[str, ...]] | None = None):
        if not math.isfinite(stale_after_s) or stale_after_s <= 0:
            raise ValueError("stale_after_s must be finite and positive")
        self.stale_after_s = float(stale_after_s)
        self.preferred_sources = {k:tuple(v) for k,v in (preferred_sources or {}).items()}
        self._readings: dict[str, dict[str, SignalReading]] = {}
        self._watermark: datetime | None = None

    def apply(self, update: SourceUpdate, *, now: datetime | None = None) -> VehicleState:
        decision = now or update.timestamp
        if decision.tzinfo is None:
            raise ValueError("Source time must be timezone-aware")
        decision = max(decision, self._watermark) if self._watermark else decision
        self._watermark = decision
        for name, incoming in update.signals.items():
            by_source = self._readings.setdefault(name, {})
            previous = by_source.get(incoming.source)
            if previous is not None and incoming.timestamp < previous.timestamp:
                continue
            # Do not retain an older GOOD reading when the same sensor reports failure.
            item = incoming.model_copy(deep=True)
            if item.timestamp > decision:
                item.quality = SignalQuality.INVALID
            by_source[item.source] = item
        return self.snapshot(now=decision)

    def snapshot(self, *, now: datetime | None = None) -> VehicleState:
        ts = now or datetime.now(timezone.utc)
        signals = {}
        for name, readings in self._readings.items():
            candidates = [self._with_age_quality(r, ts) for r in readings.values()]
            pref = self.preferred_sources.get(name, ())
            signals[name] = max(candidates, key=lambda r: (
                QUALITY_RANK[r.quality], -_source_rank(r.source,pref), r.timestamp
            ))
        state = VehicleState(timestamp=ts, signals=signals)
        state.mode = infer_mode(state)
        return state

    def _with_age_quality(self, reading: SignalReading, now: datetime) -> SignalReading:
        out = reading.model_copy(deep=True)
        age = (now - out.timestamp).total_seconds()
        if age < -0.001:
            out.quality = SignalQuality.INVALID
        elif age > self.stale_after_s and out.quality not in {SignalQuality.INVALID, SignalQuality.MISSING}:
            out.quality = SignalQuality.STALE
        return out


def _source_rank(source: str, preferred: tuple[str, ...]) -> int:
    for idx, candidate in enumerate(preferred):
        if source == candidate or source.startswith(candidate + "."):
            return idx
    return len(preferred) + 100
