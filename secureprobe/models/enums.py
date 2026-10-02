"""Shared enums for SecureProbe AI domain models."""

from enum import Enum


class AssessmentType(str, Enum):
    WEB = "WEB"
    SOURCE = "SOURCE"


class AssessmentStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    OBSERVING = "OBSERVING"
    PLANNING = "PLANNING"
    SELECTING_TOOL = "SELECTING_TOOL"
    EXECUTING = "EXECUTING"
    ANALYZING = "ANALYZING"
    VERIFYING = "VERIFYING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class RiskLevel(str, Enum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


class ValidationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    TOOL_VERIFIED = "TOOL_VERIFIED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    MANUAL_VERIFIED = "MANUAL_VERIFIED"
    REJECTED = "REJECTED"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
