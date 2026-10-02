from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from secureprobe.models import (
    AgentEvent,
    AssessmentRequest,
    AssessmentResult,
    AssessmentScope,
    AssessmentType,
    CandidateFinding,
    Credentials,
    Evidence,
    ExecutionStatus,
    Finding,
    Severity,
    TestCase,
    ToolDefinition,
    ToolExecution,
    ValidationStatus,
    VerificationRequest,
)
from secureprobe.models.enums import (
    AssessmentStatus,
    RiskLevel,
)


def test_enum_invalid_values_are_rejected():
    with pytest.raises(ValueError):
        AssessmentType("INVALID")
    with pytest.raises(ValueError):
        AssessmentStatus("UNKNOWN")
    with pytest.raises(ValueError):
        RiskLevel("DANGEROUS")
    with pytest.raises(ValueError):
        ExecutionStatus("DONE")
    with pytest.raises(ValueError):
        ValidationStatus("CONFIRMED")
    with pytest.raises(ValueError):
        Severity("SEVERE")

    with pytest.raises(ValidationError):
        AssessmentRequest.model_validate({
            "assessment_type": "INVALID",
            "target_url": "https://example.com",
            "scope": {},
        })


def test_assessment_request_required_fields_and_auth_split():
    request = AssessmentRequest(
        assessment_type=AssessmentType.WEB,
        target_url="https://example.com",
        scope=AssessmentScope(),
        authorization_confirmed=False,
    )
    assert request.authorization_confirmed is False

    source_request = AssessmentRequest(
        assessment_type=AssessmentType.SOURCE,
        source_directory="/tmp/project",
        scope=AssessmentScope(),
    )
    assert source_request.source_directory == "/tmp/project"

    with pytest.raises(ValidationError):
        AssessmentRequest(
            assessment_type=AssessmentType.WEB,
            scope=AssessmentScope(),
            authorization_confirmed=False,
        )

    with pytest.raises(ValidationError):
        AssessmentRequest(
            assessment_type=AssessmentType.SOURCE,
            scope=AssessmentScope(),
        )


def test_credentials_and_extra_field_rejections():
    credentials = Credentials(username="alice", password_ref="secret://vault/web-login")
    assert credentials.username == "alice"
    assert "password" not in Credentials.model_fields
    assert "raw_password" not in Credentials.model_fields

    with pytest.raises(ValidationError):
        Credentials(username="alice", password_ref="secret://vault/web-login", password="plain-text")

    with pytest.raises(ValidationError):
        AssessmentScope(unknown_field="x")


def test_assessment_result_boundaries_and_mutable_defaults():
    result = AssessmentResult(
        assessment_id="AR-100",
        assessment_type=AssessmentType.WEB,
        status=AssessmentStatus.CREATED,
        target="https://example.com",
        started_at="2026-10-03T00:00:00Z",
    )
    assert result.tests_planned == 0
    assert result.findings == []

    with pytest.raises(ValidationError):
        AssessmentResult(
            assessment_id="AR-101",
            assessment_type=AssessmentType.WEB,
            status=AssessmentStatus.FAILED,
            target="https://example.com",
            started_at="2026-10-03T00:00:00Z",
            tests_planned=-1,
        )

    result_a = AssessmentScope(allowed_hosts=["example.com"])
    result_b = AssessmentScope()
    result_a.allowed_hosts.append("example.org")
    assert result_b.allowed_hosts == []


