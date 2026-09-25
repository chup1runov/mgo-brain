from __future__ import annotations
import json
from pathlib import Path
from mgo_brain.resources import resolve_config_dir, resolve_static_dir

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "mgo_brain"

def test_packaged_static_matches_repository_assets():
    for name in ("index.html","i18n.js","manifest.webmanifest","service-worker.js","icon.svg"):
        assert (PACKAGE/"static"/name).read_bytes() == (ROOT/"static"/name).read_bytes()

def test_packaged_default_config_matches_repository_defaults():
    for path in (ROOT/"config").glob("*.json"):
        assert (PACKAGE/"default_config"/path.name).read_bytes() == path.read_bytes()

def test_editable_checkout_prefers_repository_resources():
    assert resolve_static_dir(ROOT) == ROOT/"static"
    assert resolve_config_dir(ROOT) == ROOT/"config"

def test_public_metadata_and_license_are_consistent():
    py=(ROOT/"pyproject.toml").read_text(encoding="utf-8")
    project=json.loads((ROOT/"config"/"project.json").read_text(encoding="utf-8"))
    security=(ROOT/"SECURITY.md").read_text(encoding="utf-8")
    assert 'version = "0.5.11"' in py
    assert 'license = {file = "LICENSE"}' in py
    assert project["current_release"] == "0.5.11"
    assert project["license"] == "Apache-2.0"
    assert "keep the repository private" not in security.lower()

def test_health_does_not_expose_runtime_paths():
    source=(ROOT/"mgo_brain"/"main.py").read_text(encoding="utf-8")
    health_block=source.split('@app.get("/manifest.webmanifest")',1)[0]
    assert '"data_dir":' not in health_block
    assert '"config_dir":' not in health_block


def test_installed_resource_detection_does_not_trust_unrelated_directories(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "static").mkdir()
    assert resolve_config_dir(tmp_path) == PACKAGE / "default_config"
    assert resolve_static_dir(tmp_path) == PACKAGE / "static"


def test_apache_license_is_canonical_form():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "APPENDIX: How to apply the Apache License to your work." in license_text
    assert "Copyright [yyyy] [name of copyright owner]" in license_text
