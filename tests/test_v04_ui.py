from __future__ import annotations

import json
from pathlib import Path

from mgo_brain.main import app

ROOT = Path(__file__).resolve().parent.parent


def test_pwa_manifest_is_valid_and_standalone():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "MGO Brain"
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/"
    assert manifest["icons"]


def test_ui_has_all_planned_v04_views():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    for view in ("home", "engine", "cvt", "electrical", "trips", "service", "lab"):
        assert f'id="{view}"' in html
        assert f'data-view="{view}"' in html
    assert "/api/v1/analytics/compare" in html
    assert "/api/v1/trips/${id}/report" in html


def test_service_worker_offline_shell_exists():
    sw = (ROOT / "static" / "service-worker.js").read_text(encoding="utf-8")
    assert "caches.open" in sw
    assert "'/manifest.webmanifest'" in sw
    assert "startsWith('/api/')" in sw


def test_backend_exposes_v04_ui_routes():
    paths = {route.path for route in app.routes}
    assert "/manifest.webmanifest" in paths
    assert "/service-worker.js" in paths
    assert "/api/v1/reports" in paths
