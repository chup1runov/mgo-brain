from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from .sources.can import CanFrame, RawCANTransport


def format_candump(record: CanFrame, *, interface: str = "can0") -> str:
    timestamp = record.timestamp.timestamp()
    width = 8 if record.arbitration_id > 0x7FF else 3
    can_id = f"{record.arbitration_id:0{width}X}"
    return f"({timestamp:.6f}) {interface} {can_id}#{record.data.hex().upper()}"


@dataclass(frozen=True)
class RecordingResult:
    path: str
    frames: int
    started_at: datetime
    ended_at: datetime
    duration_s: float
    interface: str


class CANRecorder:
    """Receive-only CAN recorder writing standard candump-style text."""

    def __init__(self, transport: RawCANTransport, *, interface: str = "can0"):
        self.transport = transport
        self.interface = interface

    async def record(
        self,
        output: str | Path,
        *,
        duration_s: float | None = None,
        frame_limit: int | None = None,
        recv_timeout_s: float = 0.25,
    ) -> RecordingResult:
        if duration_s is None and frame_limit is None:
            raise ValueError("duration_s or frame_limit is required")
        if duration_s is not None and duration_s <= 0:
            raise ValueError("duration_s must be > 0")
        if frame_limit is not None and frame_limit <= 0:
            raise ValueError("frame_limit must be > 0")

        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        started_wall = datetime.now(timezone.utc)
        started_mono = monotonic()
        frames = 0

        with path.open("w", encoding="utf-8") as handle:
            while True:
                if duration_s is not None and monotonic() - started_mono >= duration_s:
                    break
                if frame_limit is not None and frames >= frame_limit:
                    break
                frame = await self.transport.recv(timeout=recv_timeout_s)
                if frame is None:
                    await asyncio.sleep(0)
                    continue
                handle.write(format_candump(frame, interface=self.interface) + "\n")
                frames += 1
                if frames % 50 == 0:
                    handle.flush()

        ended_wall = datetime.now(timezone.utc)
        return RecordingResult(
            path=str(path),
            frames=frames,
            started_at=started_wall,
            ended_at=ended_wall,
            duration_s=max(0.0, monotonic() - started_mono),
            interface=self.interface,
        )

    async def close(self) -> None:
        await self.transport.close()
