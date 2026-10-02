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
    TestPlan,
    ToolError,
    ToolExecution,
    ToolSelection,
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


@pytest.mark.parametrize(
    "missing_field",
    [
        "assessment_id",
        "assessment_type",
        "status",
        "target",
        "started_at",
    ],
)
def test_assessment_result_required_fields(missing_field):
    payload = {
        "assessment_id": "AR-200",
        "assessment_type": "WEB",
        "status": "CREATED",
        "target": "https://example.com",
        "started_at": "2026-10-03T00:00:00Z",
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        AssessmentResult.model_validate(payload)


@pytest.mark.parametrize(
    "missing_field",
    [
        "test_id",
        "category",
        "target",
        "reason",
        "required_capability",
        "risk_level",
        "priority",
    ],
)
def test_test_case_required_fields(missing_field):
    payload = {
        "test_id": "TC-200",
        "category": "WEB",
        "target": "https://example.com",
        "reason": "Check security headers",
        "required_capability": "http_client",
        "risk_level": "ACTIVE",
        "priority": 1,
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        TestCase.model_validate(payload)


def test_tool_selection_validation():
    valid = {
        "selection_id": "SEL-001",
        "test_id": "TC-001",
        "tool_name": "http_probe",
        "reason": "Best match",
        "risk_level": "ACTIVE",
    }
    assert ToolSelection.model_validate(valid).tool_name == "http_probe"

    missing = dict(valid)
    missing.pop("risk_level")
    with pytest.raises(ValidationError):
        ToolSelection.model_validate(missing)

    with pytest.raises(ValidationError):
        ToolSelection.model_validate({**valid, "risk_level": "UNSAFE"})


@pytest.mark.parametrize(
    "missing_field",
    [
        "execution_id",
        "test_id",
        "tool_name",
        "status",
        "started_at",
    ],
)
def test_tool_execution_required_fields(missing_field):
    payload = {
        "execution_id": "EX-200",
        "test_id": "TC-200",
        "tool_name": "http_probe",
        "status": "SUCCESS",
        "started_at": "2026-10-03T00:00:00Z",
        "output": {},
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        ToolExecution.model_validate(payload)


def test_tool_execution_output_type_and_tool_error_validation():
    with pytest.raises(ValidationError):
        ToolExecution.model_validate(
            {
                "execution_id": "EX-201",
                "test_id": "TC-201",
                "tool_name": "http_probe",
                "status": "SUCCESS",
                "started_at": "2026-10-03T00:00:00Z",
                "output": ["invalid"],
            }
        )

    with pytest.raises(ValidationError):
        ToolExecution.model_validate(
            {
                "execution_id": "EX-202",
                "test_id": "TC-202",
                "tool_name": "http_probe",
                "status": "SUCCESS",
                "started_at": "2026-10-03T00:00:00Z",
                "output": "raw-string",
            }
        )

    with pytest.raises(ValidationError):
        ToolError(code="", message="request timed out", retryable=True)
    with pytest.raises(ValidationError):
        ToolError(code="   ", message="request timed out", retryable=True)
    with pytest.raises(ValidationError):
        ToolError(code="HTTP_TIMEOUT", message="", retryable=True)
    with pytest.raises(ValidationError):
        ToolError(code="HTTP_TIMEOUT", message="   ", retryable=True)


@pytest.mark.parametrize(
    "missing_field",
    [
        "evidence_id",
        "assessment_id",
        "test_id",
        "execution_id",
        "type",
        "source",
        "location",
        "created_at",
    ],
)
def test_evidence_required_fields(missing_field):
    payload = {
        "evidence_id": "EV-200",
        "assessment_id": "RUN-200",
        "test_id": "TC-200",
        "execution_id": "EX-200",
        "type": "response",
        "source": "http_probe",
        "location": "https://example.com",
        "data": {"status_code": 200},
        "created_at": "2026-10-03T00:00:00Z",
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        Evidence.model_validate(payload)


def test_evidence_sensitive_field_rejection():
    payload = {
        "evidence_id": "EV-201",
        "assessment_id": "RUN-201",
        "test_id": "TC-201",
        "execution_id": "EX-201",
        "type": "response",
        "source": "http_probe",
        "location": "https://example.com",
        "data": {"status_code": 200},
        "created_at": "2026-10-03T00:00:00Z",
    }
    for key in ["password", "raw_token", "authorization_header", "api_key", "secret_key"]:
        with pytest.raises(ValidationError):
            Evidence.model_validate({**payload, key: "secret-value"})


@pytest.mark.parametrize(
    "missing_field",
    [
        "candidate_id",
        "test_id",
        "title",
        "severity",
        "location",
        "reasoning_summary",
        "evidence_ids",
    ],
)
def test_candidate_finding_required_fields(missing_field):
    payload = {
        "candidate_id": "CF-200",
        "test_id": "TC-200",
        "title": "Missing security header",
        "severity": "MEDIUM",
        "location": "https://example.com",
        "reasoning_summary": "Header missing",
        "evidence_ids": ["EV-200"],
        "verification_required": True,
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        CandidateFinding.model_validate(payload)


def test_candidate_finding_evidence_and_severity_validation():
    with pytest.raises(ValidationError):
        CandidateFinding.model_validate(
            {
                "candidate_id": "CF-201",
                "test_id": "TC-201",
                "title": "Missing security header",
                "severity": "MEDIUM",
                "location": "https://example.com",
                "reasoning_summary": "Header missing",
                "evidence_ids": [],
                "verification_required": True,
            }
        )

    with pytest.raises(ValidationError):
        CandidateFinding.model_validate(
            {
                "candidate_id": "CF-202",
                "test_id": "TC-202",
                "title": "Missing security header",
                "severity": "SEVERE",
                "location": "https://example.com",
                "reasoning_summary": "Header missing",
                "evidence_ids": ["EV-202"],
                "verification_required": True,
            }
        )


@pytest.mark.parametrize(
    "missing_field",
    [
        "finding_id",
        "assessment_id",
        "test_id",
        "vulnerability_name",
        "severity",
        "assessment_type",
        "location",
        "description",
        "cause",
        "evidence_ids",
        "impact",
        "remediation",
        "developer_guide",
        "ai_reasoning_summary",
        "validation_status",
    ],
)
def test_finding_required_fields(missing_field):
    payload = {
        "finding_id": "F-200",
        "assessment_id": "RUN-200",
        "test_id": "TC-200",
        "vulnerability_name": "Missing Security Headers",
        "severity": "MEDIUM",
        "assessment_type": "WEB",
        "location": "https://example.com",
        "description": "Headers missing",
        "cause": "Configuration oversight",
        "evidence_ids": ["EV-200"],
        "owasp_mapping": [],
        "cwe_mapping": [],
        "impact": "Client default risk",
        "remediation": "Add recommended headers",
        "developer_guide": "Document mitigation",
        "ai_reasoning_summary": "Confirmed by evidence",
        "validation_status": "TOOL_VERIFIED",
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        Finding.model_validate(payload)


def test_finding_invalid_enum_and_mapping_types():
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "finding_id": "F-201",
                "assessment_id": "RUN-201",
                "test_id": "TC-201",
                "vulnerability_name": "Missing Security Headers",
                "severity": "SEVERE",
                "assessment_type": "WEB",
                "location": "https://example.com",
                "description": "Headers missing",
                "cause": "Configuration oversight",
                "evidence_ids": ["EV-201"],
                "owasp_mapping": [],
                "cwe_mapping": [],
                "impact": "Client default risk",
                "remediation": "Add recommended headers",
                "developer_guide": "Document mitigation",
                "ai_reasoning_summary": "Confirmed by evidence",
                "validation_status": "TOOL_VERIFIED",
            }
        )

    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "finding_id": "F-202",
                "assessment_id": "RUN-202",
                "test_id": "TC-202",
                "vulnerability_name": "Missing Security Headers",
                "severity": "MEDIUM",
                "assessment_type": "DYNAMIC",
                "location": "https://example.com",
                "description": "Headers missing",
                "cause": "Configuration oversight",
                "evidence_ids": ["EV-202"],
                "owasp_mapping": [],
                "cwe_mapping": [],
                "impact": "Client default risk",
                "remediation": "Add recommended headers",
                "developer_guide": "Document mitigation",
                "ai_reasoning_summary": "Confirmed by evidence",
                "validation_status": "TOOL_VERIFIED",
            }
        )

    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "finding_id": "F-203",
                "assessment_id": "RUN-203",
                "test_id": "TC-203",
                "vulnerability_name": "Missing Security Headers",
                "severity": "MEDIUM",
                "assessment_type": "WEB",
                "location": "https://example.com",
                "description": "Headers missing",
                "cause": "Configuration oversight",
                "evidence_ids": ["EV-203"],
                "owasp_mapping": "A03:2021-Injection",
                "cwe_mapping": [],
                "impact": "Client default risk",
                "remediation": "Add recommended headers",
                "developer_guide": "Document mitigation",
                "ai_reasoning_summary": "Confirmed by evidence",
                "validation_status": "TOOL_VERIFIED",
            }
        )

    with pytest.raises(ValidationError):
        Finding.model_validate(
            {
                "finding_id": "F-204",
                "assessment_id": "RUN-204",
                "test_id": "TC-204",
                "vulnerability_name": "Missing Security Headers",
                "severity": "MEDIUM",
                "assessment_type": "WEB",
                "location": "https://example.com",
                "description": "Headers missing",
                "cause": "Configuration oversight",
                "evidence_ids": ["EV-204"],
                "owasp_mapping": [],
                "cwe_mapping": "CWE-89",
                "impact": "Client default risk",
                "remediation": "Add recommended headers",
                "developer_guide": "Document mitigation",
                "ai_reasoning_summary": "Confirmed by evidence",
                "validation_status": "TOOL_VERIFIED",
            }
        )


