from __future__ import annotations

import asyncio
import json
import subprocess
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


def verify_listen_only(channel: str) -> None:
    """Inspect Linux link state without changing it or transmitting any frame."""
    result = subprocess.run(['ip', '-details', '-json', 'link', 'show', 'dev', channel],
                            check=True, capture_output=True, text=True, timeout=3)
    links = json.loads(result.stdout)
    if len(links) != 1:
        raise RuntimeError('Cannot verify CAN link configuration')
    info = links[0].get('linkinfo', {})
    if info.get('info_kind') == 'vcan':
        return
    raw_modes = info.get('info_data', {}).get('ctrlmode', [])
    if isinstance(raw_modes, dict):
        raw_modes = [name for name, enabled in raw_modes.items() if enabled is True]
    modes = {str(name).upper().replace('_', '-') for name in raw_modes} if isinstance(raw_modes, list) else set()
    if info.get('info_kind') != 'can' or 'LISTEN-ONLY' not in modes or 'UP' not in links[0].get('flags', []):
        raise RuntimeError('Factory CAN must be UP and OS-configured LISTEN-ONLY before use')


class SocketCANTransport:
    """Receive-only wrapper; factory interface silent mode is verified on open.

    Separate private Sensor CAN can explicitly opt out of silent mode. No send
    method is exposed. Injected bus factories are for controlled test transports.
    """
    def __init__(self, channel: str, *, bus_factory=None, receive_timeout_s: float = 1.0,
                 require_listen_only: bool = True, **bus_kwargs: Any):
        self.channel = channel
        self.receive_timeout_s = receive_timeout_s
        self.require_listen_only = require_listen_only
        self._bus_factory = bus_factory
        self._bus_kwargs = bus_kwargs
        self._bus = None

    def _open(self):
        if self._bus is not None:
            return
        if self._bus_factory is not None:
            self._bus = self._bus_factory(channel=self.channel, **self._bus_kwargs)
            return
        if self.require_listen_only:
            verify_listen_only(self.channel)
        try:
            import can
        except ImportError as exc:
            raise RuntimeError('python-can is required. Install mgo-brain[hardware].') from exc
        self._bus = can.Bus(interface='socketcan', channel=self.channel,
                            receive_own_messages=False, **self._bus_kwargs)

    async def recv(self, timeout: float | None = None) -> CanFrame | None:
        self._open()
        msg = await asyncio.to_thread(self._bus.recv, self.receive_timeout_s if timeout is None else timeout)
        if msg is None:
            return None
        if getattr(msg, 'is_remote_frame', False) or getattr(msg, 'is_error_frame', False) or getattr(msg, 'is_fd', False):
            return None
        timestamp = float(getattr(msg, 'timestamp', 0.0) or 0.0)
        ts = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp > 946684800 else datetime.now(timezone.utc)
        return CanFrame(int(msg.arbitration_id), bytes(msg.data), ts, bool(getattr(msg, 'is_extended_id', False)))

    async def close(self):
        if self._bus is not None:
            bus, self._bus = self._bus, None
            shutdown = getattr(bus, 'shutdown', None)
            if shutdown:
                await asyncio.to_thread(shutdown)
