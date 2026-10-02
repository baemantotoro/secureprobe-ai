"""Evidence data models for SecureProbe AI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SecureProbeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Evidence(SecureProbeModel):
    evidence_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    source: str = Field(min_length=1)
    location: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
