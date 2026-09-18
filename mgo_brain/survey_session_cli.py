from __future__ import annotations

import argparse
import json
from pathlib import Path

from .survey_sessions import SurveySessionStore


def main():
    parser = argparse.ArgumentParser(description="Persist a baseline/action CAN survey session.")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("action", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--store", type=Path, default=Path("data/surveys"))
    parser.add_argument("--max-candidates", type=int, default=25)
    args = parser.parse_args()

    store = SurveySessionStore(args.store)
    manifest = store.create(
        label=args.label,
        baseline=args.baseline.read_text(encoding="utf-8", errors="replace"),
        action=args.action.read_text(encoding="utf-8", errors="replace"),
        notes=args.notes,
        max_candidates=args.max_candidates,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
