from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from mgo_brain.main import app
from mgo_brain.recording import CANRecorder, format_candump
from mgo_brain.replay import CandumpReplayTransport
from mgo_brain.sources.can import CanFrame
from mgo_brain.survey import parse_candump
from mgo_brain.survey_sessions import SurveySessionStore


class FakeCAN:
    def __init__(self, frames):
        self.frames = list(frames)
        self.closed = False

    async def recv(self, timeout=None):
        if not self.frames:
            return None
        return self.frames.pop(0)

    async def close(self):
        self.closed = True


def make_frame(can_id, data, second):
    return CanFrame(
        arbitration_id=can_id,
        data=bytes.fromhex(data),
        timestamp=datetime.fromtimestamp(second, tz=timezone.utc),
    )


def test_format_and_parse_candump_roundtrip():
    frame = make_frame(0x310, "00010203", 1000.25)
    line = format_candump(frame, interface="can0")
    records, rejected = parse_candump(line)
    assert rejected == []
    assert len(records) == 1
    assert records[0].arbitration_id == 0x310
    assert records[0].data == bytes.fromhex("00010203")


def test_can_recorder_writes_all_frames(tmp_path):
    async def run():
        transport = FakeCAN([
            make_frame(0x100, "01", 1000.0),
            make_frame(0x200, "AABB", 1000.1),
            make_frame(0x310, "0001", 1000.2),
        ])
        recorder = CANRecorder(transport, interface="can0")
        output = tmp_path / "capture.log"
        result = await recorder.record(output, frame_limit=3)
        await recorder.close()
        return result, output, transport.closed

    result, output, closed = asyncio.run(run())
    assert result.frames == 3
    assert closed is True
    records, rejected = parse_candump(output.read_text(encoding="utf-8"))
    assert rejected == []
    assert [x.arbitration_id for x in records] == [0x100, 0x200, 0x310]


def test_replay_transport_preserves_order_and_payload(tmp_path):
    path = tmp_path / "capture.log"
    path.write_text(
        "(1000.000000) can0 100#01\n"
        "(1000.100000) can0 200#AABB\n",
        encoding="utf-8",
    )

    async def run():
        replay = CandumpReplayTransport.from_file(path, speed=0)
        a = await replay.recv()
        b = await replay.recv()
        c = await replay.recv()
        await replay.close()
        return a, b, c, replay.closed

    a, b, c, closed = asyncio.run(run())
    assert a.arbitration_id == 0x100
    assert a.data == b"\x01"
    assert b.arbitration_id == 0x200
    assert b.data == bytes.fromhex("AABB")
    assert c is None
    assert closed is True


def test_survey_session_store_persists_evidence(tmp_path):
    baseline = "\n".join(
        f"({1000+i/10:.1f}) can0 310#0000000000000000"
        for i in range(10)
    )
    action = "\n".join(
        f"({1002+i/10:.1f}) can0 310#0001000000000000"
        for i in range(10)
    )
    store = SurveySessionStore(tmp_path / "surveys")
    manifest = store.create(
        label="driver door open",
        baseline=baseline,
        action=action,
        notes="ignition on, stationary",
    )

    assert manifest["candidate_count"] >= 1
    assert manifest["top_candidate"]["id_hex"] == "0x310"

    loaded = store.get(manifest["id"])
    assert loaded is not None
    assert loaded["label"] == "driver door open"
    assert loaded["analysis"]["candidates"][0]["id_hex"] == "0x310"

    for kind in ("baseline", "action", "analysis", "dbc"):
        path = store.file_path(manifest["id"], kind)
        assert path is not None
        assert path.exists()


def test_survey_session_store_rejects_path_traversal(tmp_path):
    store = SurveySessionStore(tmp_path / "surveys")
    assert store.get("../secret") is None
    assert store.file_path("../secret", "baseline") is None


def test_v052_commissioning_routes_exist():
    paths = {route.path for route in app.routes}
    assert "/api/v1/survey/sessions" in paths
    assert "/api/v1/survey/sessions/{session_id}" in paths
    assert "/api/v1/survey/sessions/{session_id}/files/{kind}" in paths
