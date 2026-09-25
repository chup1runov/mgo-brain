from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent


def _is_checkout(root: Path) -> bool:
    return (
        (root / "pyproject.toml").is_file()
        and (root / "mgo_brain").is_dir()
        and (root / "config").is_dir()
        and (root / "static").is_dir()
    )


def resolve_config_dir(repository_root: str | Path) -> Path:
    root = Path(repository_root).resolve()
    if _is_checkout(root):
        return root / "config"
    packaged = PACKAGE_DIR / "default_config"
    if not packaged.is_dir():
        raise RuntimeError("MGO Brain packaged default configuration is missing")
    return packaged


def resolve_static_dir(repository_root: str | Path) -> Path:
    root = Path(repository_root).resolve()
    if _is_checkout(root):
        return root / "static"
    packaged = PACKAGE_DIR / "static"
    if not packaged.is_dir():
        raise RuntimeError("MGO Brain packaged static assets are missing")
    return packaged


def resolve_data_dir(repository_root: str | Path) -> Path:
    root = Path(repository_root).resolve()
    if _is_checkout(root):
        return root / "data"
    return Path.home() / ".local" / "share" / "mgo-brain"
