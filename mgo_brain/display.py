from __future__ import annotations

import os
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


DEFAULT_BROWSERS = (
    "chromium-browser",
    "chromium",
    "google-chrome",
    "google-chrome-stable",
)


@dataclass(frozen=True)
class KioskSettings:
    url: str = "http://127.0.0.1:8080/?kiosk=1"
    health_url: str = "http://127.0.0.1:8080/health"
    wait_timeout_s: float = 90.0
    poll_interval_s: float = 1.0
    browser: str | None = None


def find_browser(
    preferred: str | None = None,
    *,
    which: Callable[[str], str | None] = shutil.which,
) -> str:
    if preferred:
        path = which(preferred)
        if path:
            return path
        if os.path.isabs(preferred) and os.path.exists(preferred):
            return preferred
        raise FileNotFoundError(f"Browser not found: {preferred}")

    for candidate in DEFAULT_BROWSERS:
        path = which(candidate)
        if path:
            return path
    raise FileNotFoundError(
        "No supported Chromium/Chrome browser found. "
        "Set MGO_KIOSK_BROWSER or install Chromium."
    )


def build_kiosk_command(browser: str, url: str) -> list[str]:
    return [
        browser,
        "--kiosk",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-infobars",
        "--disable-translate",
        "--disable-features=Translate",
        "--overscroll-history-navigation=0",
        "--check-for-update-interval=31536000",
        url,
    ]


def wait_for_health(
    url: str,
    *,
    timeout_s: float = 90.0,
    poll_interval_s: float = 1.0,
    opener=urllib.request.urlopen,
    sleeper=time.sleep,
    clock=time.monotonic,
) -> bool:
    deadline = clock() + timeout_s
    while clock() <= deadline:
        try:
            with opener(url, timeout=min(2.0, max(0.1, poll_interval_s))) as response:
                status = getattr(response, "status", 200)
                if 200 <= int(status) < 300:
                    return True
        except (OSError, urllib.error.URLError, ValueError):
            pass
        sleeper(poll_interval_s)
    return False
