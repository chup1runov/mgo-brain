from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from .ai_models import AIProviderStatus, AskMGOResponse, EvidencePacket


SYSTEM_INSTRUCTIONS_RU = """Ты диагностический помощник MGO Brain для Microcar M.Go.
Отвечай по-русски, кратко и инженерно.
Используй только предоставленные данные.
Всегда учитывай quality/source. STALE/MISSING/INVALID не считаются текущим измерением.
Отделяй наблюдение от гипотезы.
Не утверждай неисправность без достаточных данных.
Не предлагай управление тормозами, рулём, стартером, D/N/R, ограничителем скорости или другими safety-critical системами.
Если есть CRITICAL/ATTENTION от локального deterministic engine, не занижай его важность.
"""


class AIProvider(ABC):
    name: str

    @abstractmethod
    def status(self) -> AIProviderStatus:
        raise NotImplementedError

    @abstractmethod
    def answer(self, packet: EvidencePacket) -> AskMGOResponse:
        raise NotImplementedError


class LocalEvidenceProvider(AIProvider):
    name = "local"

    def status(self) -> AIProviderStatus:
        return AIProviderStatus(
            provider="local",
            configured=True,
            model=None,
            detail="Local deterministic/evidence fallback. No external AI or API key required.",
        )

    def answer(self, packet: EvidencePacket) -> AskMGOResponse:
        evidence = packet.evidence
        warnings = list(packet.warnings)
        lines: list[str] = []

        health = evidence.get("get_engine_health") or evidence.get("get_battery_health") or evidence.get("get_cvt_health")
        if health and isinstance(health, dict):
            item = health.get("health") or {}
            status = item.get("status")
            if status:
                lines.append(f"Статус: {status}.")

        if "get_start_history" in evidence:
            starts = evidence["get_start_history"].get("starts", [])
            if starts:
                latest = starts[0]
                pieces = []
                if latest.get("starter_duration_s") is not None:
                    pieces.append(f"прокрутка {latest['starter_duration_s']:.2f} с")
                if latest.get("min_crank_voltage_v") is not None:
                    pieces.append(f"минимум АКБ {latest['min_crank_voltage_v']:.2f} В")
                if latest.get("cranking_rpm") is not None:
                    pieces.append(f"{latest['cranking_rpm']:.0f} об/мин при прокрутке")
                if pieces:
                    lines.append("Последний запуск: " + ", ".join(pieces) + ".")

        if "get_battery_health" in evidence:
            signals = evidence["get_battery_health"].get("signals", {})
            v = signals.get("electrical.battery_voltage", {})
            if v.get("value") is not None and v.get("quality") == "GOOD":
                lines.append(
                    f"Напряжение сейчас: {v['value']} {v.get('unit') or 'В'} "
                    f"({v.get('quality')}, источник {v.get('source')})."
                )

        if "get_cvt_health" in evidence:
            signals = evidence["get_cvt_health"].get("signals", {})
            dev = signals.get("transmission.cvt_ratio_deviation", {})
            if dev.get("value") is not None and dev.get("quality") == "GOOD":
                lines.append(
                    f"Отклонение CVT ratio: {dev['value']}% "
                    f"({dev.get('quality')}, источник {dev.get('source')})."
                )

        active = evidence.get("get_live_state", {}).get("signals", {})
        unusable = [
            name for name, value in active.items()
            if value.get("quality") in {"STALE", "MISSING", "INVALID", "UNVERIFIED", "SUSPECT"}
        ]
        if unusable:
            warnings.append("Часть запрошенных данных не является текущей: " + ", ".join(unusable[:8]))

        if not lines:
            lines.append("Данных достаточно только для формирования evidence-пакета; внешняя AI-модель не подключена.")
        lines.append("Это локальный fallback: вывод ограничен доступными измерениями и детерминированными статусами.")

        if packet.language == "en":
            lines = ["Local evidence report. " + str((health or {}).get("health", {}).get("status", "UNKNOWN")),
                     "No cloud model was used. Unverified or stale readings are not current evidence."]
        return AskMGOResponse(
            answer=" ".join(lines),
            provider=self.name,
            tools_used=list(packet.selected_tools),
            evidence=packet.evidence,
            warnings=warnings,
        )


class OpenAIResponsesProvider(AIProvider):
    name = "openai"

    def __init__(
        self,
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        allow_location: bool | None = None,
        client: Any | None = None,
    ):
        self.model = model or os.environ.get("MGO_AI_MODEL", "")
        self.reasoning_effort = reasoning_effort or os.environ.get("MGO_AI_REASONING", "low")
        if allow_location is None:
            allow_location = os.environ.get("MGO_AI_ALLOW_LOCATION", "0").lower() in {"1", "true", "yes", "on"}
        self.allow_location = bool(allow_location)
        self._client = client

    def _client_or_raise(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise RuntimeError("OpenAI SDK is not installed. Install mgo-brain[ai].") from exc
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        self._client = OpenAI(timeout=20.0, max_retries=0)
        return self._client

    def status(self) -> AIProviderStatus:
        try:
            import importlib.util
            sdk = importlib.util.find_spec("openai") is not None
        except Exception:
            sdk = False
        key = bool(os.environ.get("OPENAI_API_KEY")) or self._client is not None
        configured = bool(self.model) and (bool(sdk and key) or self._client is not None)
        location = "location allowed" if self.allow_location else "precise location redacted"
        detail = (
            f"Configured for OpenAI Responses API; {location}."
            if configured
            else f"Requires mgo-brain[ai] and OPENAI_API_KEY; {location}."
        )
        return AIProviderStatus(
            provider="openai",
            configured=configured,
            model=self.model,
            detail=detail,
        )

    def answer(self, packet: EvidencePacket) -> AskMGOResponse:
        if not self.model:
            raise RuntimeError("Set MGO_AI_MODEL to an API model available to your account")
        client = self._client_or_raise()
        evidence = packet.evidence if self.allow_location else _redact_precise_location(packet.evidence)
        payload = {
            "question": packet.question,
            "tools_used": packet.selected_tools,
            "warnings": packet.warnings,
            "evidence": evidence,
        }
        response = client.responses.create(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            instructions=SYSTEM_INSTRUCTIONS_RU + ("\nAnswer in English." if packet.language == "en" else ""),
            store=False,
            max_output_tokens=1200,
            input=(
                "Проанализируй вопрос пользователя и evidence-пакет MGO Brain. "
                "Не выдумывай отсутствующие значения.\n\n"
                + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            ),
        )
        text = str(getattr(response, "output_text", "") or "").strip()
        if not text:
            raise RuntimeError("OpenAI Responses API returned no output_text.")
        warnings = list(packet.warnings)
        if not self.allow_location:
            warnings.append("Точные GNSS-координаты не передавались внешнему AI.")
        return AskMGOResponse(
            answer=text,
            provider=self.name,
            model=self.model,
            tools_used=list(packet.selected_tools),
            evidence=evidence,
            warnings=warnings,
        )


def _redact_precise_location(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str in {"position.latitude", "position.longitude"}:
                out[key_str] = {
                    "value": None,
                    "quality": "REDACTED",
                    "source": None,
                }
            else:
                out[key_str] = _redact_precise_location(item)
        return out
    if isinstance(value, list):
        return [_redact_precise_location(x) for x in value]
    return value
