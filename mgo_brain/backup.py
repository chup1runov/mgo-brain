from __future__ import annotations

import json
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def create_backup(
    *,
    data_dir: str | Path,
    config_dir: str | Path,
    output: str | Path,
) -> dict:
    data_dir = Path(data_dir)
    config_dir = Path(config_dir)
    output = Path(output)
    data_dir, config_dir, output = data_dir.resolve(), config_dir.resolve(), output.resolve()
    if output.is_relative_to(data_dir) or output.is_relative_to(config_dir):
        raise ValueError("Backup output must be outside data/config directories")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="mgo-brain-backup-") as temp:
        staging = Path(temp) / "mgo-brain-backup"
        staged_data = staging / "data"
        staged_config = staging / "config"
        staged_data.mkdir(parents=True)
        staged_config.mkdir(parents=True)

        if config_dir.exists():
            _copy_tree(config_dir, staged_config)

        if data_dir.exists():
            for path in data_dir.rglob("*"):
                if path.is_dir() or path.is_symlink():
                    continue
                rel = path.relative_to(data_dir)
                target = staged_data / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".sqlite3":
                    _backup_sqlite(path, target)
                elif path.name.endswith(("-wal", "-shm")):
                    continue
                else:
                    shutil.copy2(path, target)

        manifest = {
            "created_at": created_at.isoformat(),
            "data_dir": str(data_dir),
            "config_dir": str(config_dir),
        }
        (staging / "backup-manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        with tarfile.open(output, "w:gz") as archive:
            archive.add(staging, arcname="mgo-brain-backup")

    return {
        "path": str(output),
        "created_at": created_at.isoformat(),
        "size_bytes": output.stat().st_size,
    }


def _backup_sqlite(source: Path, target: Path) -> None:
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def _copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if path.is_dir() or path.is_symlink() or path.suffix in {".env", ".key", ".pem", ".p12"} or path.name.startswith(".env"):
            continue
        if False:
            continue
        rel = path.relative_to(source)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
