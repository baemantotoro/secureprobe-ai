# SecureProbe AI — DATA SCHEMA v0.1

## 1. 문서 목적

본 문서는 SecureProbe AI에서 사용되는 핵심 데이터 객체를 정의한다.

`ARCHITECTURE_v0.1.md`와 `AGENT_FLOW_v0.1.md`에서 정의한 Agent Flow를
Structured Output 중심으로 구현하기 위한 기준 문서다.

주요 목적:

- LLM 자유 텍스트 의존 최소화
- JSON Schema Validation 가능
- Pydantic Model 구현 가능
- Agent 단계 간 계약 명확화
- Evidence와 Finding 추적성 확보
- Report와 Evaluation 재사용 가능

---

# 2. 설계 원칙

## 2.1 Structured Output First

Agent 단계 사이의 주요 데이터는 JSON 객체를 사용한다.

## 2.2 Stable ID

Assessment, Test, Tool Execution, Evidence, Finding은 고유 ID를 가진다.

## 2.3 Evidence Traceability

Finding은 반드시 Evidence ID를 참조한다.

## 2.4 No Ground Truth Leakage

Assessment Schema에는 Ground Truth 정보가 포함되지 않는다.

Ground Truth는 Evaluation Schema에서만 사용한다.

## 2.5 Extensible but Minimal

20일 PoC에 필요한 Field만 우선 정의한다.

---

# 3. 공통 Enum

## 3.1 AssessmentType

```json
[
  "WEB",
  "SOURCE"
]
```

## 3.2 AssessmentStatus

```json
[
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
  "BLOCKED"
]
```

## 3.3 RiskLevel

```json
[
  "PASSIVE",
  "ACTIVE"
]
```

## 3.4 ExecutionStatus

```json
[
  "SUCCESS",
  "FAILED",
  "TIMEOUT",
  "BLOCKED",
  "UNSUPPORTED"
]
```

## 3.5 ValidationStatus

```json
[
  "UNVERIFIED",
  "TOOL_VERIFIED",
  "MANUAL_REQUIRED",
  "MANUAL_VERIFIED",
  "REJECTED"
]
```

## 3.6 Severity

```json
[
  "INFO",
  "LOW",
  "MEDIUM",
  "HIGH",
  "CRITICAL"
]
```

---

# 4. AssessmentRequest

Assessment 실행의 시작 입력이다.

## Web 예

```json
{
  "assessment_type": "WEB",
  "target_url": "http://localhost:8080",
  "scope": {
    "allowed_hosts": ["localhost"],
    "allowed_paths": ["/"]
  },
  "authorization_confirmed": true,
  "credentials": null
}
```

## Source 예

```json
{
  "assessment_type": "SOURCE",
  "source_directory": "./secureboard",
  "scope": {
    "include_paths": ["src"],
    "exclude_paths": ["node_modules", "target"]
  }
}
```

## 필드

| Field | Type | Required | 설명 |
|---|---|---:|---|
| assessment_type | enum | Y | WEB / SOURCE |
| target_url | string/null | WEB | Web Target |
| source_directory | string/null | SOURCE | Source 경로 |
| scope | object | Y | 진단 범위 |
| authorization_confirmed | boolean | WEB | Active Assessment 권한 확인 |
| credentials | object/null | N | 선택적 테스트 계정 |

---

# 5. AssessmentScope

## Web Scope

```json
{
  "allowed_hosts": ["localhost"],
  "allowed_paths": ["/app"],
  "deny_paths": ["/logout"]
}
```

## Source Scope

```json
{
  "include_paths": ["src"],
  "exclude_paths": [
    "node_modules",
    ".git",
    "target",
    "dist"
  ]
}
```

---

# 6. Credentials

테스트 계정은 허가 증명이 아니다.

예:

```json
{
  "username": "testuser",
  "password_ref": "runtime-secret:testuser"
}
```

보안 원칙:

```text
Raw Password를 Report에 저장하지 않는다.
가능하면 Runtime Secret Reference를 사용한다.
```

---

# 7. AssessmentRun

