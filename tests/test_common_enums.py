from secureprobe.models import (
    AssessmentStatus,
    AssessmentType,
    ExecutionStatus,
    RiskLevel,
    Severity,
    ValidationStatus,
)


def test_common_enum_values():
    assert AssessmentType.WEB.value == "WEB"
    assert AssessmentType.SOURCE.value == "SOURCE"

    assert AssessmentStatus.CREATED.value == "CREATED"
    assert AssessmentStatus.COMPLETED.value == "COMPLETED"
    assert AssessmentStatus.BLOCKED.value == "BLOCKED"

    assert RiskLevel.PASSIVE.value == "PASSIVE"
    assert RiskLevel.ACTIVE.value == "ACTIVE"

    assert ExecutionStatus.SUCCESS.value == "SUCCESS"
    assert ExecutionStatus.UNSUPPORTED.value == "UNSUPPORTED"

    assert ValidationStatus.TOOL_VERIFIED.value == "TOOL_VERIFIED"
    assert ValidationStatus.MANUAL_REQUIRED.value == "MANUAL_REQUIRED"

    assert Severity.INFO.value == "INFO"
    assert Severity.CRITICAL.value == "CRITICAL"
