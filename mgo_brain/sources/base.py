from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Mapping

from pydantic import BaseModel, Field

from ..models import SignalReading


class SourceUpdate(BaseModel):
    """A partial normalized update from one physical or simulated source."""

    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signals: dict[str, SignalReading] = Field(default_factory=dict)


class SourceAdapter(ABC):
    """Read-only source contract.

    Adapters emit canonical signal names. Vehicle-control/transmit methods do not
    belong in this interface.
    """

    name: str

    @abstractmethod
    async def stream(self) -> AsyncIterator[SourceUpdate]:
        raise NotImplementedError

    async def close(self) -> None:
        return None


def update_from_values(
    source: str,
    values: Mapping[str, tuple[object, str | None]],
    *,
    timestamp: datetime | None = None,
):
    from ..models import SignalQuality

    ts = timestamp or datetime.now(timezone.utc)
    return SourceUpdate(
        source=source,
        timestamp=ts,
        signals={
            name: SignalReading(
                value=value,
                unit=unit,
                quality=SignalQuality.GOOD,
                source=source,
                timestamp=ts,
            )
            for name, (value, unit) in values.items()
        },
    )
