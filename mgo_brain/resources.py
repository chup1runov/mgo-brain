from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

def resolve_config_dir(repository_root: str | Path) -> Path:
    repo = Path(repository_root).resolve() / "config"
    if repo.is_dir():
        return repo
    packaged = PACKAGE_DIR / "default_config"
    if not packaged.is_dir():
        raise RuntimeError("MGO Brain packaged default configuration is missing")
    return packaged

def resolve_static_dir(repository_root: str | Path) -> Path:
    repo = Path(repository_root).resolve() / "static"
    if repo.is_dir():
        return repo
    packaged = PACKAGE_DIR / "static"
    if not packaged.is_dir():
        raise RuntimeError("MGO Brain packaged static assets are missing")
    return packaged

def resolve_data_dir(repository_root: str | Path) -> Path:
    root = Path(repository_root).resolve()
    if (root / "config").is_dir():
        return root / "data"
    return Path.home() / ".local" / "share" / "mgo-brain"
