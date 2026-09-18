from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .recording import CANRecorder
from .sources.can import SocketCANTransport


async def _run(args) -> None:
    transport = SocketCANTransport(args.channel)
    recorder = CANRecorder(transport, interface=args.channel)
    try:
        result = await recorder.record(
            args.output,
            duration_s=args.seconds,
            frame_limit=args.frames,
        )
    finally:
        await recorder.close()

    print(f"saved: {result.path}")
    print(f"frames: {result.frames}")
    print(f"duration: {result.duration_s:.2f}s")
    print("NOTE: the Linux CAN interface itself must be configured listen-only before recording factory CAN.")


def main():
    parser = argparse.ArgumentParser(description="Receive-only candump recorder for MGO Brain commissioning.")
    parser.add_argument("--channel", default="can0")
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--frames", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seconds is None and args.frames is None:
        parser.error("one of --seconds or --frames is required")
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
