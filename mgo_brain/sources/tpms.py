from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate


@dataclass(frozen=True)
class TPMSPacket:
    wheel: str
    pressure_bar: float
    temperature_c: float | None = None
    battery_pct: float | None = None


class TPMSTransport(Protocol):
    async def recv(self) -> TPMSPacket | None: ...
    async def close(self) -> None: ...


class TPMSSourceAdapter(SourceAdapter):
    name = "tpms"

    VALID_WHEELS = {"fl", "fr", "rl", "rr"}

    def __init__(self, transport: TPMSTransport):
        self.transport = transport

    async def stream(self):
        from datetime import datetime, timezone

        while True:
            packet = await self.transport.recv()
            if packet is None:
                continue
            wheel = packet.wheel.lower()
            if wheel not in self.VALID_WHEELS:
                continue
            ts = datetime.now(timezone.utc)
            signals = {
                f"tyres.{wheel}.pressure": SignalReading(
                    value=float(packet.pressure_bar),
                    unit="bar",
                    quality=SignalQuality.GOOD,
                    source=self.name,
                    timestamp=ts,
                )
            }
            if packet.temperature_c is not None:
                signals[f"tyres.{wheel}.temp"] = SignalReading(
                    value=float(packet.temperature_c),
                    unit="°C",
                    quality=SignalQuality.GOOD,
                    source=self.name,
                    timestamp=ts,
                )
            yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)

    async def close(self) -> None:
        await self.transport.close()