def test_test_case_and_tool_validation_contracts():
    valid_case = TestCase(
        test_id="TC-001",
        category="WEB",
        target="https://example.com",
        reason="Check header security",
        required_capability="http_client",
        risk_level=RiskLevel.ACTIVE,
        priority=1,
        expected_evidence=["headers"],
    )
    assert valid_case.priority == 1

    with pytest.raises(ValidationError):
        TestCase(
            test_id="",
            category="WEB",
            target="https://example.com",
            reason="Check header security",
            required_capability="http_client",
            risk_level=RiskLevel.ACTIVE,
            priority=1,
        )

    with pytest.raises(ValidationError):
        TestCase(
            test_id="TC-000",
            category="WEB",
            target="https://example.com",
            reason="Check header security",
            required_capability="http_client",
            risk_level=RiskLevel.ACTIVE,
            priority=0,
        )

    with pytest.raises(ValidationError):
        ToolDefinition(
            tool_name="",
            description="Check HTTP responses",
            capabilities=["network"],
            assessment_types=[AssessmentType.WEB],
            risk_level=RiskLevel.ACTIVE,
            input_schema="{type: object}",
            output_schema="{type: object}",
        )

    with pytest.raises(ValidationError):
        ToolDefinition(
            tool_name="http_probe",
            description="Check HTTP responses",
            capabilities=[],
            assessment_types=[AssessmentType.WEB],
            risk_level=RiskLevel.ACTIVE,
            input_schema="{type: object}",
            output_schema="{type: object}",
        )

    with pytest.raises(ValidationError):
        ToolDefinition(
            tool_name="http_probe",
            description="Check HTTP responses",
            capabilities=["network"],
            assessment_types=["INVALID"],
            risk_level=RiskLevel.ACTIVE,
            input_schema="{type: object}",
            output_schema="{type: object}",
        )


def test_tool_execution_and_evidence_contracts():
    execution = ToolExecution(
        execution_id="EX-001",
        test_id="TC-001",
        tool_name="http_probe",
        input={"url": "https://example.com"},
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        duration_ms=0,
        output={"status": 200},
    )
    assert execution.duration_ms == 0

    with pytest.raises(ValidationError):
        ToolExecution(
            execution_id="EX-002",
            test_id="TC-002",
            tool_name="http_probe",
            status="DONE",
            started_at=datetime.now(timezone.utc),
            output={},
        )

    with pytest.raises(ValidationError):
        ToolExecution(
            execution_id="EX-003",
            test_id="TC-003",
            tool_name="http_probe",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.now(timezone.utc),
            duration_ms=-1,
            output={},
        )

    with pytest.raises(ValidationError):
        ToolExecution(
            execution_id="EX-004",
            test_id="TC-004",
            tool_name="http_probe",
            input="not-a-dict",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.now(timezone.utc),
            output={},
        )

    evidence = Evidence(
        evidence_id="EV-001",
        assessment_id="RUN-001",
        test_id="TC-001",
        execution_id="EX-001",
        type="response",
        source="http_probe",
        location="https://example.com",
        data={"status_code": 200},
        created_at=datetime.now(timezone.utc),
    )
    assert evidence.data["status_code"] == 200

    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="EV-002",
            assessment_id="RUN-001",
            test_id="TC-001",
            execution_id="EX-001",
            type="response",
            source="http_probe",
            location="https://example.com",
            data="raw-string",
            created_at=datetime.now(timezone.utc),
        )

    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="EV-003",
            assessment_id="RUN-001",
            test_id="TC-001",
            execution_id="EX-001",
            type="response",
            source="http_probe",
            location="https://example.com",
            data={},
            created_at="not-a-date",
        )


