from __future__ import annotations

import json
import sqlite3
import tarfile
from pathlib import Path

from mgo_brain.backup import create_backup
from mgo_brain.doctor import run_doctor
from mgo_brain.runtime import RuntimeSettings


ROOT = Path(__file__).resolve().parent.parent


def write_minimal_config(config_dir: Path):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "sources.json").write_text(
        json.dumps({
            "stale_after_s": 3,
            "sources": [{"type": "simulator", "enabled": True, "options": {}}],
        }),
        encoding="utf-8",
    )
    (config_dir / "signals-v1.json").write_text(
        json.dumps({
            "signals": [
                {"name": "vehicle.speed", "preferred_sources": ["can.bfi", "gnss"]}
            ]
        }),
        encoding="utf-8",
    )
    (config_dir / "maintenance-plan.json").write_text(
        json.dumps({"items": [{"component": "engine_oil"}]}),
        encoding="utf-8",
    )


def test_runtime_settings_from_env(tmp_path):
    env = {
        "MGO_BRAIN_DATA_DIR": str(tmp_path / "var"),
        "MGO_BRAIN_CONFIG_DIR": str(tmp_path / "etc"),
        "MGO_BRAIN_SOURCES_FILE": str(tmp_path / "bench.json"),
        "MGO_BRAIN_HOST": "127.0.0.1",
        "MGO_BRAIN_PORT": "9090",
    }
    settings = RuntimeSettings.from_env(tmp_path, env)
    assert settings.data_dir == (tmp_path / "var").resolve()
    assert settings.config_dir == (tmp_path / "etc").resolve()
    assert settings.sources_path == (tmp_path / "bench.json").resolve()
    assert settings.host == "127.0.0.1"
    assert settings.port == 9090


def test_doctor_reports_valid_core_runtime(tmp_path):
    config_dir = tmp_path / "etc"
    data_dir = tmp_path / "var"
    write_minimal_config(config_dir)
    settings = RuntimeSettings(
        root=tmp_path,
        data_dir=data_dir,
        config_dir=config_dir,
        host="0.0.0.0",
        port=8080,
    )
    report = run_doctor(settings)
    assert report["ok"] is True
    by_name = {x["name"]: x for x in report["checks"]}
    assert by_name["data_dir_writable"]["ok"] is True
    assert by_name["sources_config"]["ok"] is True
    assert by_name["signal_registry"]["ok"] is True


def test_backup_contains_config_data_and_consistent_sqlite(tmp_path):
    config = tmp_path / "config"
    data = tmp_path / "data"
    write_minimal_config(config)
    data.mkdir()
    db = data / "mgo_brain.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE test (value TEXT)")
        conn.execute("INSERT INTO test VALUES ('hello')")
    (data / "notes.txt").write_text("evidence", encoding="utf-8")

    output = tmp_path / "backup.tar.gz"
    result = create_backup(data_dir=data, config_dir=config, output=output)
    assert result["size_bytes"] > 0

    extract = tmp_path / "extract"
    with tarfile.open(output, "r:gz") as archive:
        archive.extractall(extract, filter="data")

    root = extract / "mgo-brain-backup"
    assert (root / "config" / "sources.json").exists()
    assert (root / "data" / "notes.txt").read_text(encoding="utf-8") == "evidence"
    with sqlite3.connect(root / "data" / "mgo_brain.sqlite3") as conn:
        assert conn.execute("SELECT value FROM test").fetchone()[0] == "hello"


def test_deployment_templates_exist_and_are_safe_by_default():
    unit = (ROOT / "deployment" / "systemd" / "mgo-brain.service").read_text(encoding="utf-8")
    env = (ROOT / "deployment" / "mgo-brain.env.example").read_text(encoding="utf-8")
    avahi = (ROOT / "deployment" / "avahi" / "mgo-brain.service").read_text(encoding="utf-8")
    assert "Restart=on-failure" in unit
    assert "ReadWritePaths=/var/lib/mgo-brain" in unit
    assert "MGO_BRAIN_DATA_DIR=/var/lib/mgo-brain" in env
    assert "_http._tcp" in avahi
    assert "ip link" not in unit.lower()
