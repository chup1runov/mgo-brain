from __future__ import annotations

import json
from types import SimpleNamespace

from mgo_brain.ai_gateway import AIGateway, _compact, select_tools
from mgo_brain.ai_models import EvidencePacket
from mgo_brain.ai_provider import OpenAIResponsesProvider
from mgo_brain.service import MGOBrainService


def make_service(tmp_path):
    service = MGOBrainService(tmp_path)
    service.process_state(service.simulator.snapshot_at(20.0))
    return service


def test_router_selects_start_and_battery_evidence():
    tools = select_tools("Почему сегодня дольше заводился и просело напряжение АКБ?")
    assert "get_start_history" in tools
    assert "get_battery_health" in tools
    assert "get_engine_health" in tools
    assert len(tools) <= 7


def test_toolbox_has_no_vehicle_control_tools(tmp_path):
    gateway = AIGateway(make_service(tmp_path), provider_name="local")
    names = {tool.name for tool in gateway.tool_specs()}
    forbidden = {
        "send_can", "start_engine", "set_gear", "control_brake",
        "control_throttle", "control_glow", "disable_speed_limiter",
    }
    assert names.isdisjoint(forbidden)
    assert {"get_live_state", "get_engine_health", "get_cvt_health", "get_battery_health"} <= names


def test_local_ask_works_without_external_ai_and_hides_evidence_by_default(tmp_path):
    gateway = AIGateway(make_service(tmp_path), provider_name="local")
    response = gateway.ask("Что сейчас с аккумулятором?")
    assert response.provider == "local"
    assert response.answer
    assert "get_battery_health" in response.tools_used
    assert response.evidence == {}


def test_evidence_can_be_explicitly_included_for_engineering_debug(tmp_path):
    gateway = AIGateway(make_service(tmp_path), provider_name="local")
    response = gateway.ask("Как сейчас двигатель?", include_evidence=True)
    assert response.evidence
    assert "get_engine_health" in response.evidence


def test_compactor_drops_raw_high_volume_payloads_and_bounds_lists():
    compact = _compact({
        "raw_can": ["frame"] * 100,
        "audio": "x" * 10000,
        "normal": list(range(50)),
        "nested": {"video": "secret", "value": 5},
    }, max_list=5)
    assert "raw_can" not in compact
    assert "audio" not in compact
    assert "video" not in compact["nested"]
    assert compact["nested"]["value"] == 5
    assert len(compact["normal"]) == 6
    assert compact["normal"][-1]["_truncated_items"] == 45


class FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text="По данным MGO Brain отклонений не видно.")


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_provider_uses_responses_api_shape_without_network():
    client = FakeClient()
    provider = OpenAIResponsesProvider(
        model="gpt-5.6-terra",
        reasoning_effort="low",
        client=client,
    )
    packet = EvidencePacket(
        question="Что с вариатором?",
        selected_tools=["get_cvt_health"],
        evidence={"get_cvt_health": {"health": {"status": "NORMAL"}}},
    )
    response = provider.answer(packet)
    assert response.provider == "openai"
    assert response.model == "gpt-5.6-terra"
    assert "отклонений" in response.answer
    assert client.responses.kwargs["model"] == "gpt-5.6-terra"
    assert client.responses.kwargs["reasoning"] == {"effort": "low"}
    assert "evidence" in client.responses.kwargs["input"]


def test_openai_provider_redacts_precise_location_by_default():
    client = FakeClient()
    provider = OpenAIResponsesProvider(client=client, allow_location=False)
    packet = EvidencePacket(
        question="Где машина?",
        selected_tools=["get_live_state"],
        evidence={
            "get_live_state": {
                "signals": {
                    "position.latitude": {"value": 57.7, "quality": "GOOD", "source": "gnss"},
                    "position.longitude": {"value": 12.0, "quality": "GOOD", "source": "gnss"},
                    "vehicle.speed": {"value": 20, "quality": "GOOD", "source": "can.bfi"},
                }
            }
        },
    )
    response = provider.answer(packet)
    sent = json.loads(client.responses.kwargs["input"].split("\n\n", 1)[1])
    lat = sent["evidence"]["get_live_state"]["signals"]["position.latitude"]
    lon = sent["evidence"]["get_live_state"]["signals"]["position.longitude"]
    assert lat["quality"] == "REDACTED"
    assert lon["quality"] == "REDACTED"
    assert sent["evidence"]["get_live_state"]["signals"]["vehicle.speed"]["value"] == 20
    assert any("координаты" in warning.lower() for warning in response.warnings)


def test_openai_provider_status_with_injected_client_is_configured():
    provider = OpenAIResponsesProvider(client=FakeClient())
    status = provider.status()
    assert status.provider == "openai"
    assert status.configured is True


def test_ai_routes_exist():
    from mgo_brain.main import app
    paths = {route.path for route in app.routes}
    assert "/api/v1/ai/status" in paths
    assert "/api/v1/ai/tools" in paths
    assert "/api/v1/ai/evidence" in paths
    assert "/api/v1/ai/ask" in paths
