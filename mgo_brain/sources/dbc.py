from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate
from .can import CanFrame, RawCANTransport


@dataclass(frozen=True)
class DBCSignalMapping:
    message: str
    signal: str
    canonical: str
    unit: str | None = None
    scale: float = 1.0
    offset: float = 0.0


class DBCDecoder:
    """Decode CAN frames through a DBC and map selected signals to canonical names."""

    def __init__(
        self,
        *,
        mappings: list[DBCSignalMapping],
        dbc_path: str | Path | None = None,
        database: Any | None = None,
        source: str = "can.bfi",
    ):
        if database is None and dbc_path is None:
            raise ValueError("Either database or dbc_path is required")
        if database is None:
            try:
                import cantools  # type: ignore
            except ImportError as exc:
                raise RuntimeError("cantools is required for DBC decoding. Install mgo-brain[hardware].") from exc
            database = cantools.database.load_file(str(dbc_path))
        self.database = database
        self.source = source
        self._mapping = {(m.message, m.signal): m for m in mappings}

    def decode(self, frame: CanFrame) -> SourceUpdate | None:
        try:
            message = self.database.get_message_by_frame_id(frame.arbitration_id)
        except Exception:
            return None
        try:
            decoded = message.decode(frame.data, decode_choices=False)
        except Exception:
            return None

        signals: dict[str, SignalReading] = {}
        for signal_name, raw in decoded.items():
            mapping = self._mapping.get((message.name, signal_name))
            if mapping is None:
                continue
            try:
                value = float(raw) * mapping.scale + mapping.offset
            except (TypeError, ValueError):
                value = raw
            signals[mapping.canonical] = SignalReading(
                value=value,
                unit=mapping.unit,
                quality=SignalQuality.GOOD,
                source=self.source,
                timestamp=frame.timestamp,
            )
        if not signals:
            return None
        return SourceUpdate(source=self.source, timestamp=frame.timestamp, signals=signals)


class DBCSourceAdapter(SourceAdapter):
    def __init__(self, transport: RawCANTransport, decoder: DBCDecoder, *, name: str = "can.bfi"):
        self.transport = transport
        self.decoder = decoder
        self.name = name

    async def stream(self):
        while True:
            frame = await self.transport.recv()
            if frame is None:
                continue
            update = self.decoder.decode(frame)
            if update is not None:
                yield update

    async def close(self) -> None:
        await self.transport.close()
