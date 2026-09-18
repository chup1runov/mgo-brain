from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .backup import create_backup
from .runtime import RuntimeSettings


def main():
    root = Path(__file__).resolve().parent.parent
    settings = RuntimeSettings.from_env(root)

    parser = argparse.ArgumentParser(description="Create a consistent MGO Brain data/config backup.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(f"mgo-brain-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"),
    )
    args = parser.parse_args()

    result = create_backup(
        data_dir=settings.data_dir,
        config_dir=settings.config_dir,
        output=args.output,
    )
    print(f"backup: {result['path']}")
    print(f"size: {result['size_bytes']} bytes")


if __name__ == "__main__":
    main()