Assessment 전체 상태를 관리한다.

```json
{
  "assessment_id": "WEB-20261002-0001",
  "assessment_type": "WEB",
  "status": "OBSERVING",
  "started_at": "2026-10-02T12:00:00Z",
  "finished_at": null,
  "request": {},
  "errors": []
}
```

---

# 8. ValidationResult

Safety / Scope Validation 결과다.

```json
{
  "allowed": true,
  "reason": "localhost target",
  "active_assessment_allowed": true,
  "validated_scope": {
    "allowed_hosts": ["localhost"]
  }
}
```

차단 예:

```json
{
  "allowed": false,
  "reason": "external target not in allowlist",
  "active_assessment_allowed": false,
  "validated_scope": null
}
```

---

# 9. WebTargetContext

Web Observer 출력이다.

```json
{
  "context_id": "CTX-WEB-0001",
  "base_url": "http://localhost:8080",
  "endpoints": [
    {
      "url": "http://localhost:8080/login",
      "method": "GET",
      "source": "link"
    }
  ],
  "forms": [],
  "headers": {},
  "cookies": [],
  "authentication_detected": true,
  "session_detected": true,
  "content_types": [
    "text/html"
  ]
}
```

---

# 10. Endpoint

```json
{
  "url": "http://localhost:8080/search",
  "method": "GET",
  "parameters": [
    {
      "name": "q",
      "location": "query"
    }
  ],
  "source": "form"
}
```

---

# 11. Form

```json
{
  "action": "/login",
  "method": "POST",
  "fields": [
    {
      "name": "username",
      "type": "text"
    },
    {
      "name": "password",
      "type": "password"
    }
  ]
}
```

---

# 12. CookieInfo

```json
{
  "name": "SESSION",
  "secure": false,
  "http_only": true,
  "same_site": "Lax",
  "domain": "localhost",
  "path": "/"
}
```

민감한 Cookie Value는 저장하지 않는 것을 기본으로 한다.

---

# 13. SourceTargetContext

Source Observer 출력이다.

```json
{
  "context_id": "CTX-SRC-0001",
  "root_path": "./secureboard",
  "languages": [
    "Python"
  ],
  "frameworks": [
    "Flask"
  ],
  "important_files": [
    {
      "path": "app.py",
      "category": "application_entry"
    }
  ],
  "directory_summary": {
    "file_count": 25,
    "directory_count": 6
  }
}
```

---

# 14. SourceFileRef

```json
{
  "path": "src/user.py",
  "language": "Python",
  "category": "service",
  "size": 4200
}
```

---

# 15. TestPlan

Planner의 Structured Output이다.

```json
{
  "plan_id": "PLAN-0001",
  "assessment_id": "WEB-20261002-0001",
  "tests": [
    {
      "test_id": "WEB-001",
      "category": "security_header",
      "target": "/",
      "reason": "Security header 설정 확인",
      "required_capability": "header_inspection",
      "risk_level": "PASSIVE",
      "priority": 1,
      "expected_evidence": [
        "response_headers"
      ]
    }
  ]
}
```

---

# 16. TestCase

| Field | Type | Required | 설명 |
|---|---|---:|---|
| test_id | string | Y | Test 식별자 |
| category | string | Y | 진단 분류 |
| target | string | Y | 대상 Endpoint/File |
| reason | string | Y | Planner의 검사 이유 |
| required_capability | string | Y | 필요한 Tool Capability |
| risk_level | enum | Y | PASSIVE / ACTIVE |
| priority | integer | Y | 실행 우선순위 |
| expected_evidence | array | Y | 기대 Evidence 종류 |

---

# 17. ToolDefinition

Tool Registry 항목이다.

```json
{
  "tool_name": "header_inspector",
  "description": "HTTP response security headers를 확인한다.",
  "capabilities": [
    "header_inspection"
  ],
  "assessment_types": [
    "WEB"
  ],
  "risk_level": "PASSIVE",
  "input_schema": "HeaderInspectorInput",
  "output_schema": "HeaderInspectorOutput"
}
```

---

# 18. ToolSelection

