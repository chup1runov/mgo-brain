from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from ..models import SignalQuality, SignalReading
from .base import SourceAdapter, SourceUpdate


class ModbusTransport(Protocol):
    async def read_discrete_inputs(self, address: int, count: int, *, slave: int) -> list[bool]: ...
    async def read_input_registers(self, address: int, count: int, *, slave: int) -> list[int]: ...
    async def close(self) -> None: ...


@dataclass(frozen=True)
class DigitalInputChannel:
    address: int
    canonical: str
    invert: bool = False
    source: str = "digital.oem"


@dataclass(frozen=True)
class AnalogInputChannel:
    address: int
    canonical: str
    unit: str | None = None
    scale: float = 1.0
    offset: float = 0.0
    signed: bool = False
    source: str = "modbus.ai"


class ModbusDigitalInputAdapter(SourceAdapter):
    name = "modbus.di"

    def __init__(self, transport: ModbusTransport, channels: list[DigitalInputChannel], *, slave: int = 1, poll_interval_s: float = 0.2):
        self.transport = transport
        self.channels = channels
        self.slave = slave
        self.poll_interval_s = poll_interval_s

    async def stream(self):
        from datetime import datetime, timezone
        while True:
            ts = datetime.now(timezone.utc)
            signals = {}
            for channel in self.channels:
                bits = await self.transport.read_discrete_inputs(channel.address, 1, slave=self.slave)
                value = bool(bits[0]) if bits else False
                if channel.invert:
                    value = not value
                signals[channel.canonical] = SignalReading(value=value, quality=SignalQuality.GOOD, source=channel.source, timestamp=ts)
            yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)
            await asyncio.sleep(self.poll_interval_s)

    async def close(self) -> None:
        await self.transport.close()


class ModbusAnalogInputAdapter(SourceAdapter):
    name = "modbus.ai"

    def __init__(self, transport: ModbusTransport, channels: list[AnalogInputChannel], *, slave: int = 1, poll_interval_s: float = 0.2):
        self.transport = transport
        self.channels = channels
        self.slave = slave
        self.poll_interval_s = poll_interval_s

    async def stream(self):
        from datetime import datetime, timezone
        while True:
            ts = datetime.now(timezone.utc)
            signals = {}
            for channel in self.channels:
                regs = await self.transport.read_input_registers(channel.address, 1, slave=self.slave)
                raw = int(regs[0]) if regs else 0
                if channel.signed and raw >= 0x8000:
                    raw -= 0x10000
                value = raw * channel.scale + channel.offset
                signals[channel.canonical] = SignalReading(value=value, unit=channel.unit, quality=SignalQuality.GOOD, source=channel.source, timestamp=ts)
            yield SourceUpdate(source=self.name, timestamp=ts, signals=signals)
            await asyncio.sleep(self.poll_interval_s)

    async def close(self) -> None:
        await self.transport.close()


class PymodbusSerialTransport:
    def __init__(self, *, port: str, baudrate: int = 9600, parity: str = "N", stopbits: int = 1):
        try:
            from pymodbus.client import AsyncModbusSerialClient  # type: ignore
        except ImportError as exc:
            raise RuntimeError("pymodbus is required. Install mgo-brain[hardware].") from exc
        self.client = AsyncModbusSerialClient(port=port, baudrate=baudrate, parity=parity, stopbits=stopbits)
        self._connected = False

    async def _ensure(self):
        if not self._connected:
            result = await self.client.connect()
            if result is False:
                raise RuntimeError("Unable to connect to Modbus serial transport")
            self._connected = True

    async def _call(self, name: str, *, address: int, count: int, slave: int):
        await self._ensure()
        fn = getattr(self.client, name)
        try:
            return await fn(address=address, count=count, device_id=slave)
        except TypeError:
            return await fn(address=address, count=count, slave=slave)

    async def read_discrete_inputs(self, address: int, count: int, *, slave: int) -> list[bool]:
        response = await self._call("read_discrete_inputs", address=address, count=count, slave=slave)
        if getattr(response, "isError", lambda: False)():
            raise RuntimeError(f"Modbus discrete-input read failed: {response}")
        return list(getattr(response, "bits", []))[:count]

    async def read_input_registers(self, address: int, count: int, *, slave: int) -> list[int]:
        response = await self._call("read_input_registers", address=address, count=count, slave=slave)
        if getattr(response, "isError", lambda: False)():
            raise RuntimeError(f"Modbus register read failed: {response}")
        return [int(x) for x in getattr(response, "registers", [])[:count]]

    async def close(self) -> None:
        close = getattr(self.client, "close", None)
        if close:
            result = close()
            if asyncio.iscoroutine(result):
                await result
