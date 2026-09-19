from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent
_config_dir: Path = _ROOT / "config"


def configure_paths(*, config_dir: Path) -> None:
    global _config_dir
    _config_dir = Path(config_dir)


def maintenance_path() -> Path:
    return _config_dir / "maintenance-plan.json"
