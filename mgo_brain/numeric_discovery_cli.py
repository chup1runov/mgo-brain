from __future__ import annotations

import argparse
import json
from pathlib import Path

from .numeric_discovery import discover_numeric_from_text


def main():
    parser = argparse.ArgumentParser(description="Rank CAN numeric fields against a timestamped reference series.")
    parser.add_argument("can_log", type=Path)
    parser.add_argument("reference_csv", type=Path)
    parser.add_argument("--label", default="numeric_signal")
    parser.add_argument("--max-time-gap", type=float, default=0.25)
    parser.add_argument("--min-samples", type=int, default=12)
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = discover_numeric_from_text(
        args.can_log.read_text(encoding="utf-8", errors="replace"),
        args.reference_csv.read_text(encoding="utf-8", errors="replace"),
        label=args.label,
        max_time_gap_s=args.max_time_gap,
        min_samples=args.min_samples,
        max_candidates=args.max_candidates,
    )

    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"reference samples: {report['reference_samples']}")
    print(f"CAN frames: {report['can_frames']}")
    for i, candidate in enumerate(report["candidates"][:15], start=1):
        print(
            f"{i:2}. {candidate['id_hex']} {candidate['field']} "
            f"score={candidate['score']:.4f} r2={candidate['r2']:.4f} "
            f"{candidate['hypothesis']}"
        )


if __name__ == "__main__":
    main()
