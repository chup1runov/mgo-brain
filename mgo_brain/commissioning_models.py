from __future__ import annotations

from pydantic import BaseModel, Field


class SurveySessionCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    baseline: str
    action: str
    notes: str = Field(default="", max_length=4000)
    max_candidates: int = Field(default=25, ge=1, le=200)
