from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .survey import analyze_text


_SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]+")


class SurveySessionStore:
    """Persistent research sessions for repeatable CAN experiments."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        label: str,
        baseline: str,
        action: str,
        notes: str = "",
        max_candidates: int = 25,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        slug = _slug(label)
        session_id = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}_{slug}"
        folder = self.root / session_id
        folder.mkdir(parents=True)

        report = analyze_text(
            baseline,
            action,
            label=label,
            max_candidates=max_candidates,
        )

        (folder / "baseline.log").write_text(baseline, encoding="utf-8")
        (folder / "action.log").write_text(action, encoding="utf-8")
        (folder / "analysis.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (folder / "draft.dbc").write_text(report["draft_dbc"], encoding="utf-8")

        manifest = {
            "id": session_id,
            "label": label,
            "created_at": now.isoformat(),
            "notes": notes,
            "baseline_frames": report["baseline"]["frames"],
            "action_frames": report["action"]["frames"],
            "candidate_count": len(report["candidates"]),
            "top_candidate": report["candidates"][0] if report["candidates"] else None,
            "files": {
                "baseline": "baseline.log",
                "action": "action.log",
                "analysis": "analysis.json",
                "dbc": "draft.dbc",
            },
        }
        (folder / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return manifest

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        manifests = []
        for path in sorted(self.root.glob("*/manifest.json"), reverse=True):
            try:
                manifests.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
            if len(manifests) >= limit:
                break
        return manifests

    def get(self, session_id: str) -> dict[str, Any] | None:
        if "/" in session_id or "\\" in session_id or session_id.startswith("."):
            return None
        folder = self.root / session_id
        manifest_path = folder / "manifest.json"
        if not manifest_path.exists():
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        analysis_path = folder / "analysis.json"
        if analysis_path.exists():
            manifest["analysis"] = json.loads(analysis_path.read_text(encoding="utf-8"))
        return manifest

    def file_path(self, session_id: str, kind: str) -> Path | None:
        item = self.get(session_id)
        if item is None:
            return None
        rel = item.get("files", {}).get(kind)
        if rel is None:
            return None
        path = (self.root / session_id / rel).resolve()
        root = (self.root / session_id).resolve()
        if root not in path.parents:
            return None
        return path if path.exists() else None


def _slug(label: str) -> str:
    value = _SLUG_RE.sub("_", label.strip()).strip("_").lower()
    return value[:60] or "survey"
