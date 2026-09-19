from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
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
    VEField('V', 'electrical.battery_voltage', 'V', 0.001),
    VEField('I', 'electrical.battery_current', 'A', 0.001),
    VEField('SOC', 'electrical.battery_soc', '%', 0.1),
]


class VEDirectParser:
    """Legacy text-only parser for fixtures. Output is UNVERIFIED, never GOOD."""
    def __init__(self):
        self.fields: dict[str, str] = {}

    def feed(self, line: str) -> dict[str, str] | None:
        line = line.rstrip('\r\n')
        if '\t' not in line:
            return None
        key, value = line.split('\t', 1)
        if key == 'Checksum':
            block, self.fields = dict(self.fields), {}
            return block
        self.fields[key] = value
        if len(self.fields) > 128:
            self.fields.clear()
        return None


class VEDirectByteParser:
    """Parse exact text-frame bytes, including the binary checksum byte.

    A block begins with CRLF; the Checksum value may itself be CR/LF/NUL.
    Corrupt, mixed-HEX or truncated blocks are discarded, not presented as GOOD.
    """
    MARKER = b'\r\nChecksum\t'

    def __init__(self, max_block_bytes: int = 16384):
        self.buffer = bytearray()
        self.max_block_bytes = max_block_bytes
        self.rejected_blocks = 0

    def feed(self, data: bytes) -> list[dict[str, str]]:
        self.buffer.extend(data)
        blocks = []
        while True:
            marker = self.buffer.find(self.MARKER)
            end = marker + len(self.MARKER) + 1
            if marker < 0 or len(self.buffer) < end:
                break
            raw = bytes(self.buffer[:end])
            del self.buffer[:end]
            if not raw.startswith(b'\r\n') or sum(raw) % 256 != 0:
                self.rejected_blocks += 1
                continue
            fields = {}
            try:
                for line in raw[:marker].split(b'\r\n'):
                    if not line:
                        continue
                    key, value = line.split(b'\t', 1)
                    fields[key.decode('ascii')] = value.decode('ascii')
            except (ValueError, UnicodeDecodeError):
                self.rejected_blocks += 1
                continue
            blocks.append(fields)
        if len(self.buffer) > self.max_block_bytes:
            self.buffer.clear()
            self.rejected_blocks += 1
        return blocks


class VEDirectSourceAdapter(SourceAdapter):
    name = 'smartshunt'

    def __init__(self, transport, *, fields: list[VEField] | None = None):
        self.transport = transport
        self.fields = {x.key: x for x in (fields or DEFAULT_FIELDS)}
        self.parser = VEDirectParser()
        self.byte_parser = VEDirectByteParser()

    async def stream(self):
        binary = callable(getattr(self.transport, 'read_bytes', None))
        while True:
            if binary:
                raw = await self.transport.read_bytes()
                blocks = self.byte_parser.feed(raw or b'')
                quality = SignalQuality.GOOD
            else:
                line = await self.transport.read_line()
                block = self.parser.feed(line) if line else None
                blocks = [block] if block is not None else []
                quality = SignalQuality.UNVERIFIED
            if not blocks:
                await asyncio.sleep(0.01)
                continue
            for block in blocks:
                ts = datetime.now(timezone.utc)
                signals = {}
                for key, raw_value in block.items():
                    field = self.fields.get(key)
                    if field is None:
                        continue
                    try:
                        value = float(raw_value) * field.scale + field.offset
                    except ValueError:
                        continue
                    signals[field.canonical] = SignalReading(value=value, unit=field.unit,
                        quality=quality, source=self.name, timestamp=ts)
                if signals:
                    yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)

    async def close(self):
        await self.transport.close()


class SerialLineTransport:
    """Byte-capable serial transport; historical class name retained for configuration."""
    def __init__(self, port: str, baudrate: int = 19200):
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError('pyserial is required. Install mgo-brain[hardware].') from exc
        self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=0.1)

    async def read_bytes(self) -> bytes:
        return await asyncio.to_thread(self.serial.read, 256)

    async def read_line(self) -> str | None:
        raw = await asyncio.to_thread(self.serial.readline)
        return raw.decode('latin-1') if raw else None

    async def close(self):
        await asyncio.to_thread(self.serial.close)
