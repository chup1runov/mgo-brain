from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .base import SourceAdapter
from .mux import SourceMux
from .simulator_adapter import SimulatorSourceAdapter


@dataclass(frozen=True)
class SourceEntry:
    type: str
    enabled: bool = True
    options: dict | None = None


@dataclass(frozen=True)
class RuntimeSourceConfig:
    stale_after_s: float
    sources: tuple[SourceEntry, ...]


def load_source_config(path: str | Path) -> RuntimeSourceConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return RuntimeSourceConfig(
        stale_after_s=float(raw.get("stale_after_s", 3.0)),
        sources=tuple(
            SourceEntry(
                type=str(item["type"]),
                enabled=bool(item.get("enabled", True)),
                options=dict(item.get("options", {})),
            )
            for item in raw.get("sources", [])
        ),
    )


def load_preferred_sources(signal_registry_path: str | Path) -> dict[str, list[str]]:
    raw = json.loads(Path(signal_registry_path).read_text(encoding="utf-8"))
    return {
        item["name"]: list(item.get("preferred_sources", []))
        for item in raw.get("signals", [])
    }


class SourceFactory:
    """Configurable adapter factory with injectable builders.

    Only the simulator builder is enabled by default. Hardware builders can be
    registered by the deployment layer so importing the core never requires
    hardware libraries.
    """

    def __init__(self, *, simulator=None):
        self.simulator = simulator
        self.builders: dict[str, Callable[[dict], SourceAdapter]] = {}
        if simulator is not None:
            self.register("simulator", lambda options: SimulatorSourceAdapter(simulator))

    def register(self, source_type: str, builder: Callable[[dict], SourceAdapter]) -> None:
        self.builders[source_type] = builder

    def build(self, config: RuntimeSourceConfig) -> SourceAdapter:
        adapters = []
        for entry in config.sources:
            if not entry.enabled:
                continue
            builder = self.builders.get(entry.type)
            if builder is None:
                raise ValueError(f"No SourceAdapter builder registered for type {entry.type!r}")
            adapters.append(builder(entry.options or {}))
        if not adapters:
            raise ValueError("No enabled sources in runtime configuration")
        return adapters[0] if len(adapters) == 1 else SourceMux(adapters)
