from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate
from .can import CanFrame, RawCANTransport


PROTOCOL_VERSION = 1
DEFAULT_BASE_ID = 0x600
MAX_NODE_ID = 0x1F
FLAG_SENSOR_FAULT = 0x01


class SensorValueType(IntEnum):
    FLOAT32 = 1
    BOOL = 2
    UINT32 = 3
    INT32 = 4


@dataclass(frozen=True)
class SensorHubChannel:
    node_id: int
    channel: int
    canonical: str
    unit: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class SensorHubSample:
    node_id: int
    channel: int
    value: object
    flags: int
    value_type: SensorValueType


class SensorHubCodec:
    """Sensor CAN v1 on the separate MGO Sensor CAN.

    8-byte payload:
      byte0 protocol version
      byte1 value type
      byte2 channel
      byte3 flags
      byte4..7 little-endian value

    CAN ID = base_id + node_id.
    """

    @staticmethod
    def encode(sample: SensorHubSample, *, base_id: int = DEFAULT_BASE_ID) -> CanFrame:
        if not 0 <= sample.node_id <= MAX_NODE_ID:
            raise ValueError("node_id out of range")
        if not 0 <= sample.channel <= 255:
            raise ValueError("channel out of range")
        if sample.value_type == SensorValueType.FLOAT32:
            raw = struct.pack("<f", float(sample.value))
        elif sample.value_type == SensorValueType.BOOL:
            raw = struct.pack("<I", 1 if bool(sample.value) else 0)
        elif sample.value_type == SensorValueType.UINT32:
            raw = struct.pack("<I", int(sample.value))
        elif sample.value_type == SensorValueType.INT32:
            raw = struct.pack("<i", int(sample.value))
        else:
            raise ValueError("unsupported value type")
        from datetime import datetime, timezone
        return CanFrame(
            arbitration_id=base_id + sample.node_id,
            data=bytes([PROTOCOL_VERSION, int(sample.value_type), sample.channel, sample.flags]) + raw,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def decode(frame: CanFrame, *, base_id: int = DEFAULT_BASE_ID) -> SensorHubSample | None:
        node_id = frame.arbitration_id - base_id
        if not 0 <= node_id <= MAX_NODE_ID or len(frame.data) != 8:
            return None
        version, type_raw, channel, flags = frame.data[:4]
        if version != PROTOCOL_VERSION:
            return None
        try:
            value_type = SensorValueType(type_raw)
        except ValueError:
            return None
        payload = frame.data[4:]
        if value_type == SensorValueType.FLOAT32:
            value = struct.unpack("<f", payload)[0]
        elif value_type == SensorValueType.BOOL:
            value = bool(struct.unpack("<I", payload)[0])
        elif value_type == SensorValueType.UINT32:
            value = struct.unpack("<I", payload)[0]
        else:
            value = struct.unpack("<i", payload)[0]
        return SensorHubSample(node_id=node_id, channel=channel, value=value, flags=flags, value_type=value_type)


class SensorHubSourceAdapter(SourceAdapter):
    name = "sensorhub.can"

    def __init__(
        self,
        transport: RawCANTransport,
        channels: list[SensorHubChannel],
        *,
        base_id: int = DEFAULT_BASE_ID,
    ):
        self.transport = transport
        self.base_id = base_id
        self.channels = {(c.node_id, c.channel): c for c in channels}

    async def stream(self):
        while True:
            frame = await self.transport.recv()
            if frame is None:
                continue
            sample = SensorHubCodec.decode(frame, base_id=self.base_id)
            if sample is None:
                continue
            channel = self.channels.get((sample.node_id, sample.channel))
            if channel is None:
                continue
            quality = SignalQuality.SUSPECT if sample.flags & FLAG_SENSOR_FAULT else SignalQuality.GOOD
            reading_source = channel.source or self.name
            yield SourceUpdate(
                source=self.name,
                timestamp=frame.timestamp,
                signals={
                    channel.canonical: SignalReading(
                        value=sample.value,
                        unit=channel.unit,
                        quality=quality,
                        source=reading_source,
                        timestamp=frame.timestamp,
                    )
                },
            )

    async def close(self) -> None:
        await self.transport.close()