@pytest.mark.parametrize(
    "missing_field",
    [
        "event_id",
        "assessment_id",
        "event_type",
        "timestamp",
        "summary",
    ],
)
def test_agent_event_required_fields(missing_field):
    payload = {
        "event_id": "AE-200",
        "assessment_id": "RUN-200",
        "event_type": "PLAN_CREATED",
        "timestamp": "2026-10-03T00:00:00Z",
        "summary": "Plan created",
    }
    payload.pop(missing_field)
    with pytest.raises(ValidationError):
        AgentEvent.model_validate(payload)


def test_ground_truth_and_benchmark_and_internal_reasoning_rejected():
    finding_base = {
        "finding_id": "F-300",
        "assessment_id": "RUN-300",
        "test_id": "TC-300",
        "vulnerability_name": "Missing Security Headers",
        "severity": "MEDIUM",
        "assessment_type": "WEB",
        "location": "https://example.com",
        "description": "Headers missing",
        "cause": "Configuration oversight",
        "evidence_ids": ["EV-300"],
        "impact": "Client default risk",
        "remediation": "Add recommended headers",
        "developer_guide": "Document mitigation",
        "ai_reasoning_summary": "Confirmed by evidence",
        "validation_status": "TOOL_VERIFIED",
    }
    for key in ["ground_truth_id", "expected_ground_truth", "known_vulnerability"]:
        with pytest.raises(ValidationError):
            Finding.model_validate({**finding_base, key: "secret"})

    for key in ["benchmark_result", "zap_result", "semgrep_result"]:
        with pytest.raises(ValidationError):
            Finding.model_validate({**finding_base, key: {"status": "ok"}})

    for key in ["chain_of_thought", "full_reasoning", "hidden_reasoning", "internal_reasoning"]:
        with pytest.raises(ValidationError):
            CandidateFinding.model_validate(
                {
                    "candidate_id": "CF-300",
                    "test_id": "TC-300",
                    "title": "Missing security header",
                    "severity": "MEDIUM",
                    "location": "https://example.com",
                    "reasoning_summary": "Header missing",
                    "evidence_ids": ["EV-300"],
                    "verification_required": True,
                    key: "not allowed",
                }
            )

    for key in ["chain_of_thought", "full_reasoning", "hidden_reasoning", "internal_reasoning"]:
        with pytest.raises(ValidationError):
            Finding.model_validate({**finding_base, key: "not allowed"})

    with pytest.raises(ValidationError):
        Finding.model_validate({**finding_base, "validation_status": "CONFIRMED"})

    plan_base = {"plan_id": "PLAN-600", "assessment_id": "RUN-600", "tests": []}
    for key in ["ground_truth_id", "expected_ground_truth", "known_vulnerability"]:
        with pytest.raises(ValidationError):
            TestPlan.model_validate({**plan_base, key: "GT-01"})

    for key in ["benchmark_result", "zap_result", "semgrep_result"]:
        with pytest.raises(ValidationError):
            TestPlan.model_validate({**plan_base, key: {"status": "ok"}})


