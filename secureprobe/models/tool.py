"""Tool selection and execution models for SecureProbe AI."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .enums import AssessmentType, ExecutionStatus, RiskLevel


class SecureProbeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ToolDefinition(SecureProbeModel):
    tool_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list, min_length=1)
    assessment_types: list[AssessmentType] = Field(default_factory=list, min_length=1)
    risk_level: RiskLevel
    input_schema: str = Field(min_length=1)
    output_schema: str = Field(min_length=1)


class ToolSelection(SecureProbeModel):
    selection_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    risk_level: RiskLevel


class ToolError(SecureProbeModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool = False


class ToolExecution(SecureProbeModel):
    execution_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    output: dict[str, Any] = Field(default_factory=dict)
    error: ToolError | None = None
