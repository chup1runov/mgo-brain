from __future__ import annotations

import argparse
import json
from pathlib import Path

from .survey import analyze_text


def main():
    parser = argparse.ArgumentParser(description="Compare two candump logs for MGO CAN survey candidates.")
    parser.add_argument("baseline", type=Path, help="candump log with the condition inactive")
    parser.add_argument("action", type=Path, help="candump log with the condition active")
    parser.add_argument("--label", default="event", help="human-readable event label")
    parser.add_argument("--max-candidates", type=int, default=25)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--dbc-out", type=Path)
    args = parser.parse_args()

    report = analyze_text(
        args.baseline.read_text(encoding="utf-8", errors="replace"),
        args.action.read_text(encoding="utf-8", errors="replace"),
        label=args.label,
        max_candidates=args.max_candidates,
    )

    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.dbc_out:
        args.dbc_out.write_text(report["draft_dbc"], encoding="utf-8")

    print(f"baseline: {report['baseline']['frames']} frames / {report['baseline']['unique_ids']} ids")
    print(f"action:   {report['action']['frames']} frames / {report['action']['unique_ids']} ids")
    print()
    for rank, candidate in enumerate(report["candidates"][:15], start=1):
        changes = []
        for byte in candidate["changed_bytes"][:4]:
            before = byte.get("baseline_top") or {}
            after = byte.get("action_top") or {}
            changes.append(
                f"b{byte['index']}:{before.get('hex','--')}->{after.get('hex','--')}"
            )
        suffix = ", ".join(changes) or "presence"
        print(f"{rank:2}. {candidate['id_hex']} score={candidate['score']:.3f}  {suffix}")


if __name__ == "__main__":
    main()