def test_mutable_defaults_are_isolated_in_agent_models():
    finding_a = Finding(
        finding_id="F-400",
        assessment_id="RUN-400",
        test_id="TC-400",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="Headers missing",
        cause="Configuration oversight",
        evidence_ids=["EV-400"],
        owasp_mapping=["A03:2021-Injection"],
        cwe_mapping=["CWE-89"],
        impact="Client default risk",
        remediation="Add recommended headers",
        developer_guide="Document mitigation",
        ai_reasoning_summary="Confirmed by evidence",
        validation_status=ValidationStatus.TOOL_VERIFIED,
    )
    finding_b = Finding(
        finding_id="F-401",
        assessment_id="RUN-401",
        test_id="TC-401",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="Headers missing",
        cause="Configuration oversight",
        evidence_ids=["EV-401"],
        owasp_mapping=[],
        cwe_mapping=[],
        impact="Client default risk",
        remediation="Add recommended headers",
        developer_guide="Document mitigation",
        ai_reasoning_summary="Confirmed by evidence",
        validation_status=ValidationStatus.TOOL_VERIFIED,
    )
    finding_a.owasp_mapping.append("A05:2021")
    finding_a.cwe_mapping.append("CWE-693")
    assert finding_b.owasp_mapping == []
    assert finding_b.cwe_mapping == []

    evidence_a = Evidence(
        evidence_id="EV-400",
        assessment_id="RUN-400",
        test_id="TC-400",
        execution_id="EX-400",
        type="response",
        source="http_probe",
        location="https://example.com",
        data={"status_code": 200},
        created_at=datetime.now(timezone.utc),
    )
    evidence_b = Evidence(
        evidence_id="EV-401",
        assessment_id="RUN-401",
        test_id="TC-401",
        execution_id="EX-401",
        type="response",
        source="http_probe",
        location="https://example.com",
        data={},
        created_at=datetime.now(timezone.utc),
    )
    evidence_a.data["status_code"] = 500
    assert evidence_b.data == {}


