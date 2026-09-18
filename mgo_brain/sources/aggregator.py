from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ..models import SignalQuality, SignalReading, VehicleState
from ..state_machine import infer_mode
from .base import SourceUpdate


QUALITY_RANK = {
    SignalQuality.INVALID: 0,
    SignalQuality.MISSING: 1,
    SignalQuality.STALE: 2,
    SignalQuality.SUSPECT: 3,
    SignalQuality.UNVERIFIED: 4,
    SignalQuality.GOOD: 5,
}


class StateAggregator:
    """Merge partial SourceUpdates into one canonical VehicleState.

    Preferred source order is honored while the preferred reading is fresh.
    Once it ages beyond stale_after_s, a fresh lower-priority fallback may take over.
    """

    def __init__(
        self,
        *,
        stale_after_s: float = 3.0,
        preferred_sources: Mapping[str, list[str] | tuple[str, ...]] | None = None,
    ):
        self.stale_after_s = float(stale_after_s)
        self.preferred_sources = {k: tuple(v) for k, v in (preferred_sources or {}).items()}
        self._signals: dict[str, SignalReading] = {}

    def apply(self, update: SourceUpdate, *, now: datetime | None = None) -> VehicleState:
        decision_time = now or update.timestamp or datetime.now(timezone.utc)
        for name, incoming in update.signals.items():
            current = self._signals.get(name)
            if current is None or self._prefer(name, incoming, current, decision_time):
                self._signals[name] = incoming.model_copy(deep=True)

        return self.snapshot(now=decision_time)

    def snapshot(self, *, now: datetime | None = None) -> VehicleState:
        ts = now or datetime.now(timezone.utc)
        signals = {
            name: self._with_age_quality(reading, ts)
            for name, reading in self._signals.items()
        }
        state = VehicleState(timestamp=ts, signals=signals)
        state.mode = infer_mode(state)
        return state

    def _prefer(
        self,
        name: str,
        incoming: SignalReading,
        current: SignalReading,
        now: datetime,
    ) -> bool:
        current_age = max(0.0, (now - current.timestamp).total_seconds())
        current_is_stale = current_age > self.stale_after_s or current.quality == SignalQuality.STALE
        incoming_is_live = incoming.quality not in {
            SignalQuality.STALE,
            SignalQuality.INVALID,
            SignalQuality.MISSING,
        }
        if current_is_stale and incoming_is_live:
            return True

        incoming_rank = QUALITY_RANK.get(incoming.quality, 0)
        current_rank = QUALITY_RANK.get(current.quality, 0)
        if incoming_rank != current_rank:
            return incoming_rank > current_rank

        pref = self.preferred_sources.get(name, ())
        if pref:
            i = _source_rank(incoming.source, pref)
            c = _source_rank(current.source, pref)
            if i != c:
                return i < c

        return incoming.timestamp >= current.timestamp

    def _with_age_quality(self, reading: SignalReading, now: datetime) -> SignalReading:
        out = reading.model_copy(deep=True)
        age_s = max(0.0, (now - out.timestamp).total_seconds())
        if age_s > self.stale_after_s and out.quality not in {SignalQuality.INVALID, SignalQuality.MISSING}:
            out.quality = SignalQuality.STALE
        return out


def _source_rank(source: str, preferred: tuple[str, ...]) -> int:
    for idx, candidate in enumerate(preferred):
        if source == candidate or source.startswith(candidate + "."):
            return idx
    return len(preferred) + 100
