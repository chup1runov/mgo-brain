from __future__ import annotations

from pathlib import Path

from mgo_brain.display import build_kiosk_command, find_browser, wait_for_health


ROOT = Path(__file__).resolve().parent.parent


def test_build_kiosk_command_contains_expected_flags_and_url():
    cmd = build_kiosk_command("/usr/bin/chromium", "http://127.0.0.1:8080/?kiosk=1")
    assert cmd[0] == "/usr/bin/chromium"
    assert "--kiosk" in cmd
    assert "--disable-session-crashed-bubble" in cmd
    assert cmd[-1] == "http://127.0.0.1:8080/?kiosk=1"


def test_find_browser_honors_preferred_name():
    mapping = {"chromium": "/usr/bin/chromium"}
    assert find_browser("chromium", which=mapping.get) == "/usr/bin/chromium"


def test_wait_for_health_succeeds_after_initial_failure():
    calls = {"open": 0, "clock": 0.0}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def opener(url, timeout):
        calls["open"] += 1
        if calls["open"] < 2:
            raise OSError("not ready")
        return Response()

    def clock():
        return calls["clock"]

    def sleeper(seconds):
        calls["clock"] += seconds

    assert wait_for_health(
        "http://127.0.0.1:8080/health",
        timeout_s=5,
        poll_interval_s=1,
        opener=opener,
        sleeper=sleeper,
        clock=clock,
    ) is True
    assert calls["open"] == 2


def test_kiosk_deployment_templates_exist():
    unit = (ROOT / "deployment" / "systemd-user" / "mgo-brain-kiosk.service").read_text(encoding="utf-8")
    env = (ROOT / "deployment" / "kiosk.env.example").read_text(encoding="utf-8")
    assert "Restart=always" in unit
    assert "mgo-kiosk" in unit
    assert "MGO_KIOSK_URL=" in env


def test_ui_supports_kiosk_mode_and_wake_lock():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "kioskMode" in html
    assert "navigator.wakeLock.request('screen')" in html
    assert "classList.add('kiosk')" in html