```json
{
  "selection_id": "SEL-0001",
  "test_id": "WEB-001",
  "tool_name": "header_inspector",
  "reason": "header_inspection capability와 일치",
  "risk_level": "PASSIVE"
}
```

---

# 19. ToolExecution

Tool 실제 실행 기록이다.

```json
{
  "execution_id": "EXEC-0001",
  "test_id": "WEB-001",
  "tool_name": "header_inspector",
  "input": {
    "url": "http://localhost:8080/"
  },
  "status": "SUCCESS",
  "started_at": "2026-10-02T12:01:10Z",
  "finished_at": "2026-10-02T12:01:10Z",
  "duration_ms": 145,
  "output": {},
  "error": null
}
```

---

# 20. ToolError

```json
{
  "code": "HTTP_TIMEOUT",
  "message": "request timed out",
  "retryable": true
}
```

---

# 21. Evidence

Evidence 공통 Wrapper다.

```json
{
  "evidence_id": "EVID-0001",
  "assessment_id": "WEB-20261002-0001",
  "test_id": "WEB-001",
  "execution_id": "EXEC-0001",
  "type": "HTTP_RESPONSE_HEADERS",
  "source": "header_inspector",
  "location": "http://localhost:8080/",
  "data": {},
  "created_at": "2026-10-02T12:01:10Z"
}
```

---

# 22. Web Evidence 예

```json
{
  "evidence_id": "EVID-WEB-0001",
  "type": "HTTP_RESPONSE_HEADERS",
  "location": "http://localhost:8080/",
  "data": {
    "status_code": 200,
    "headers": {
      "Content-Type": "text/html"
    }
  }
}
```

민감한 Header/Cookie 값은 Masking 정책을 적용한다.

---

# 23. Source Evidence 예

```json
{
  "evidence_id": "EVID-SRC-0001",
  "type": "SOURCE_CODE",
  "location": "src/user.py:42-46",
  "data": {
    "file_path": "src/user.py",
    "start_line": 42,
    "end_line": 46,
    "snippet": "query = \"SELECT ...\"",
    "matched_pattern": "string-built-sql"
  }
}
```

---

# 24. CandidateFinding

Analyzer가 생성하는 미확정 Finding이다.

```json
{
  "candidate_id": "CAND-0001",
  "test_id": "WEB-001",
  "title": "Missing X-Content-Type-Options Header",
  "severity": "LOW",
  "location": "http://localhost:8080/",
  "reasoning_summary": "Response에 해당 header가 확인되지 않았다.",
  "evidence_ids": [
    "EVID-WEB-0001"
  ],
  "verification_required": true
}
```

---

# 25. VerificationRequest

추가 검증이 필요한 경우 사용한다.

```json
{
  "verification_id": "VER-0001",
  "candidate_id": "CAND-0001",
  "decision": "REQUEST_ADDITIONAL_TOOL",
  "required_capability": "header_inspection",
  "reason": "실제 response header 재확인 필요",
  "round": 1
}
```

가능한 decision:

```json
[
  "ACCEPT_TOOL_VERIFIED",
  "REQUEST_ADDITIONAL_TOOL",
  "REQUEST_MANUAL_REVIEW",
  "REJECT"
]
```

---

# 26. Finding

최종 Finding 객체다.

```json
{
  "finding_id": "FIND-WEB-0001",
  "assessment_id": "WEB-20261002-0001",
  "test_id": "WEB-001",
  "vulnerability_name": "Missing Security Header",
  "severity": "LOW",
  "assessment_type": "WEB",
  "location": "http://localhost:8080/",
  "description": "X-Content-Type-Options header가 설정되어 있지 않다.",
  "cause": "HTTP response security header configuration 누락",
  "evidence_ids": [
    "EVID-WEB-0001"
  ],
  "owasp_mapping": [
    "A05:2021-Security Misconfiguration"
  ],
  "cwe_mapping": [
    "CWE-693"
  ],
  "impact": "브라우저 보안 동작이 약화될 수 있다.",
  "remediation": "X-Content-Type-Options: nosniff 설정",
  "developer_guide": "Web framework response header 설정을 적용한다.",
  "ai_reasoning_summary": "Header inspection 결과와 검증 Evidence를 기반으로 판단했다.",
  "validation_status": "TOOL_VERIFIED"
}
```