def test_finding_verification_and_event_validation_contracts():
    candidate = CandidateFinding(
        candidate_id="CF-001",
        test_id="TC-001",
        title="Missing security header",
        severity=Severity.MEDIUM,
        location="https://example.com",
        reasoning_summary="Header missing",
        evidence_ids=["EV-001"],
        verification_required=True,
    )
    assert candidate.evidence_ids == ["EV-001"]

    with pytest.raises(ValidationError):
        CandidateFinding(
            candidate_id="CF-002",
            test_id="TC-001",
            title="Missing security header",
            severity="SEVERE",
            location="https://example.com",
            reasoning_summary="Header missing",
            evidence_ids=[],
            verification_required=True,
        )

    with pytest.raises(ValidationError):
        VerificationRequest(
            verification_id="VR-001",
            candidate_id="CF-001",
            decision="APPROVE",
            reason="bad decision",
            round=1,
        )

    with pytest.raises(ValidationError):
        VerificationRequest(
            verification_id="VR-001",
            candidate_id="CF-001",
            decision="REJECT",
            reason="bad round",
            round=0,
        )

    finding = Finding(
        finding_id="F-001",
        assessment_id="RUN-001",
        test_id="TC-001",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="Headers missing",
        cause="Configuration oversight",
        evidence_ids=["EV-001"],
        owasp_mapping=[],
        cwe_mapping=[],
        impact="Client default risk",
        remediation="Add recommended headers",
        developer_guide="Document mitigation",
        ai_reasoning_summary="Confirmed by evidence",
        validation_status=ValidationStatus.TOOL_VERIFIED,
    )
    assert finding.validation_status == ValidationStatus.TOOL_VERIFIED

    with pytest.raises(ValidationError):
        Finding(
            finding_id="F-002",
            assessment_id="RUN-001",
            test_id="TC-001",
            vulnerability_name="Missing Security Headers",
            severity=Severity.MEDIUM,
            assessment_type=AssessmentType.WEB,
            location="https://example.com",
            description="Headers missing",
            cause="Configuration oversight",
            evidence_ids=[],
            owasp_mapping=[],
            cwe_mapping=[],
            impact="Client default risk",
            remediation="Add recommended headers",
            developer_guide="Document mitigation",
            ai_reasoning_summary="Confirmed by evidence",
            validation_status=ValidationStatus.TOOL_VERIFIED,
        )

    event = AgentEvent(
        event_id="AE-001",
        assessment_id="RUN-001",
        event_type="PLAN_CREATED",
        timestamp=datetime.now(timezone.utc),
        summary="Plan created for the HTTP check",
    )
    assert event.event_type == "PLAN_CREATED"

    with pytest.raises(ValidationError):
        AgentEvent(
            event_id="AE-002",
            assessment_id="RUN-001",
            event_type="UNKNOWN",
            timestamp=datetime.now(timezone.utc),
            summary="Bad event",
        )

    with pytest.raises(ValidationError):
        AgentEvent(
            event_id="AE-003",
            assessment_id="RUN-001",
            event_type="PLAN_CREATED",
            timestamp="tomorrow",
            summary="Bad timestamp",
        )


def test_json_round_trip_and_whitespace_rules():
    payload = AssessmentRequest(
        assessment_type=AssessmentType.WEB,
        target_url="https://example.com",
        scope=AssessmentScope(allowed_hosts=["example.com"]),
        authorization_confirmed=False,
    ).model_dump(mode="json")
    assert payload["assessment_type"] == "WEB"
    assert payload["scope"]["allowed_hosts"] == ["example.com"]

    restored = AssessmentRequest.model_validate(payload)
    assert restored.target_url == "https://example.com"

    finding = Finding(
        finding_id="F-001",
        assessment_id="RUN-001",
        test_id="TC-001",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="Headers missing",
        cause="Configuration oversight",
        evidence_ids=["EV-001"],
        owasp_mapping=[],
        cwe_mapping=[],
        impact="Client default risk",
        remediation="Add recommended headers",
        developer_guide="Document mitigation",
        ai_reasoning_summary="Confirmed by evidence",
        validation_status=ValidationStatus.TOOL_VERIFIED,
    )
    dumped = finding.model_dump(mode="json")
    assert dumped["severity"] == "MEDIUM"
    assert Finding.model_validate(dumped).finding_id == "F-001"

    with pytest.raises(ValidationError):
        TestCase(
            test_id="   ",
            category="WEB",
            target="https://example.com",
            reason="Check header security",
            required_capability="http_client",
            risk_level=RiskLevel.ACTIVE,
            priority=1,
        )

    with pytest.raises(ValidationError):
        ToolDefinition(
            tool_name="   ",
            description="Check HTTP responses",
            capabilities=["network"],
            assessment_types=[AssessmentType.WEB],
            risk_level=RiskLevel.ACTIVE,
            input_schema="{type: object}",
            output_schema="{type: object}",
        )
