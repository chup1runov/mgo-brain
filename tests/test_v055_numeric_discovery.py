from __future__ import annotations

import pytest

from mgo_brain.numeric_discovery import (
    discover_numeric_from_text,
    make_numeric_demo,
    parse_reference_csv,
)


def test_reference_csv_parser():
    samples, rejected = parse_reference_csv(
        "timestamp,value\n1000.0,0\n1000.2,12.5\n"
    )
    assert rejected == []
    assert len(samples) == 2
    assert samples[1].timestamp == pytest.approx(1000.2)
    assert samples[1].value == pytest.approx(12.5)


def test_numeric_demo_finds_encoded_speed_field():
    demo = make_numeric_demo()
    report = discover_numeric_from_text(
        demo["can_log"],
        demo["reference_csv"],
        label=demo["label"],
        min_samples=12,
    )
    assert report["candidates"]
    top = report["candidates"][0]
    assert top["id_hex"] == "0x420"
    assert top["offset"] == 0
    assert top["width"] == 2
    assert top["endian"] == "le"
    assert top["r2"] > 0.999
    assert top["slope"] == pytest.approx(0.05, rel=1e-5)
    assert abs(top["intercept"]) < 1e-6


def test_counter_noise_is_penalized():
    demo = make_numeric_demo()
    report = discover_numeric_from_text(
        demo["can_log"],
        demo["reference_csv"],
        label=demo["label"],
        min_samples=12,
        max_candidates=100,
    )
    speed = max(
        x["score"]
        for x in report["candidates"]
        if x["id_hex"] == "0x420" and x["offset"] == 0 and x["width"] == 2 and x["endian"] == "le"
    )
    counters = [x["score"] for x in report["candidates"] if x["id_hex"] == "0x201"]
    assert not counters or speed > max(counters)


def test_numeric_discovery_is_explicitly_hypothesis_only():
    demo = make_numeric_demo()
    report = discover_numeric_from_text(demo["can_log"], demo["reference_csv"])
    assert "statistical hypotheses" in report["warning"].lower()
