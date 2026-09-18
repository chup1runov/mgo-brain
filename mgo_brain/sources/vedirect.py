from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate


class LineTransport(Protocol):
    async def read_line(self) -> str | None: ...
    async def close(self) -> None: ...


@dataclass(frozen=True)
class VEField:
    key: str
    canonical: str
    unit: str | None = None
    scale: float = 1.0
    offset: float = 0.0


DEFAULT_FIELDS = [
    VEField("V", "electrical.battery_voltage", "V", 0.001),
    VEField("I", "electrical.battery_current", "A", 0.001),
    VEField("SOC", "electrical.battery_soc", "%", 0.1),
]


class VEDirectParser:
    """Collect VE.Direct text key/value lines into blocks.

    Checksum validation belongs in the transport layer because the checksum value
    may be a binary byte rather than text.
    """

    def __init__(self):
        self.fields: dict[str, str] = {}

    def feed(self, line: str) -> dict[str, str] | None:
        line = line.rstrip("\r\n")
        if not line:
            return None
        if "\t" not in line:
            return None
        key, value = line.split("\t", 1)
        if key == "Checksum":
            block = dict(self.fields)
            self.fields.clear()
            return block
        self.fields[key] = value
        return None


class VEDirectSourceAdapter(SourceAdapter):
    name = "smartshunt"

    def __init__(
        self,
        transport: LineTransport,
        *,
        fields: list[VEField] | None = None,
    ):
        self.transport = transport
        self.fields = {x.key: x for x in (fields or DEFAULT_FIELDS)}
        self.parser = VEDirectParser()

    async def stream(self):
        from datetime import datetime, timezone

        while True:
            line = await self.transport.read_line()
            if line is None:
                await asyncio.sleep(0.05)
                continue
            block = self.parser.feed(line)
            if block is None:
                continue
            ts = datetime.now(timezone.utc)
            signals = {}
            for key, raw in block.items():
                field = self.fields.get(key)
                if field is None:
                    continue
                try:
                    value = float(raw) * field.scale + field.offset
                except ValueError:
                    continue
                signals[field.canonical] = SignalReading(
                    value=value,
                    unit=field.unit,
                    quality=SignalQuality.GOOD,
                    source=self.name,
                    timestamp=ts,
                )
            if signals:
                yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)

    async def close(self) -> None:
        await self.transport.close()


class SerialLineTransport:
    def __init__(self, port: str, baudrate: int = 19200):
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError("pyserial is required. Install mgo-brain[hardware].") from exc
        self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)

    async def read_line(self) -> str | None:
        raw = await asyncio.to_thread(self.serial.readline)
        if not raw:
            return None
        return raw.decode("latin-1", errors="replace")

    async def close(self) -> None:
        await asyncio.to_thread(self.serial.close)