---

# 27. Finding 필수 Field

```text
finding_id
vulnerability_name
severity
assessment_type
location
description
cause
evidence_ids
owasp_mapping
cwe_mapping
impact
remediation
developer_guide
ai_reasoning_summary
validation_status
```

PROJECT_CONTEXT의 Finding 요구사항을 충족한다.

---

# 28. AI Reasoning Summary 원칙

`ai_reasoning_summary`는 긴 Chain-of-Thought 저장용이 아니다.

저장 대상:

```text
어떤 Evidence를 근거로
어떤 보안 판단을 했는지에 대한 짧은 설명
```

예:

```text
Response Header Evidence에서 X-Content-Type-Options가 존재하지 않아
Security Misconfiguration 후보로 판단했고,
동일 요청 재검증으로 누락을 확인했다.
```

---

# 29. AssessmentError

```json
{
  "error_id": "ERR-0001",
  "phase": "EXECUTING",
  "code": "HTTP_TIMEOUT",
  "message": "Tool execution timed out",
  "retryable": true,
  "tool_name": "http_request",
  "test_id": "WEB-003"
}
```

---

# 30. AgentEvent

Audit Trail용 객체다.

```json
{
  "event_id": "EVT-0001",
  "assessment_id": "WEB-20261002-0001",
  "event_type": "TOOL_EXECUTED",
  "timestamp": "2026-10-02T12:01:10Z",
  "test_id": "WEB-001",
  "tool_name": "header_inspector",
  "summary": "header inspection completed"
}
```

---

# 31. AgentEventType

v0.1 이벤트:

```json
[
  "ASSESSMENT_CREATED",
  "VALIDATION_COMPLETED",
  "OBSERVATION_COMPLETED",
  "PLAN_CREATED",
  "TOOL_SELECTED",
  "TOOL_EXECUTED",
  "CANDIDATE_CREATED",
  "VERIFICATION_REQUESTED",
  "FINDING_CREATED",
  "REPORT_CREATED",
  "ASSESSMENT_COMPLETED"
]
```

---

# 32. AssessmentResult

최종 JSON 결과다.

```json
{
  "assessment_id": "WEB-20261002-0001",
  "assessment_type": "WEB",
  "status": "COMPLETED",
  "target": "http://localhost:8080",
  "started_at": "2026-10-02T12:00:00Z",
  "finished_at": "2026-10-02T12:05:00Z",
  "tests_planned": 8,
  "tests_executed": 8,
  "findings": [
    "FIND-WEB-0001"
  ],
  "manual_review_required": [],
  "errors": [],
  "report_paths": {
    "json": "reports/secureprobe/web-0001.json",
    "markdown": "reports/secureprobe/web-0001.md"
  }
}
```

---

# 33. ReportSummary

Markdown Report 생성에 사용할 요약 객체다.

```json
{
  "assessment_id": "WEB-20261002-0001",
  "target": "http://localhost:8080",
  "finding_count": 3,
  "severity_counts": {
    "CRITICAL": 0,
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
    "INFO": 0
  },
  "manual_review_count": 1
}
```

---

# 34. GroundTruthFinding

Assessment Agent에서는 사용하지 않는다.

Evaluation 단계 전용이다.

```json
{
  "ground_truth_id": "GT-01",
  "vulnerability_name": "SQL Injection",
  "location": "/search?q=",
  "cwe_mapping": [
    "CWE-89"
  ],
  "owasp_mapping": [
    "A03:2021-Injection"
  ],
  "expected_evidence": "controlled SQL injection behavior",
  "remediation": "parameterized query"
}
```

---

# 35. BenchmarkFinding

ZAP / Semgrep 결과를 공통 비교 모델로 정규화할 때 사용한다.

