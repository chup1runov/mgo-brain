from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


REQUIRED = [
    "PROJECT.md",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "README.md",
    "CHANGELOG.md",
    "docs/INDEX.md",
    "docs/PROJECT_HANDOFF.md",
    "docs/PROJECT_STATE.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "docs/SAFETY.md",
    "docs/EVIDENCE_POLICY.md",
    "docs/VEHICLE_BASELINE.md",
    "docs/HARDWARE_BOM.md",
    "docs/INSTALLATION_PLAN.md",
    "docs/FIRST_VEHICLE_DAY.md",
    "docs/OPEN_QUESTIONS.md",
    "docs/DATA_PRIVACY.md",
    "docs/AI_GATEWAY.md",
    "docs/TESTING.md",
    "docs/RELEASE_PROCESS.md",
    "docs/PUBLIC_RELEASE.md",
    "docs/BACKUP_RECOVERY.md",
    "docs/REFERENCES.md",
    "docs/GLOSSARY.md",
    "docs/UI_CONCEPT.md",
    "docs/decisions/README.md",
    "docs/decisions/ADR-0007-ai-gateway.md",
    "docs/OPENAI_REFERENCES.md",
    "config/project.json",
    "config/hardware-plan.json",
    "config/ai-policy.json",
    "config/vehicle-profile.example.json",
    "mgo_brain/resources.py",
    "mgo_brain/static/index.html",
    "mgo_brain/default_config/sources.json",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/can_signal_report.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/dependabot.yml",
]


def test_repository_canon_files_exist():
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    assert missing == []


def test_project_declares_repo_first_rule():
    text = (ROOT / "PROJECT.md").read_text(encoding="utf-8").lower()
    assert "repo-first" in text
    assert "source of truth" in text
    assert "mgo brain" in text


def test_project_metadata_matches_package_version():
    project = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = project["current_release"]
    assert project["project_name"] == "MGO Brain"
    assert f'version = "{version}"' in pyproject


def test_private_runtime_patterns_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", "*.sqlite3", "*.parquet", "*.log", "data/*"):
        assert pattern in ignore
