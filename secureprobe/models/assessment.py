"""Assessment-related Pydantic models for SecureProbe AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import AssessmentStatus, AssessmentType


class SecureProbeModel(BaseModel):
    """Common validation settings for the assessment model layer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AssessmentScope(SecureProbeModel):
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    deny_paths: list[str] = Field(default_factory=list)
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)


class Credentials(SecureProbeModel):
    username: str = Field(min_length=1)
    password_ref: str = Field(min_length=1)


class AssessmentRequest(SecureProbeModel):
    assessment_type: AssessmentType
    target_url: str | None = None
    source_directory: str | None = None
    scope: AssessmentScope = Field(default_factory=AssessmentScope)
    authorization_confirmed: bool = False
    credentials: Credentials | None = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "AssessmentRequest":
        if self.assessment_type == AssessmentType.WEB:
            if not self.target_url:
                raise ValueError("target_url is required for WEB assessment")
            if self.authorization_confirmed is not True:
                raise ValueError("authorization_confirmed must be true for WEB assessment")
        elif self.assessment_type == AssessmentType.SOURCE:
            if not self.source_directory:
                raise ValueError("source_directory is required for SOURCE assessment")

        return self


class AssessmentError(SecureProbeModel):
    error_id: str
    phase: str
    code: str
    message: str
    retryable: bool = False
    tool_name: str | None = None
    test_id: str | None = None


class AssessmentRun(SecureProbeModel):
    assessment_id: str = Field(default_factory=lambda: f"assessment-{uuid.uuid4().hex[:12]}")
    assessment_type: AssessmentType | None = None
    status: AssessmentStatus = AssessmentStatus.CREATED
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    request: AssessmentRequest
    errors: list[AssessmentError] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_assessment_type_from_request(self) -> "AssessmentRun":
        if self.assessment_type is None:
            self.assessment_type = self.request.assessment_type
        return self


class ValidationResult(SecureProbeModel):
    allowed: bool
    reason: str
    active_assessment_allowed: bool
    validated_scope: AssessmentScope | None = None


class AssessmentResult(SecureProbeModel):
    schema_version: str = "0.1"
    assessment_id: str
    assessment_type: AssessmentType
    status: AssessmentStatus
    target: str
    started_at: datetime
    finished_at: datetime | None = None
    tests_planned: int = Field(default=0, ge=0)
    tests_executed: int = Field(default=0, ge=0)
    findings: list[str] = Field(default_factory=list)
    manual_review_required: list[str] = Field(default_factory=list)
    errors: list[AssessmentError] = Field(default_factory=list)
    report_paths: dict[str, str] = Field(default_factory=dict)
