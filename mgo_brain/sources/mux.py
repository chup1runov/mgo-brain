from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from .base import SourceAdapter, SourceUpdate


class SourceMux(SourceAdapter):
    """Concurrent fan-in with observable errors, finite EOF and bounded cleanup."""
    name = "source-mux"

    def __init__(self, adapters: list[SourceAdapter], queue_size: int = 128):
        if not adapters or queue_size <= 0:
            raise ValueError("A nonempty adapter set and positive queue size are required")
        self.adapters = adapters
        self.queue_size = queue_size
        self.errors: dict[str,str] = {}
        self._closed: set[int] = set()

    async def stream(self) -> AsyncIterator[SourceUpdate]:
        queue = asyncio.Queue(maxsize=self.queue_size)
        async def pump(index, adapter):
            try:
                async for update in adapter.stream():
                    await queue.put((index, update))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.errors[f"{index}:{adapter.name}"] = type(exc).__name__
            finally:
                # Consumer cancellation also cancels pumps; no blocking sentinel then.
                if not asyncio.current_task().cancelling():
                    await queue.put((index, None))
        tasks = [asyncio.create_task(pump(i,a),name=f"source:{a.name}") for i,a in enumerate(self.adapters)]
        finished = set()
        try:
            while len(finished) < len(tasks):
                index, update = await queue.get()
                if update is None:
                    finished.add(index)
                else:
                    yield update
            if self.errors:
                raise RuntimeError(f"SourceMux exhausted with failures: {self.errors}")
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.close()

    async def close(self) -> None:
        for adapter in self.adapters:
            if id(adapter) in self._closed:
                continue
            self._closed.add(id(adapter))
            try:
                await asyncio.wait_for(adapter.close(), timeout=3.0)
            except Exception as exc:
                self.errors[f"close:{adapter.name}"] = type(exc).__name__
