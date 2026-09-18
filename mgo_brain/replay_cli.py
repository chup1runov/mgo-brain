from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .recording import format_candump
from .replay import CandumpReplayTransport


async def _run(args):
    transport = CandumpReplayTransport.from_file(args.log, speed=args.speed, loop=args.loop)
    count = 0
    try:
        while args.frames is None or count < args.frames:
            frame = await transport.recv(timeout=0.01)
            if frame is None:
                break
            print(format_candump(frame, interface=args.interface))
            count += 1
    finally:
        await transport.close()


def main():
    parser = argparse.ArgumentParser(description="Replay a candump recording without CAN hardware.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--speed", type=float, default=0.0, help="0=no delay, 1=recorded timing")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--frames", type=int)
    parser.add_argument("--interface", default="replay0")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
