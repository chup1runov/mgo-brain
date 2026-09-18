from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate


@dataclass(frozen=True)
class MotionPacket:
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    speed_kmh: float | None = None
    accel_x_ms2: float | None = None
    accel_y_ms2: float | None = None
    accel_z_ms2: float | None = None


class MotionTransport(Protocol):
    async def recv(self) -> MotionPacket | None: ...
    async def close(self) -> None: ...


class GNSSIMUSourceAdapter(SourceAdapter):
    name = "gnss.imu"

    def __init__(self, transport: MotionTransport):
        self.transport = transport

    async def stream(self):
        from datetime import datetime, timezone

        while True:
            packet = await self.transport.recv()
            if packet is None:
                continue
            ts = datetime.now(timezone.utc)
            signals = {}

            def add(name, value, unit, source):
                if value is not None:
                    signals[name] = SignalReading(
                        value=float(value),
                        unit=unit,
                        quality=SignalQuality.GOOD,
                        source=source,
                        timestamp=ts,
                    )

            add("position.latitude", packet.latitude, "deg", "gnss")
            add("position.longitude", packet.longitude, "deg", "gnss")
            add("position.altitude", packet.altitude_m, "m", "gnss")
            add("vehicle.speed_gps", packet.speed_kmh, "km/h", "gnss")
            add("motion.accel_x", packet.accel_x_ms2, "m/s²", "autopi.imu")
            add("motion.accel_y", packet.accel_y_ms2, "m/s²", "autopi.imu")
            add("motion.accel_z", packet.accel_z_ms2, "m/s²", "autopi.imu")
            if signals:
                yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)

    async def close(self) -> None:
        await self.transport.close()
