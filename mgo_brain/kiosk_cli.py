from __future__ import annotations

import argparse
import os
from pathlib import Path

from .display import KioskSettings, build_kiosk_command, find_browser, wait_for_health


def main():
    defaults = KioskSettings(
        url=os.environ.get("MGO_KIOSK_URL", KioskSettings.url),
        health_url=os.environ.get("MGO_KIOSK_HEALTH_URL", KioskSettings.health_url),
        wait_timeout_s=float(os.environ.get("MGO_KIOSK_WAIT_TIMEOUT", KioskSettings.wait_timeout_s)),
        poll_interval_s=float(os.environ.get("MGO_KIOSK_POLL_INTERVAL", KioskSettings.poll_interval_s)),
        browser=os.environ.get("MGO_KIOSK_BROWSER") or None,
    )

    parser = argparse.ArgumentParser(description="Wait for MGO Brain and launch its dashboard in Chromium kiosk mode.")
    parser.add_argument("--url", default=defaults.url)
    parser.add_argument("--health-url", default=defaults.health_url)
    parser.add_argument("--wait-timeout", type=float, default=defaults.wait_timeout_s)
    parser.add_argument("--poll-interval", type=float, default=defaults.poll_interval_s)
    parser.add_argument("--browser", default=defaults.browser)
    parser.add_argument("--print-command", action="store_true")
    args = parser.parse_args()

    browser = find_browser(args.browser)
    command = build_kiosk_command(browser, args.url)

    if args.print_command:
        print(" ".join(command))
        return

    if not wait_for_health(
        args.health_url,
        timeout_s=args.wait_timeout,
        poll_interval_s=args.poll_interval,
    ):
        raise SystemExit(f"MGO Brain health endpoint did not become ready: {args.health_url}")

    os.execv(browser, command)


if __name__ == "__main__":
    main()
