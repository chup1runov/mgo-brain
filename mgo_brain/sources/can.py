from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class CanFrame:
    arbitration_id: int
    data: bytes
    timestamp: datetime
    is_extended_id: bool = False


class RawCANTransport(Protocol):
    async def recv(self, timeout: float | None = None) -> CanFrame | None: ...
    async def close(self) -> None: ...


class SocketCANTransport:
    """Receive-only wrapper around python-can.

    This class intentionally exposes no transmit API. The Linux CAN interface
    must still be configured in listen-only mode at the OS level before use on
    the factory MGO bus.
    """

    def __init__(
        self,
        channel: str,
        *,
        bus_factory=None,
        receive_timeout_s: float = 1.0,
        **bus_kwargs: Any,
    ):
        self.channel = channel
        self.receive_timeout_s = receive_timeout_s
        self._bus_factory = bus_factory
        self._bus_kwargs = bus_kwargs
        self._bus = None

    def _open(self):
        if self._bus is not None:
            return
        if self._bus_factory is not None:
            self._bus = self._bus_factory(channel=self.channel, **self._bus_kwargs)
            return
        try:
            import can  # type: ignore
        except ImportError as exc:
            raise RuntimeError("python-can is required for SocketCAN. Install mgo-brain[hardware].") from exc
        self._bus = can.Bus(
            interface="socketcan",
            channel=self.channel,
            receive_own_messages=False,
            **self._bus_kwargs,
        )

    async def recv(self, timeout: float | None = None) -> CanFrame | None:
        self._open()
        wait = self.receive_timeout_s if timeout is None else timeout
        msg = await asyncio.to_thread(self._bus.recv, wait)
        if msg is None:
            return None
        ts = datetime.fromtimestamp(float(getattr(msg, "timestamp", 0.0) or 0.0), tz=timezone.utc)
        if ts.year < 2000:
            ts = datetime.now(timezone.utc)
        return CanFrame(
            arbitration_id=int(msg.arbitration_id),
            data=bytes(msg.data),
            timestamp=ts,
            is_extended_id=bool(getattr(msg, "is_extended_id", False)),
        )

    async def close(self) -> None:
        if self._bus is None:
            return
        bus, self._bus = self._bus, None
        shutdown = getattr(bus, "shutdown", None)
        if shutdown:
            await asyncio.to_thread(shutdown)
