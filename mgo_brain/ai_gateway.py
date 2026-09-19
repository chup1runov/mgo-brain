from __future__ import annotations

import os
from typing import Any

from .ai_models import AIProviderStatus, AskMGOResponse, EvidencePacket
from .ai_provider import LocalEvidenceProvider, OpenAIResponsesProvider
from .ai_toolbox import MGOToolbox


class AIGateway:
    """Question router + evidence compressor + provider boundary."""

    def __init__(self, service, *, provider_name: str | None = None, provider=None):
        self.service = service
        self.toolbox = MGOToolbox(service)
        self.provider_name = (provider_name or os.environ.get("MGO_AI_PROVIDER", "local")).strip().lower()
        self.provider = provider or self._build_provider(self.provider_name)

    def _build_provider(self, name: str):
        if name == "local":
            return LocalEvidenceProvider()
        if name == "openai":
            return OpenAIResponsesProvider()
        raise ValueError(f"Unknown MGO_AI_PROVIDER: {name!r}")

    def status(self) -> AIProviderStatus:
        return self.provider.status()

    def tool_specs(self):
        return self.toolbox.specs()

    def build_evidence(self, question: str) -> EvidencePacket:
        tools = select_tools(question)
        evidence: dict[str, Any] = {}
        warnings: list[str] = []

        for name in tools:
            try:
                if name == "get_start_history":
                    result = self.toolbox.execute(name, limit=10)
                elif name == "get_recent_trips":
                    result = self.toolbox.execute(name, limit=5)
                elif name == "get_fault_events":
                    result = self.toolbox.execute(name, limit=30)
                else:
                    result = self.toolbox.execute(name)
                evidence[name] = _compact(result)
            except Exception as exc:
                warnings.append(f"{name}: {type(exc).__name__}: {exc}")

        return EvidencePacket(
            question=question,
            selected_tools=tools,
            evidence=evidence,
            warnings=warnings,
        )

    def ask(self, question: str, *, include_evidence: bool = False) -> AskMGOResponse:
        packet = self.build_evidence(question)
        response = self.provider.answer(packet)
        if not include_evidence:
            response.evidence = {}
        return response


def select_tools(question: str) -> list[str]:
    q = question.lower()
    selected = ["get_live_state"]

    def add(*names):
        for name in names:
            if name not in selected:
                selected.append(name)

    if any(x in q for x in ("завод", "запуск", "стартер", "свеч", "crank", "start", "glow")):
        add("get_start_history", "get_battery_health", "get_engine_health")

    if any(x in q for x in ("акб", "батар", "генератор", "заряд", "напряж", "battery", "alternator", "voltage")):
        add("get_battery_health", "get_start_history")

    if any(x in q for x in ("двиг", "масл", "давлен", "охлаж", "ож", "температур", "engine", "oil", "coolant")):
        add("get_engine_health", "get_fault_events")

    if any(x in q for x in ("cvt", "вариатор", "ремень", "трансмисс", "ratio")):
        add("get_cvt_health", "get_recent_trips", "get_fault_events")

    if any(x in q for x in ("поезд", "trip", "сравн", "истор", "месяц", "недел")):
        add("get_recent_trips", "get_baselines", "get_fault_events")

    if any(x in q for x in ("сервис", "обслуж", "масло менять", "ремень менять", "maintenance")):
        add("get_service_plan", "get_recent_trips")

    if any(x in q for x in ("ошиб", "неисправ", "fault", "alert", "warning", "почему")):
        add("get_fault_events", "get_baselines")

    if len(selected) == 1:
        add("get_engine_health", "get_cvt_health", "get_battery_health", "get_recent_trips")

    return selected[:7]


def _compact(value: Any, *, max_list: int = 20, depth: int = 0) -> Any:
    """Bound context size and remove accidental raw high-volume structures."""
    if depth > 6:
        return "<truncated>"
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if str(key).lower() in {"raw_can", "audio", "video", "samples_raw"}:
                continue
            result[str(key)] = _compact(item, max_list=max_list, depth=depth + 1)
        return result
    if isinstance(value, list):
        out = [_compact(x, max_list=max_list, depth=depth + 1) for x in value[:max_list]]
        if len(value) > max_list:
            out.append({"_truncated_items": len(value) - max_list})
        return out
    if isinstance(value, str) and len(value) > 4000:
        return value[:4000] + "…<truncated>"
    return value
