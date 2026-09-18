from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .base import SourceAdapter, SourceUpdate


class SourceMux(SourceAdapter):
    """Fan-in updates from multiple independent adapters."""

    name = "source-mux"

    def __init__(self, adapters: list[SourceAdapter], queue_size: int = 128):
        if not adapters:
            raise ValueError("SourceMux requires at least one adapter")
        self.adapters = adapters
        self.queue_size = queue_size

    async def stream(self) -> AsyncIterator[SourceUpdate]:
        queue: asyncio.Queue[SourceUpdate] = asyncio.Queue(maxsize=self.queue_size)

        async def pump(adapter: SourceAdapter):
            async for update in adapter.stream():
                await queue.put(update)

        tasks = [asyncio.create_task(pump(adapter), name=f"source:{adapter.name}") for adapter in self.adapters]
        try:
            while True:
                yield await queue.get()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            for adapter in self.adapters:
                await adapter.close()

    async def close(self) -> None:
        for adapter in self.adapters:
            await adapter.close()
