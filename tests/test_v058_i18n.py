from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_russian_is_default_ui_language():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="ru">' in html
    assert 'data-i18n="nav.home">ГЛАВНАЯ<' in html
    assert 'data-i18n="metric.speed">Скорость<' in html
    assert 'data-i18n="section.health">Состояние систем<' in html
    assert 'data-i18n="service.plan">Регламент обслуживания<' in html


def test_i18n_has_russian_and_english_fallback():
    js = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")
    assert "ru:" in js
    assert "en:" in js
    assert '"common.critical": "КРИТИЧНО"' in js
    assert '"common.critical": "CRITICAL"' in js
    assert '"mode.DRIVING": "ДВИЖЕНИЕ"' in js
    assert '"mode.DRIVING": "DRIVING"' in js


def test_manifest_declares_russian_default():
    manifest = json.loads((ROOT / "static" / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["lang"] == "ru"
    assert manifest["start_url"].endswith("lang=ru")
    assert "диагностика" in manifest["description"].lower()


def test_canonical_signal_names_remain_untranslated():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert 'data-sig="engine.oil_pressure"' in html
    assert 'data-sig="electrical.battery_voltage"' in html
    assert 'data-sig="transmission.cvt_ratio_deviation"' in html


def test_english_fallback_is_query_selectable():
    js = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")
    assert 'params.get("lang")' in js
    assert 'localStorage.getItem("mgo-lang")' in js
