"""Agent event models for SecureProbe AI."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SecureProbeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


AgentEventType = Literal[
    "ASSESSMENT_CREATED",
    "VALIDATION_COMPLETED",
    "OBSERVATION_COMPLETED",
    "PLAN_CREATED",
    "TOOL_SELECTED",
    "TOOL_EXECUTED",
    "CANDIDATE_CREATED",
    "VERIFICATION_REQUESTED",
    "FINDING_CREATED",
    "REPORT_CREATED",
    "ASSESSMENT_COMPLETED",
]


class AgentEvent(SecureProbeModel):
    event_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    event_type: AgentEventType
    timestamp: datetime
    test_id: str | None = None
    tool_name: str | None = None
    summary: str = Field(min_length=1)
