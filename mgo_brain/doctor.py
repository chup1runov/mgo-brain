from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from .runtime import RuntimeSettings
from .sources.config import load_source_config, load_preferred_sources


def run_doctor(settings: RuntimeSettings) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str, *, required: bool = True):
        checks.append({
            "name": name,
            "ok": bool(ok),
            "required": required,
            "detail": detail,
        })

    try:
        settings.ensure_runtime_dirs()
        probe = settings.data_dir / ".mgo-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        add("data_dir_writable", True, str(settings.data_dir))
    except Exception as exc:
        add("data_dir_writable", False, f"{settings.data_dir}: {exc}")

    add(
        "config_dir_exists",
        settings.config_dir.is_dir(),
        str(settings.config_dir),
    )

    try:
        cfg = load_source_config(settings.sources_path)
        enabled = [x.type for x in cfg.sources if x.enabled]
        add("sources_config", bool(enabled), f"enabled={enabled}")
    except Exception as exc:
        add("sources_config", False, str(exc))

    try:
        preferred = load_preferred_sources(settings.signal_registry_path)
        add("signal_registry", bool(preferred), f"signals={len(preferred)}")
    except Exception as exc:
        add("signal_registry", False, str(exc))

    try:
        data = json.loads(settings.maintenance_path.read_text(encoding="utf-8"))
        count = len(data.get("items", []))
        add("maintenance_registry", count > 0, f"items={count}")
    except Exception as exc:
        add("maintenance_registry", False, str(exc))

    optional = {
        "duckdb": "historical analytics",
        "can": "SocketCAN/python-can",
        "cantools": "DBC decoding",
        "pymodbus": "Modbus/RS485",
        "serial": "serial / VE.Direct",
    }
    for module, purpose in optional.items():
        available = importlib.util.find_spec(module) is not None
        add(
            f"optional:{module}",
            available,
            f"{purpose}: {'available' if available else 'not installed'}",
            required=False,
        )

    required_failed = [x for x in checks if x["required"] and not x["ok"]]
    return {
        "ok": not required_failed,
        "data_dir": str(settings.data_dir),
        "config_dir": str(settings.config_dir),
        "host": settings.host,
        "port": settings.port,
        "checks": checks,
    }
