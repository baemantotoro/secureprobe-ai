from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from secureprobe.models import (
    AgentEvent,
    CandidateFinding,
    Evidence,
    ExecutionStatus,
    Finding,
    RiskLevel,
    Severity,
    TestCase,
    TestPlan,
    ToolDefinition,
    ToolError,
    ToolExecution,
    ToolSelection,
    ValidationStatus,
    AssessmentType,
    VerificationRequest,
)


def test_test_plan_and_case_contract():
    case = TestCase(
        test_id="TC-001",
        category="WEB",
        target="https://example.com",
        reason="Check header security",
        required_capability="http_client",
        risk_level=RiskLevel.ACTIVE,
        priority=2,
        expected_evidence=["headers"],
    )
    plan = TestPlan(plan_id="PLAN-001", assessment_id="RUN-001", tests=[case])

    assert plan.tests[0].risk_level == RiskLevel.ACTIVE
    assert plan.model_dump(mode="json")["tests"][0]["risk_level"] == "ACTIVE"

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
            test_id="TC-002",
            category="WEB",
            target="https://example.com",
            reason="Check header security",
            required_capability="http_client",
            risk_level=RiskLevel.ACTIVE,
            priority=0,
        )


def test_tool_definition_and_selection_contract():
    tool = ToolDefinition(
        tool_name="http_probe",
        description="Check HTTP responses",
        capabilities=["network"],
        assessment_types=[AssessmentType.WEB],
        risk_level=RiskLevel.ACTIVE,
        input_schema="{type: object}",
        output_schema="{type: object}",
    )
    selection = ToolSelection(
        selection_id="SEL-001",
        test_id="TC-001",
        tool_name=tool.tool_name,
        reason="Best match",
        risk_level=RiskLevel.ACTIVE,
    )

    assert tool.assessment_types == [AssessmentType.WEB]
    assert selection.tool_name == "http_probe"

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


def test_tool_execution_and_error_contract():
    execution = ToolExecution(
        execution_id="EX-001",
        test_id="TC-001",
        tool_name="http_probe",
        input={"url": "https://example.com"},
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_ms=120,
        output={"status": "ok"},
    )

    assert execution.status == ExecutionStatus.SUCCESS
    assert execution.input["url"] == "https://example.com"

    error = ToolError(code="TIMEOUT", message="Request exceeded timeout", retryable=True)
    failed = ToolExecution(
        execution_id="EX-002",
        test_id="TC-002",
        tool_name="http_probe",
        status=ExecutionStatus.FAILED,
        started_at=datetime.now(timezone.utc),
        output={},
        error=error,
    )

    assert failed.error is not None
    assert failed.error.retryable is True

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


def test_evidence_candidate_and_verification_contract():
    evidence = Evidence(
        evidence_id="EV-001",
        assessment_id="RUN-001",
        test_id="TC-001",
        execution_id="EX-001",
        type="response",
        source="http_probe",
        location="https://example.com",
        data={"status": 200},
        created_at=datetime.now(timezone.utc),
    )

    assert evidence.data["status"] == 200

    candidate = CandidateFinding(
        candidate_id="CF-001",
        test_id="TC-001",
        title="Missing security header",
        severity=Severity.MEDIUM,
        location="https://example.com",
        reasoning_summary="Header is missing in the HTTP response",
        evidence_ids=[evidence.evidence_id],
        verification_required=True,
    )

    assert candidate.severity == Severity.MEDIUM

    with pytest.raises(ValidationError):
        CandidateFinding(
            candidate_id="CF-002",
            test_id="TC-002",
            title="Missing security header",
            severity=Severity.MEDIUM,
            location="https://example.com",
            reasoning_summary="Header is missing in the HTTP response",
            evidence_ids=[],
            verification_required=True,
        )

    verification = VerificationRequest(
        verification_id="VR-001",
        candidate_id=candidate.candidate_id,
        decision="ACCEPT_TOOL_VERIFIED",
        reason="Evidence confirms the miss",
        round=1,
    )
    assert verification.decision == "ACCEPT_TOOL_VERIFIED"

    with pytest.raises(ValidationError):
        VerificationRequest(
            verification_id="VR-002",
            candidate_id=candidate.candidate_id,
            decision="UNKNOWN",
            reason="bad decision",
            round=1,
        )

    with pytest.raises(ValidationError):
        VerificationRequest(
            verification_id="VR-003",
            candidate_id=candidate.candidate_id,
            decision="ACCEPT_TOOL_VERIFIED",
            reason="bad round",
            round=0,
        )


