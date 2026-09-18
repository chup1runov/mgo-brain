from __future__ import annotations

import json
from pathlib import Path

from .doctor import run_doctor
from .runtime import RuntimeSettings


def main():
    root = Path(__file__).resolve().parent.parent
    settings = RuntimeSettings.from_env(root)
    report = run_doctor(settings)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