```json
{
  "benchmark": "ZAP",
  "external_id": "10021",
  "vulnerability_name": "X-Content-Type-Options Header Missing",
  "severity": "LOW",
  "location": "http://localhost:8080/",
  "raw_result_ref": "benchmarks/zap/result.json"
}
```

SecureProbe Agent 내부 입력으로 사용하지 않는다.

---

# 36. EvaluationRecord

Ground Truth와 진단 결과를 비교한다.

```json
{
  "ground_truth_id": "GT-01",
  "scanner": "SECUREPROBE",
  "detected": true,
  "classification": "TP",
  "finding_id": "FIND-WEB-0003",
  "manual_validation": "CONFIRMED"
}
```

classification:

```json
[
  "TP",
  "FP",
  "FN"
]
```

---

# 37. EvaluationSummary

```json
{
  "scanner": "SECUREPROBE",
  "tp": 8,
  "fp": 2,
  "fn": 2,
  "precision": 0.8,
  "recall": 0.8,
  "assessment_time_seconds": 120
}
```

공식 계산:

```text
Precision = TP / (TP + FP)

Recall = TP / (TP + FN)
```

분모가 0인 경우 별도 처리한다.

---

# 38. Web Tool Input 예

## HttpRequestInput

```json
{
  "url": "http://localhost:8080/",
  "method": "GET",
  "headers": {},
  "parameters": {},
  "follow_redirects": true
}
```

## HeaderInspectorInput

```json
{
  "url": "http://localhost:8080/"
}
```

---

# 39. Web Tool Output 예

## HttpResponseOutput

```json
{
  "status_code": 200,
  "headers": {},
  "content_type": "text/html",
  "body_excerpt": "<html>...</html>",
  "elapsed_ms": 132
}
```

전체 Response Body를 무조건 저장하지 않고 필요 범위만 Evidence로 보관한다.

---

# 40. Source Tool Input 예

## FileReaderInput

```json
{
  "path": "src/user.py",
  "start_line": 35,
  "end_line": 60
}
```

## SourceSearchInput

```json
{
  "root_path": "./secureboard",
  "pattern": "SELECT",
  "extensions": [
    ".py"
  ]
}
```

---

# 41. Source Tool Output 예

## FileReaderOutput

```json
{
  "path": "src/user.py",
  "start_line": 35,
  "end_line": 60,
  "content": "..."
}
```

## PatternMatchOutput

```json
{
  "matches": [
    {
      "path": "src/user.py",
      "line": 42,
      "match": "SELECT"
    }
  ]
}
```

---

# 42. Pydantic 구현 권장 매핑

권장 파일:

```text
secureprobe/models/
├── assessment.py
├── target.py
├── plan.py
├── tool.py
├── evidence.py
├── finding.py
├── event.py
└── evaluation.py
```

예상 Model:

```text
AssessmentRequest
AssessmentRun
ValidationResult
WebTargetContext
SourceTargetContext
TestPlan
TestCase
ToolDefinition
ToolSelection
ToolExecution
Evidence
CandidateFinding
VerificationRequest
Finding
AssessmentError
AgentEvent
AssessmentResult
```

---

# 43. JSON 저장 구조 권장안

```text
evidence/
├── web/
│   └── <assessment_id>/
└── source/
    └── <assessment_id>/

reports/
└── secureprobe/
    ├── <assessment_id>.json
    └── <assessment_id>.md
```

---

# 44. ID 규칙

권장 Prefix:

```text
WEB- / SRC-      Assessment
CTX-             Context
PLAN-            Plan
TEST-            Test
SEL-             Selection
EXEC-            Execution
EVID-            Evidence
CAND-            Candidate
VER-             Verification
FIND-            Finding
ERR-             Error
EVT-             Event
```

ID는 내부 UUID 또는 순번과 조합해도 된다.

---

# 45. Timestamp

Timestamp는 ISO 8601을 사용한다.

예:

```text
2026-10-02T12:00:00Z
```

저장 형식은 UTC 권장.

UI에서 필요 시 Local Time으로 변환한다.

---

# 46. Sensitive Data 정책

다음 정보는 Evidence/Report에 그대로 저장하지 않는다.

