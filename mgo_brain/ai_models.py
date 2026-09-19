from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class AskMGORequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    language: Literal["ru", "en"] = "ru"
    include_evidence: bool = False


class AskMGOResponse(BaseModel):
    answer: str
    provider: str
    model: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tools_used: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class EvidencePacket(BaseModel):
    language: Literal["ru", "en"] = "ru"
    question: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    selected_tools: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class AIProviderStatus(BaseModel):
    provider: Literal["local", "openai"]
    configured: bool
    model: str | None = None
    detail: str
