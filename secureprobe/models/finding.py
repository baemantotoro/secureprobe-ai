"""Agent finding and verification models for SecureProbe AI."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import AssessmentType, Severity, ValidationStatus


class SecureProbeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


VerificationDecision = Literal[
    "ACCEPT_TOOL_VERIFIED",
    "REQUEST_ADDITIONAL_TOOL",
    "REQUEST_MANUAL_REVIEW",
    "REJECT",
]


class CandidateFinding(SecureProbeModel):
    candidate_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    severity: Severity
    location: str = Field(min_length=1)
    reasoning_summary: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list, min_length=1)
    verification_required: bool = False


class VerificationRequest(SecureProbeModel):
    verification_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    decision: VerificationDecision
    required_capability: str | None = None
    reason: str = Field(min_length=1)
    round: int = Field(ge=1)


class Finding(SecureProbeModel):
    finding_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    vulnerability_name: str = Field(min_length=1)
    severity: Severity
    assessment_type: AssessmentType
    location: str = Field(min_length=1)
    description: str = Field(min_length=1)
    cause: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list, min_length=1)
    owasp_mapping: list[str] = Field(default_factory=list)
    cwe_mapping: list[str] = Field(default_factory=list)
    impact: str = Field(min_length=1)
    remediation: str = Field(min_length=1)
    developer_guide: str = Field(min_length=1)
    ai_reasoning_summary: str = Field(min_length=1)
    validation_status: ValidationStatus
