import pytest
from pydantic import ValidationError

from secureprobe.models import (
    AssessmentError,
    AssessmentRequest,
    AssessmentResult,
    AssessmentRun,
    AssessmentScope,
    AssessmentStatus,
    AssessmentType,
    Credentials,
    ValidationResult,
)


def test_assessment_scope_defaults():
    scope = AssessmentScope()

    assert scope.allowed_hosts == []
    assert scope.allowed_paths == []
    assert scope.deny_paths == []
    assert scope.include_paths == []
    assert scope.exclude_paths == []


def test_credentials_requires_reference_only():
    credentials = Credentials(username="alice", password_ref="secret://vault/web-login")

    assert credentials.username == "alice"
    assert credentials.password_ref.startswith("secret://")


def test_web_assessment_request_requires_target_and_authorization():
    with pytest.raises(ValidationError, match="target_url is required for WEB assessment"):
        AssessmentRequest(
            assessment_type=AssessmentType.WEB,
            scope=AssessmentScope(),
            authorization_confirmed=True,
        )

    with pytest.raises(ValidationError, match="authorization_confirmed must be true for WEB assessment"):
        AssessmentRequest(
            assessment_type=AssessmentType.WEB,
            target_url="https://example.com",
            scope=AssessmentScope(),
            authorization_confirmed=False,
        )


def test_source_assessment_request_requires_directory():
    with pytest.raises(ValidationError, match="source_directory is required for SOURCE assessment"):
        AssessmentRequest(
            assessment_type=AssessmentType.SOURCE,
            scope=AssessmentScope(),
        )

    request = AssessmentRequest(
        assessment_type=AssessmentType.SOURCE,
        source_directory="/tmp/project",
        scope=AssessmentScope(),
    )

    assert request.source_directory == "/tmp/project"


def test_assessment_run_defaults_and_errors():
    request = AssessmentRequest(
        assessment_type=AssessmentType.WEB,
        target_url="https://example.com",
        scope=AssessmentScope(),
        authorization_confirmed=True,
    )
    run = AssessmentRun(request=request)

    assert run.assessment_type == AssessmentType.WEB
    assert run.status == AssessmentStatus.CREATED
    assert run.finished_at is None
    assert run.errors == []
    assert run.request.assessment_type == AssessmentType.WEB


def test_validation_result_and_assessment_result_constraints():
    validation = ValidationResult(
        allowed=True,
        reason="scope approved",
        active_assessment_allowed=True,
        validated_scope=AssessmentScope(allowed_hosts=["example.com"]),
    )
    assert validation.allowed is True
    assert validation.validated_scope is not None

    error = AssessmentError(
        error_id="ERR-001",
        phase="execution",
        code="TIMEOUT",
        message="The scan timed out",
        retryable=True,
    )

    result = AssessmentResult(
        assessment_id="AR-001",
        assessment_type=AssessmentType.WEB,
        status=AssessmentStatus.COMPLETED,
        target="https://example.com",
        started_at="2026-10-03T00:00:00Z",
        finished_at="2026-10-03T00:05:00Z",
        tests_planned=3,
        tests_executed=2,
        findings=["one finding"],
        manual_review_required=["review this result"],
        errors=[error],
        report_paths={"summary": "reports/summary.json"},
    )

    assert result.status == AssessmentStatus.COMPLETED
    assert len(result.errors) == 1
    assert result.report_paths["summary"] == "reports/summary.json"

    with pytest.raises(ValidationError):
        AssessmentResult(
            assessment_id="AR-002",
            assessment_type=AssessmentType.WEB,
            status=AssessmentStatus.FAILED,
            target="https://example.com",
            started_at="2026-10-03T00:00:00Z",
            tests_planned=-1,
        )
