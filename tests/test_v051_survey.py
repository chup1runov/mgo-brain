from __future__ import annotations

from mgo_brain.survey import (
    analyze_text,
    parse_candump,
    parse_candump_line,
    sample_pair,
)


def test_parse_candump_common_formats():
    a = parse_candump_line("(123.456) can0 310#00010203")
    assert a is not None
    assert a.arbitration_id == 0x310
    assert a.data == bytes.fromhex("00010203")
    assert a.timestamp == 123.456

    b = parse_candump_line("can0 123 [4] 11 22 33 44")
    assert b is not None
    assert b.arbitration_id == 0x123
    assert b.data == bytes.fromhex("11223344")


def test_parse_reports_rejected_lines():
    records, rejected = parse_candump("can0 100#00\nthis is not candump\n")
    assert len(records) == 1
    assert rejected[0]["line"] == 2


def test_sample_pair_ranks_door_candidate_above_counter_noise():
    sample = sample_pair()
    report = analyze_text(sample["baseline"], sample["action"], label=sample["label"])
    assert report["candidates"]
    assert report["candidates"][0]["id_hex"] == "0x310"
    byte = report["candidates"][0]["changed_bytes"][0]
    assert byte["index"] == 1
    assert byte["baseline_top"]["hex"] == "00"
    assert byte["action_top"]["hex"] == "01"
    assert byte["modal_changed"] is True


def test_no_signal_layout_is_invented_in_dbc_draft():
    sample = sample_pair()
    report = analyze_text(sample["baseline"], sample["action"], label=sample["label"])
    dbc = report["draft_dbc"]
    assert "BO_ 784 MGO_310" in dbc
    assert "no signal layout decoded" in dbc
    assert "SG_" not in dbc


def test_presence_only_id_is_candidate():
    baseline = "\n".join(f"({i}.0) can0 100#00" for i in range(5))
    action = baseline + "\n" + "\n".join(f"({i}.1) can0 555#AABB" for i in range(5))
    report = analyze_text(baseline, action)
    by_id = {x["id_hex"]: x for x in report["candidates"]}
    assert by_id["0x555"]["only_in_action"] is True
    assert by_id["0x555"]["score"] > 0
