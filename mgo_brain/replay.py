from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from .survey import CANLogRecord, parse_candump
from .sources.can import CanFrame


class CandumpReplayTransport:
    """RawCANTransport implementation backed by a recorded candump log.

    speed:
      0   -> no timing delay, useful for tests/offline decoding
      1.0 -> recorded timing
      2.0 -> twice as fast
    """

    def __init__(
        self,
        records: Iterable[CANLogRecord],
        *,
        speed: float = 0.0,
        loop: bool = False,
    ):
        if speed < 0:
            raise ValueError("speed must be >= 0")
        self.records = list(records)
        self.speed = float(speed)
        self.loop = loop
        self._index = 0
        self._previous_timestamp: float | None = None
        self.closed = False

    @classmethod
    def from_text(cls, text: str, *, speed: float = 0.0, loop: bool = False):
        records, rejected = parse_candump(text)
        if rejected:
            raise ValueError(f"candump contains {len(rejected)} unrecognized line(s)")
        return cls(records, speed=speed, loop=loop)

    @classmethod
    def from_file(cls, path: str | Path, *, speed: float = 0.0, loop: bool = False):
        return cls.from_text(
            Path(path).read_text(encoding="utf-8", errors="replace"),
            speed=speed,
            loop=loop,
        )

    @property
    def exhausted(self):
        return self.closed or (not self.loop and self._index >= len(self.records))

    async def recv(self, timeout: float | None = None) -> CanFrame | None:
        if self.closed or not self.records:
            if timeout:
                await asyncio.sleep(min(timeout, 0.01))
            return None

        if self._index >= len(self.records):
            if not self.loop:
                return None
            self._index = 0
            self._previous_timestamp = None

        record = self.records[self._index]
        self._index += 1

        if self.speed > 0 and record.timestamp is not None and self._previous_timestamp is not None:
            delay = max(0.0, record.timestamp - self._previous_timestamp) / self.speed
            if delay > 0:
                await asyncio.sleep(delay)
        if record.timestamp is not None:
            self._previous_timestamp = record.timestamp

        timestamp = (
            datetime.fromtimestamp(record.timestamp, tz=timezone.utc)
            if record.timestamp is not None
            else datetime.now(timezone.utc)
        )
        return CanFrame(
            arbitration_id=record.arbitration_id,
            data=record.data,
            timestamp=timestamp,
            is_extended_id=record.arbitration_id > 0x7FF,
        )

    async def close(self) -> None:
        self.closed = True
