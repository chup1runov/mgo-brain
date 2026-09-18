from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field

from .models import Event, Severity


class AlertStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLEARED = "CLEARED"


class AlertRecord(BaseModel):
    code: str
    severity: Severity
    message: str
    data: dict = Field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    active_since: datetime
    last_seen: datetime
    cleared_at: datetime | None = None
    occurrences: int = 1


class AlertTransition(BaseModel):
    transition: AlertStatus
    alert: AlertRecord


class AlertManager:
    """Tracks alert activation/clearing independently from event persistence."""

    def __init__(self, clear_after_s: float = 1.0, history_limit: int = 200):
        self.clear_after = timedelta(seconds=clear_after_s)
        self._active: dict[str, AlertRecord] = {}
        self._history: deque[AlertRecord] = deque(maxlen=history_limit)

    def update(self, events: list[Event], now: datetime) -> list[AlertTransition]:
        transitions: list[AlertTransition] = []
        incoming = {event.code: event for event in events}

        for code, event in incoming.items():
            current = self._active.get(code)
            if current is None:
                current = AlertRecord(
                    code=event.code,
                    severity=event.severity,
                    message=event.message,
                    data=dict(event.data),
                    active_since=now,
                    last_seen=now,
                )
                self._active[code] = current
                transitions.append(AlertTransition(transition=AlertStatus.ACTIVE, alert=current.model_copy(deep=True)))
            else:
                current.last_seen = now
                current.occurrences += 1
                current.severity = event.severity
                current.message = event.message
                current.data = dict(event.data)

        for code, current in list(self._active.items()):
            if code in incoming:
                continue
            if now - current.last_seen >= self.clear_after:
                current.status = AlertStatus.CLEARED
                current.cleared_at = now
                self._history.appendleft(current.model_copy(deep=True))
                transitions.append(AlertTransition(transition=AlertStatus.CLEARED, alert=current.model_copy(deep=True)))
                del self._active[code]

        return transitions

    def active(self) -> list[AlertRecord]:
        return sorted(self._active.values(), key=lambda a: a.active_since, reverse=True)

    def history(self, limit: int = 50) -> list[AlertRecord]:
        return list(self._history)[:limit]

    def snapshot(self) -> dict:
        return {
            "active": [a.model_dump(mode="json") for a in self.active()],
            "history": [a.model_dump(mode="json") for a in self.history()],
        }
