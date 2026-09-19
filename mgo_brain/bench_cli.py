from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bench_smoke import run_temporary_bench_smoke
from .sources.bench import BENCH_SCENARIOS


def main():
    parser = argparse.ArgumentParser(description="Run the complete MGO Brain virtual integration bench.")
    parser.add_argument("--scenario", choices=BENCH_SCENARIOS, default="normal")
    parser.add_argument("--signal-registry", type=Path, default=Path("config/signals-v1.json"))
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = run_temporary_bench_smoke(
        signal_registry_path=args.signal_registry,
        scenario=args.scenario,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    if not all(report["checks"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