def test_json_serialization_and_round_trip_for_core_models():
    request = AssessmentRequest(
        assessment_type=AssessmentType.WEB,
        target_url="https://example.com",
        scope=AssessmentScope(allowed_hosts=["example.com"]),
        authorization_confirmed=False,
    )
    payload = request.model_dump(mode="json")
    assert payload["assessment_type"] == "WEB"
    assert AssessmentRequest.model_validate(payload).target_url == "https://example.com"

    finding = Finding(
        finding_id="F-500",
        assessment_id="RUN-500",
        test_id="TC-500",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="Headers missing",
        cause="Configuration oversight",
        evidence_ids=["EV-500"],
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
    assert Finding.model_validate(dumped).finding_id == "F-500"

    event = AgentEvent(
        event_id="AE-500",
        assessment_id="RUN-500",
        event_type="PLAN_CREATED",
        timestamp=datetime.now(timezone.utc),
        summary="Plan created for the HTTP check",
    )
    assert event.model_dump(mode="json")["event_type"] == "PLAN_CREATED"


@pytest.mark.parametrize(
    "value",
    ["not-a-date", "tomorrow"],
)
def test_datetime_validation_for_multiple_models(value):
    with pytest.raises(ValidationError):
        Evidence.model_validate(
            {
                "evidence_id": "EV-500",
                "assessment_id": "RUN-500",
                "test_id": "TC-500",
                "execution_id": "EX-500",
                "type": "response",
                "source": "http_probe",
                "location": "https://example.com",
                "data": {"status_code": 200},
                "created_at": value,
            }
        )

    with pytest.raises(ValidationError):
        AgentEvent.model_validate(
            {
                "event_id": "AE-501",
                "assessment_id": "RUN-500",
                "event_type": "PLAN_CREATED",
                "timestamp": value,
                "summary": "Plan created",
            }
        )


@pytest.mark.parametrize(
    "field_value",
    ["   ", ""],
)
def test_whitespace_only_values_are_rejected(field_value):
    with pytest.raises(ValidationError):
        TestCase(
            test_id=field_value,
            category="WEB",
            target="https://example.com",
            reason="Check header security",
            required_capability="http_client",
            risk_level=RiskLevel.ACTIVE,
            priority=1,
        )

    with pytest.raises(ValidationError):
        ToolDefinition(
            tool_name=field_value,
            description="Check HTTP responses",
            capabilities=["network"],
            assessment_types=[AssessmentType.WEB],
            risk_level=RiskLevel.ACTIVE,
            input_schema="{type: object}",
            output_schema="{type: object}",
        )

    with pytest.raises(ValidationError):
        Finding(
            finding_id=field_value,
            assessment_id="RUN-500",
            test_id="TC-500",
            vulnerability_name="Missing Security Headers",
            severity=Severity.MEDIUM,
            assessment_type=AssessmentType.WEB,
            location="https://example.com",
            description="Headers missing",
            cause="Configuration oversight",
            evidence_ids=["EV-500"],
            impact="Client default risk",
            remediation="Add recommended headers",
            developer_guide="Document mitigation",
            ai_reasoning_summary="Confirmed by evidence",
            validation_status=ValidationStatus.TOOL_VERIFIED,
        )

    with pytest.raises(ValidationError):
        ToolError(code=field_value, message="request timed out", retryable=True)