```text
Password
Raw Session Token
Authorization Header
Secret Key
API Key
Personal Sensitive Data
```

필요한 경우 Masking:

```text
Bearer abcdef...
→ Bearer ***MASKED***
```

---

# 47. Schema Validation 실패 처리

LLM Structured Output이 Schema를 만족하지 않으면:

```text
Reject
↓
Retry
↓
최대 Retry 초과
↓
Phase Failure
```

잘못된 JSON을 자동 추측해 강제로 확정하지 않는다.

---

# 48. Null / Optional 원칙

Optional Field는 명시적으로 `null`을 허용한다.

필수 Field를 누락한 객체는 Validation 실패로 처리한다.

---

# 49. Version Field

향후 Schema 변경 추적을 위해 주요 최상위 객체에 Schema Version을 둘 수 있다.

예:

```json
{
  "schema_version": "0.1",
  "assessment_id": "WEB-20261002-0001"
}
```

v0.1 구현 시 최소한 Report와 AssessmentResult에는 적용하는 것을 권장한다.

---

# 50. Finding과 Evidence 관계

권장 관계:

```text
Finding
   │
   ├── Evidence 1
   ├── Evidence 2
   └── Evidence 3
```

Evidence는 여러 Finding에서 참조 가능하지만,
v0.1에서는 단순 구현을 위해 중복 참조를 허용하되 삭제 연쇄 처리는 구현하지 않는다.

---

# 51. Candidate와 Finding 관계

```text
CandidateFinding
       ↓
Verification
       ↓
Finding
```

Candidate는 최종 Report 기본 목록에 포함하지 않는다.

단:

```text
MANUAL_REQUIRED
```

로 전환된 경우 최종 Finding으로 보존한다.

---

# 52. Report에서의 Finding 분류

최종 Report에서 구분한다.

```text
Verified Findings
Manual Review Required
Rejected Candidates
Execution Errors
```

Rejected Candidate는 기본 사용자 Report에서는 상세 노출하지 않아도 되지만
Audit Data에는 남길 수 있다.

---

# 53. Evaluation에서의 자동/수동 구분

다음 필드를 권장한다.

```json
{
  "automatic_result": "TP",
  "manual_validation": "CONFIRMED"
}
```

자동진단 결과와 사람의 최종 확인을 구분한다.

---

# 54. v0.1 최소 구현 Schema

20일 프로젝트에서 반드시 구현할 객체:

```text
AssessmentRequest
AssessmentRun
ValidationResult
TargetContext
TestPlan
TestCase
ToolDefinition
ToolSelection
ToolExecution
Evidence
CandidateFinding
VerificationRequest
Finding
AssessmentError
AssessmentResult
```

다음은 비교 단계에서 구현:

```text
GroundTruthFinding
BenchmarkFinding
EvaluationRecord
EvaluationSummary
```

---

# 55. 완료 기준

DATA_SCHEMA v0.1은 다음 조건을 만족하면 구현 기준으로 사용할 수 있다.

```text
1. Agent 단계별 입력/출력이 객체로 정의되어 있다.
2. Finding이 Evidence를 ID로 참조한다.
3. Validation Status가 Enum으로 정의되어 있다.
4. Tool 실행 상태와 취약점 판단을 구분한다.
5. Ground Truth가 Assessment Schema와 분리되어 있다.
6. Benchmark 결과가 Agent 입력과 분리되어 있다.
7. JSON 및 Pydantic 구현이 가능한 수준이다.
8. 민감정보 저장 제한이 정의되어 있다.
```

---

# 56. 다음 단계

본 문서와 `AGENT_FLOW_v0.1.md`가 확정되면 다음 문서를 작성한다.

```text
docs/03_wbs/WBS_20DAYS_v0.1.md
```

WBS에서는 실제 구현을 다음과 같이 작은 Task로 분해한다.

```text
설계
→ SecureBoard
→ Agent Core
→ Web Tools
→ Source Tools
→ Verification
→ Report
→ Benchmark
→ Evaluation
→ Portfolio
```
