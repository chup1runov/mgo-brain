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
    """Read Linux link configuration; never change it or transmit on the bus."""
    result = subprocess.run(['ip', '-details', '-json', 'link', 'show', 'dev', channel],
                            check=True, capture_output=True, text=True, timeout=3)
    links = json.loads(result.stdout)
    if len(links) != 1:
        raise RuntimeError('Cannot verify CAN link configuration')
    info = links[0].get('linkinfo', {})
    if info.get('info_kind') == 'vcan':
        return  # Linux virtual CAN has no physical wire to disturb.
    modes = info.get('info_data', {}).get('ctrlmode', [])
    mode_text = json.dumps(modes).upper().replace('_', '-')
    if info.get('info_kind') != 'can' or 'LISTEN-ONLY' not in mode_text or 'UP' not in links[0].get('flags', []):
        raise RuntimeError('Factory CAN must be UP and OS-configured LISTEN-ONLY before use')


class SocketCANTransport:
    """Receive-only CAN wrapper. Factory interface mode is verified on open.

    Sensor CAN can explicitly opt out of silent mode because it is a separate bus.
    No send API is exposed by this wrapper.
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
        # Preserve the documented classic-CAN boundary instead of interpreting FD/RTR/error data.
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