def test_finding_and_event_contract():
    finding = Finding(
        finding_id="F-001",
        assessment_id="RUN-001",
        test_id="TC-001",
        vulnerability_name="Missing Security Headers",
        severity=Severity.MEDIUM,
        assessment_type=AssessmentType.WEB,
        location="https://example.com",
        description="The response lacks security headers.",
        cause="Server configuration omitted recommended mitigation.",
        evidence_ids=["EV-001"],
        owasp_mapping=["A05:2021"],
        cwe_mapping=["CWE-693"],
        impact="Clients may not apply safe defaults.",
        remediation="Add recommended HTTP headers.",
        developer_guide="Document the new server headers.",
        ai_reasoning_summary="The response was inspected and the header gap is confirmed.",
        validation_status=ValidationStatus.TOOL_VERIFIED,
    )

    assert finding.validation_status == ValidationStatus.TOOL_VERIFIED
    assert finding.model_dump(mode="json")["severity"] == "MEDIUM"

    with pytest.raises(ValidationError):
        Finding(
            finding_id="F-002",
            assessment_id="RUN-001",
            test_id="TC-002",
            vulnerability_name="Missing Security Headers",
            severity=Severity.MEDIUM,
            assessment_type=AssessmentType.WEB,
            location="https://example.com",
            description="The response lacks security headers.",
            cause="Server configuration omitted recommended mitigation.",
            evidence_ids=[],
            owasp_mapping=[],
            cwe_mapping=[],
            impact="Clients may not apply safe defaults.",
            remediation="Add recommended HTTP headers.",
            developer_guide="Document the new server headers.",
            ai_reasoning_summary="The response was inspected and the header gap is confirmed.",
            validation_status=ValidationStatus.TOOL_VERIFIED,
        )

    event = AgentEvent(
        event_id="AE-001",
        assessment_id="RUN-001",
        event_type="PLAN_CREATED",
        timestamp=datetime.now(timezone.utc),
        test_id="TC-001",
        tool_name="http_probe",
        summary="Plan created for the HTTP check",
    )
    assert event.event_type == "PLAN_CREATED"

    with pytest.raises(ValidationError):
        AgentEvent(
            event_id="AE-002",
            assessment_id="RUN-001",
            event_type="BANNED_EVENT",
            timestamp=datetime.now(timezone.utc),
            summary="bad event",
        )


def test_extra_field_and_mutable_default_safety():
    with pytest.raises(ValidationError):
        TestPlan(plan_id="PLAN-999", assessment_id="RUN-999", tests=[], unknown_field="value")

    plan_a = TestPlan(plan_id="PLAN-A", assessment_id="RUN-A", tests=[])
    plan_b = TestPlan(plan_id="PLAN-B", assessment_id="RUN-B", tests=[])
    plan_a.tests.append(
        TestCase(
            test_id="TC-A",
            category="WEB",
            target="https://example.com",
            reason="Check stuff",
            required_capability="http_client",
            risk_level=RiskLevel.PASSIVE,
            priority=1,
        )
    )

    assert plan_b.tests == []

    execution_a = ToolExecution(
        execution_id="EX-A",
        test_id="TC-A",
        tool_name="http_probe",
        input={},
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        output={},
    )
    execution_b = ToolExecution(
        execution_id="EX-B",
        test_id="TC-B",
        tool_name="http_probe",
        input={},
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        output={},
    )
    execution_a.output["result"] = "A"
    assert execution_b.output == {}


def test_imports():
    from secureprobe.models import (
        AgentEvent,
        CandidateFinding,
        Evidence,
        Finding,
        TestCase,
        TestPlan,
        ToolDefinition,
        ToolError,
        ToolExecution,
        ToolSelection,
        VerificationRequest,
    )

    assert AgentEvent is not None
    assert ToolExecution is not None
    assert Finding is not None
