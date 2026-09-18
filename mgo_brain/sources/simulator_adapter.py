from __future__ import annotations

from collections.abc import AsyncIterator

from .base import SourceAdapter, SourceUpdate


class SimulatorSourceAdapter(SourceAdapter):
    name = "simulator"

    def __init__(self, simulator):
        self.simulator = simulator

    async def stream(self) -> AsyncIterator[SourceUpdate]:
        async for state in self.simulator.stream():
            yield SourceUpdate(
                source=self.name,
                timestamp=state.timestamp,
                signals={name: reading.model_copy(deep=True) for name, reading in state.signals.items()},
            )
