"""Agent planning models for SecureProbe AI."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import RiskLevel


class SecureProbeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TestCase(SecureProbeModel):
    __test__ = False

    test_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    target: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    required_capability: str = Field(min_length=1)
    risk_level: RiskLevel
    priority: int = Field(ge=1)
    expected_evidence: list[str] = Field(default_factory=list)


class TestPlan(SecureProbeModel):
    __test__ = False

    plan_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    tests: list[TestCase] = Field(default_factory=list)
