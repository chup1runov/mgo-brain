from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .resources import resolve_config_dir, resolve_data_dir


@dataclass(frozen=True)
class RuntimeSettings:
    root: Path
    data_dir: Path
    config_dir: Path
    sources_file: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8080

    @property
    def sources_path(self) -> Path:
        return self.sources_file or (self.config_dir / "sources.json")

    @property
    def signal_registry_path(self) -> Path:
        return self.config_dir / "signals-v1.json"

    @property
    def maintenance_path(self) -> Path:
        return self.config_dir / "maintenance-plan.json"

    @classmethod
    def from_env(
        cls,
        root: str | Path,
        environ: Mapping[str, str] | None = None,
    ) -> "RuntimeSettings":
        env = os.environ if environ is None else environ
        root_path = Path(root).resolve()
        data_default = resolve_data_dir(root_path)
        config_default = resolve_config_dir(root_path)
        data_dir = Path(env.get("MGO_BRAIN_DATA_DIR", str(data_default))).expanduser()
        config_dir = Path(env.get("MGO_BRAIN_CONFIG_DIR", str(config_default))).expanduser()
        sources_file_raw = env.get("MGO_BRAIN_SOURCES_FILE")
        sources_file = Path(sources_file_raw).expanduser().resolve() if sources_file_raw else None
        host = env.get("MGO_BRAIN_HOST", "127.0.0.1")
        port = int(env.get("MGO_BRAIN_PORT", "8080"))
        if not 1 <= port <= 65535:
            raise ValueError("MGO_BRAIN_PORT must be between 1 and 65535")
        return cls(
            root=root_path,
            data_dir=data_dir.resolve(),
            config_dir=config_dir.resolve(),
            sources_file=sources_file,
            host=host,
            port=port,
        )

    def ensure_runtime_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
