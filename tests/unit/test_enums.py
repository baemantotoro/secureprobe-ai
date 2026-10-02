from secureprobe.models import (
    AssessmentStatus,
    AssessmentType,
    ExecutionStatus,
    RiskLevel,
    Severity,
    ValidationStatus,
)


def test_assessment_type_values():
    assert {item.value for item in AssessmentType} == {"WEB", "SOURCE"}


def test_assessment_status_values():
    assert {item.value for item in AssessmentStatus} == {
        "CREATED",
        "VALIDATING",
        "OBSERVING",
        "PLANNING",
        "SELECTING_TOOL",
        "EXECUTING",
        "ANALYZING",
        "VERIFYING",
        "REPORTING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
        "BLOCKED",
    }


def test_risk_level_values():
    assert {item.value for item in RiskLevel} == {"PASSIVE", "ACTIVE"}


def test_execution_status_values():
    assert {item.value for item in ExecutionStatus} == {
        "SUCCESS",
        "FAILED",
        "TIMEOUT",
        "BLOCKED",
        "UNSUPPORTED",
    }


def test_validation_status_values():
    assert {item.value for item in ValidationStatus} == {
        "UNVERIFIED",
        "TOOL_VERIFIED",
        "MANUAL_REQUIRED",
        "MANUAL_VERIFIED",
        "REJECTED",
    }


def test_severity_values():
    assert {item.value for item in Severity} == {
        "INFO",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }


def test_enums_are_string_compatible():
    assert isinstance(AssessmentType.WEB, str)
    assert isinstance(AssessmentStatus.CREATED, str)
    assert isinstance(RiskLevel.PASSIVE, str)
    assert isinstance(ExecutionStatus.SUCCESS, str)
    assert isinstance(ValidationStatus.UNVERIFIED, str)
    assert isinstance(Severity.INFO, str)

    assert AssessmentType.WEB.value == "WEB"
    assert AssessmentStatus.COMPLETED.value == "COMPLETED"
    assert RiskLevel.PASSIVE.value == "PASSIVE"
    assert ExecutionStatus.SUCCESS.value == "SUCCESS"
    assert ValidationStatus.TOOL_VERIFIED.value == "TOOL_VERIFIED"
    assert Severity.CRITICAL.value == "CRITICAL"
