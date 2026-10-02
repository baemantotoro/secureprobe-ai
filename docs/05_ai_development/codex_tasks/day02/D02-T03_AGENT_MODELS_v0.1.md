# D02-T03 — Agent Models Implementation v0.1

## 1. 목적

`DATA_SCHEMA_v0.1.md`, `AGENT_FLOW_v0.1.md`, `WBS_20DAYS_v0.1.md`에 정의된
SecureProbe AI Agent 단계 간 Structured Output 모델을 Pydantic v2로 구현한다.

이번 Task의 목적은 실제 Agent 로직을 구현하는 것이 아니라,
다음 흐름의 **데이터 계약(Data Contract)** 을 코드로 고정하는 것이다.

```text
Plan
→ Tool Selection
→ Tool Execution
→ Evidence
→ Candidate Finding
→ Verification Request
→ Finding
→ Agent Event
```

이번 Task에서는 실제 Planner, Tool Registry, Executor, Analyzer, Verifier를 구현하지 않는다.

---

## 2. 작업 ID와 근거

- WBS 기준: Day 2, Task 03
- 작업 ID: `D02-T03`
- 작업명: Agent Model 구현
- 우선순위: P0
- 선행 작업:
  - D02-T01 Common Enum 완료
  - D02-T02 Assessment Model 완료
- 다음 작업:
  - D02-T04 Validation Unit Test

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. D02-T03 구현 대상

WBS에 정의된 다음 모델을 구현한다.

```text
TestPlan
TestCase
ToolDefinition
ToolSelection
ToolExecution
Evidence
CandidateFinding
VerificationRequest
Finding
AgentEvent
```

ToolExecution에서 필요한 최소 보조 모델:

```text
ToolError
```

총 구현 대상:

```text
11개
```

---

## 4. 구현하지 않는 것

이번 Task는 Model Layer만 구현한다.

다음은 구현하지 않는다.

```text
Planner 실제 코드
OpenAI API 호출
Tool Registry 실제 저장소
Tool Selector 실제 선택 로직
Tool Executor 실제 실행 로직
Safety Gate
Analyzer 실제 판단 로직
Verifier 실제 판단 로직
Evidence 파일 저장
Report Generator
Web Tool
Source Tool
Ground Truth
Evaluation
```

---

# 5. 권장 파일 구조

다음 파일로 분리한다.

```text
secureprobe/models/
├── assessment.py
├── enums.py
├── plan.py
├── tool.py
├── evidence.py
├── finding.py
└── event.py
```

생성 대상:

```text
secureprobe/models/plan.py
secureprobe/models/tool.py
secureprobe/models/evidence.py
secureprobe/models/finding.py
secureprobe/models/event.py
```

수정 가능:

```text
secureprobe/models/__init__.py
```

---

# 6. 공통 Model 정책

기존 Assessment Model의 정책과 일관성을 유지한다.

가능하면 기존:

```python
SecureProbeModel
```

을 재사용한다.

현재 `assessment.py` 안에만 존재하여 순환참조 또는 구조 문제가 발생한다면,
이번 Task에서 공통 Base Model을 별도 파일로 이동하지 않는다.

20일 PoC 범위를 유지하기 위해 각 파일에서:

```python
ConfigDict(extra="forbid", str_strip_whitespace=True)
```

를 일관되게 적용해도 된다.

단, 대규모 Refactoring은 금지한다.

---

# 7. 기존 Enum 재사용

반드시 기존 Enum을 재사용한다.

```text
AssessmentType
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

다음 Enum은 새로 중복 정의하지 않는다.

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

---

# 8. TestPlan

Planner의 Structured Output이다.

기준 구조:

```json
{
  "plan_id": "PLAN-0001",
  "assessment_id": "WEB-20261002-0001",
  "tests": []
}
```

필드:

```python
plan_id: str
assessment_id: str
tests: list[TestCase]
```

`tests`는:

```python
Field(default_factory=list)
```

를 사용한다.

---

# 9. TestCase

필드:

```text
test_id
category
target
reason
required_capability
risk_level
priority
expected_evidence
```

권장 타입:

```python
test_id: str
category: str
target: str
reason: str
required_capability: str
risk_level: RiskLevel
priority: int
expected_evidence: list[str]
```

---

# 10. TestCase Validation

최소 다음을 적용한다.

```text
test_id              빈 문자열 금지
category             빈 문자열 금지
target               빈 문자열 금지
reason               빈 문자열 금지
required_capability  빈 문자열 금지
priority             1 이상
expected_evidence    list
```

권장:

```python
priority: int = Field(ge=1)
```

`expected_evidence`는 빈 리스트를 허용할 수 있다.

Planner가 Evidence 종류를 명시하도록 권장하지만
Model 생성 단계에서 강제하지는 않는다.

---

# 11. ToolDefinition

Tool Registry 항목의 Structured Model이다.

기준 필드:

```text
tool_name
description
capabilities
assessment_types
risk_level
input_schema
output_schema
```

권장 타입:

```python
tool_name: str
description: str
capabilities: list[str]
assessment_types: list[AssessmentType]
risk_level: RiskLevel
input_schema: str
output_schema: str
```

---

# 12. ToolDefinition Validation

최소 다음을 검증한다.

```text
tool_name 빈 문자열 금지
description 빈 문자열 금지
capabilities 최소 1개
assessment_types 최소 1개
input_schema 빈 문자열 금지
output_schema 빈 문자열 금지
```

권장:

```python
Field(min_length=1)
```

또는 Pydantic List 길이 제약을 사용한다.

---

# 13. ToolSelection

필드:

```text
selection_id
test_id
tool_name
reason
risk_level
```

권장 타입:

```python
selection_id: str
test_id: str
tool_name: str
reason: str
risk_level: RiskLevel
```

이 Model은 Tool 선택 결과만 표현한다.

실제 capability matching은 이번 Task에서 구현하지 않는다.

---

# 14. ToolError

ToolExecution의 오류 객체다.

필드:

```text
code
message
retryable
```

권장 타입:

```python
code: str
message: str
retryable: bool = False
```

---

# 15. ToolExecution

실제 Tool 실행 기록의 Structured Model이다.

필드:

```text
execution_id
test_id
tool_name
input
status
started_at
finished_at
duration_ms
output
error
```

권장 타입:

```python
execution_id: str
test_id: str
tool_name: str
input: dict[str, Any]
status: ExecutionStatus
started_at: datetime
finished_at: datetime | None = None
duration_ms: int | None = None
output: dict[str, Any]
error: ToolError | None = None
```

기본값:

```python
input = Field(default_factory=dict)
output = Field(default_factory=dict)
```

---

# 16. ToolExecution Validation

최소:

```text
duration_ms >= 0
```

단:

```text
duration_ms = None
```

은 실행 중 또는 측정 불가 상태를 위해 허용할 수 있다.

이번 Task에서는 다음 Cross-field 정책을 과도하게 구현하지 않는다.

예:

```text
SUCCESS이면 반드시 error=None
FAILED이면 반드시 error 존재
```

이러한 실행 상태 정책은 실제 Executor 구현 시 강화할 수 있다.

Model Layer에서는 구조 검증 중심으로 유지한다.

---

# 17. Evidence

Evidence 공통 Wrapper다.

필드:

```text
evidence_id
assessment_id
test_id
execution_id
type
source
location
data
created_at
```

권장 타입:

```python
evidence_id: str
assessment_id: str
test_id: str
execution_id: str
type: str
source: str
location: str
data: dict[str, Any]
created_at: datetime
```

`data`:

```python
Field(default_factory=dict)
```

---

# 18. Evidence 보안 원칙

Evidence Model은 Password/Token을 별도 필드로 만들지 않는다.

금지 필드 예:

```text
password
raw_token
authorization_header
api_key
secret_key
```

단, `data: dict[str, Any]` 안의 민감정보 Masking은
이번 Model Task에서 자동 구현하지 않는다.

Masking은 실제 Evidence 생성 계층의 책임이다.

결과 문서에 이 책임 분리를 기록한다.

---

# 19. CandidateFinding

Analyzer가 생성하는 미확정 Finding이다.

필드:

```text
candidate_id
test_id
title
severity
location
reasoning_summary
evidence_ids
verification_required
```

권장 타입:

```python
candidate_id: str
test_id: str
title: str
severity: Severity
location: str
reasoning_summary: str
evidence_ids: list[str]
verification_required: bool
```

---

# 20. CandidateFinding Evidence 정책

CandidateFinding은 Evidence 기반 판단이어야 한다.

따라서:

```text
evidence_ids 최소 1개
```

를 Model Validation으로 강제한다.

이유:

```text
Evidence 없는 AI 추측 Finding 방지
```

---

# 21. reasoning_summary 정책

`reasoning_summary`는 Chain-of-Thought 저장용이 아니다.

저장 대상:

```text
어떤 Evidence를 근거로 어떤 후보 판단을 했는지에 대한 짧은 요약
```

Model 이름은 기준 문서에 따라:

```text
reasoning_summary
```

를 유지한다.

---

# 22. VerificationRequest

추가 검증이 필요한 경우 사용한다.

필드:

```text
verification_id
candidate_id
decision
required_capability
reason
round
```

가능한 decision:

```text
ACCEPT_TOOL_VERIFIED
REQUEST_ADDITIONAL_TOOL
REQUEST_MANUAL_REVIEW
REJECT
```

---

# 23. VerificationDecision 표현

D02-T01 공통 Enum 6종은 수정하지 않는다.

이번 v0.1에서는 다음 중 하나를 사용한다.

권장:

```python
from typing import Literal

VerificationDecision = Literal[
    "ACCEPT_TOOL_VERIFIED",
    "REQUEST_ADDITIONAL_TOOL",
    "REQUEST_MANUAL_REVIEW",
    "REJECT",
]
```

또는 `finding.py` 내부의 전용 Enum을 사용할 수 있다.

단:

```text
secureprobe/models/enums.py
```

의 공통 Enum 목록을 임의로 변경하지 않는다.

---

# 24. VerificationRequest 타입

권장:

```python
verification_id: str
candidate_id: str
decision: VerificationDecision
required_capability: str | None = None
reason: str
round: int = Field(ge=1)
```

`required_capability`는:

```text
REQUEST_ADDITIONAL_TOOL
```

에서 주로 사용한다.

이번 Task에서는 decision별 Cross-field 조건까지 강제하지 않는다.

---

# 25. Finding

최종 Finding 객체다.

필수 Field:

```text
finding_id
assessment_id
test_id
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

---

# 26. Finding 권장 타입

```python
finding_id: str
assessment_id: str
test_id: str
vulnerability_name: str
severity: Severity
assessment_type: AssessmentType
location: str
description: str
cause: str
evidence_ids: list[str]
owasp_mapping: list[str]
cwe_mapping: list[str]
impact: str
remediation: str
developer_guide: str
ai_reasoning_summary: str
validation_status: ValidationStatus
```

---

# 27. Finding Evidence 강제

최종 Finding은 반드시 Evidence를 참조해야 한다.

따라서:

```text
evidence_ids 최소 1개
```

로 Validation한다.

Evidence 없는 Finding은 생성 실패해야 한다.

이 규칙은 SecureProbe AI의 핵심 설계 원칙이다.

---

# 28. OWASP / CWE Mapping

다음 필드는 list로 유지한다.

```text
owasp_mapping
cwe_mapping
```

v0.1에서는 빈 리스트를 허용할 수 있다.

이유:

```text
일부 INFO Finding이나 매핑이 확정되지 않은 경우 존재 가능
```

하지만 최종 보안 Finding 생성 시 가능한 경우 매핑하도록
Analyzer/Report Task에서 처리한다.

---

# 29. ai_reasoning_summary

Finding의:

```text
ai_reasoning_summary
```

는 긴 내부 추론을 저장하지 않는다.

짧고 검증 가능한 근거 요약만 저장한다.

예:

```text
Header Evidence에서 X-Content-Type-Options가 누락됐고
동일 요청 재검증에서도 누락을 확인했다.
```

---

# 30. AgentEvent

Audit Trail용 Structured Model이다.

필드:

```text
event_id
assessment_id
event_type
timestamp
test_id
tool_name
summary
```

권장 타입:

```python
event_id: str
assessment_id: str
event_type: AgentEventType
timestamp: datetime
test_id: str | None = None
tool_name: str | None = None
summary: str
```

---

# 31. AgentEventType

허용값:

```text
ASSESSMENT_CREATED
VALIDATION_COMPLETED
OBSERVATION_COMPLETED
PLAN_CREATED
TOOL_SELECTED
TOOL_EXECUTED
CANDIDATE_CREATED
VERIFICATION_REQUESTED
FINDING_CREATED
REPORT_CREATED
ASSESSMENT_COMPLETED
```

D02-T01 공통 Enum 파일은 변경하지 않는다.

권장 구현:

```python
AgentEventType = Literal[
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
    "ASSESSMENT_COMPLETED",
]
```

또는 event.py 내부 전용 Enum을 사용할 수 있다.

---

# 32. Timestamp

다음 Model에서 `datetime` 사용:

```text
ToolExecution.started_at
ToolExecution.finished_at
Evidence.created_at
AgentEvent.timestamp
```

JSON 직렬화는 Pydantic:

```python
model_dump(mode="json")
```

을 통해 ISO 8601 형태로 출력 가능해야 한다.

UTC를 권장한다.

---

# 33. Stable ID 원칙

다음 객체는 고유 ID 필드를 가진다.

```text
TestPlan      → plan_id
TestCase      → test_id
ToolSelection → selection_id
ToolExecution → execution_id
Evidence      → evidence_id
Candidate     → candidate_id
Verification  → verification_id
Finding       → finding_id
AgentEvent    → event_id
```

이번 Task에서 자동 UUID 생성은 필수가 아니다.

호출자가 ID를 제공하도록 구현해도 된다.

---

# 34. Mutable Default 금지

다음과 같은 구현 금지:

```python
tests: list[TestCase] = []
capabilities: list[str] = []
data: dict[str, Any] = {}
evidence_ids: list[str] = []
```

반드시:

```python
Field(default_factory=list)
Field(default_factory=dict)
```

사용.

---

# 35. extra="forbid"

Agent 관련 Model은 가능하면 모두:

```python
ConfigDict(extra="forbid", str_strip_whitespace=True)
```

정책을 사용한다.

예상하지 않은 LLM Structured Output 필드를
조용히 수용하지 않기 위함이다.

---

# 36. `Any` 사용 범위 제한

`Any`는 다음 자유형 Tool/Evidence Payload에서만 허용한다.

```text
ToolExecution.input
ToolExecution.output
Evidence.data
```

그 외 필드는 가능한 한 명확한 Type을 사용한다.

---

# 37. Ground Truth Leakage 금지

이번 Agent Model에는 다음 필드를 절대 추가하지 않는다.

```text
ground_truth_id
expected_ground_truth
known_vulnerability
benchmark_result
zap_result
semgrep_result
```

Ground Truth / Benchmark는 Evaluation 단계 전용이다.

---

# 38. Unit Test 파일

생성:

```text
tests/unit/test_agent_models.py
```

이번 D02-T03에서는 기본 Contract Test를 작성한다.

D02-T04에서는 Invalid JSON / 누락 필드 / Enum Validation을
더 체계적으로 확장할 예정이다.

---

# 39. TestPlan / TestCase Test

최소:

```text
정상 TestCase 생성
RiskLevel 저장
priority 저장
TestPlan에 TestCase list 저장
JSON serialization 성공
```

그리고:

```text
priority = 0
```

은 ValidationError.

---

# 40. ToolDefinition Test

최소:

```text
capabilities 저장
assessment_types 저장
risk_level 저장
input_schema / output_schema 저장
```

빈 capability list를 금지하도록 구현한 경우
ValidationError 테스트도 포함한다.

---

# 41. ToolSelection Test

최소:

```text
selection_id
test_id
tool_name
reason
risk_level
```

정상 저장 확인.

---

# 42. ToolExecution Test

최소:

```text
SUCCESS 실행 기록 생성
input/output dict 저장
ExecutionStatus 직렬화 확인
ToolError 포함 FAILED 기록 생성
duration_ms >= 0
```

다음은 ValidationError:

```text
duration_ms = -1
```

---

# 43. Evidence Test

최소:

```text
Evidence 생성
assessment_id / test_id / execution_id 연결
data 저장
datetime JSON serialization
```

민감정보 Masking 로직은 테스트하지 않는다.

이번 Task 범위가 아니다.

---

# 44. CandidateFinding Test

최소:

```text
Evidence 1개 이상 → 생성 성공
evidence_ids=[] → ValidationError
Severity 직렬화 성공
```

---

# 45. VerificationRequest Test

각 decision 값 중 최소 하나의 정상 생성 테스트.

그리고:

```text
round = 0
```

은 ValidationError.

허용되지 않은 decision 문자열은 ValidationError여야 한다.

---

# 46. Finding Test

최소:

```text
필수 필드 전체 입력 → 생성 성공
Evidence ID 1개 이상
Severity
AssessmentType
ValidationStatus
OWASP/CWE list
JSON serialization
```

다음은 실패:

```text
evidence_ids=[]
```

---

# 47. AgentEvent Test

최소:

```text
허용 event_type 생성 성공
datetime JSON serialization
test_id/tool_name optional
```

허용되지 않은 event_type은 ValidationError.

---

# 48. Extra Field Test

최소 하나 이상의 Agent Model에서:

```python
with pytest.raises(ValidationError):
    ...
```

형태로 미정의 필드 거부를 검증한다.

---

# 49. Mutable Default Isolation Test

최소 다음 중 2개 이상 검증:

```text
TestPlan.tests
ToolExecution.input/output
Evidence.data
Finding mapping lists
```

서로 다른 instance 간 기본 객체가 공유되지 않아야 한다.

---

# 50. Import Test

다음 import가 성공해야 한다.

```bash
python -c "from secureprobe.models import TestPlan, TestCase, ToolDefinition, ToolSelection, ToolExecution, ToolError, Evidence, CandidateFinding, VerificationRequest, Finding, AgentEvent; print('IMPORT_OK')"
```

---

# 51. 개별 Unit Test

```bash
pytest tests/unit/test_agent_models.py -q
```

PASS해야 한다.

---

# 52. 전체 Regression Test

```bash
pytest -q
```

다음 기존 테스트 포함 전체 PASS:

```text
Python Environment Smoke
Package Structure Smoke
Enum Test
Assessment Model Test
Agent Model Test
```

---

# 53. D02-T04와의 경계

이번 Task에서도 기본 Unit Test는 작성한다.

하지만 다음 exhaustive validation은 D02-T04의 주 목적이다.

```text
모든 Required Field 개별 누락
모든 잘못된 Enum 값
Malformed Structured Output
다수 Schema Validation Error 조합
```

따라서 D02-T03에서 지나치게 많은 Validation Test를 추가하여
D02-T04 범위를 잠식하지 않는다.

---

# 54. __init__.py Export

다음 Model을 export한다.

```text
TestPlan
TestCase
ToolDefinition
ToolSelection
ToolExecution
ToolError
Evidence
CandidateFinding
VerificationRequest
Finding
AgentEvent
```

기존 Assessment / Enum export는 유지한다.

---

# 55. 수정 금지 파일

다음은 수정하지 않는다.

```text
secureprobe/models/enums.py
secureprobe/models/assessment.py

PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md

secureprobe/agent/*
secureprobe/web/*
secureprobe/source/*
secureprobe/report/*
```

---

# 56. 결과 문서

반드시 생성:

```text
docs/05_ai_development/codex_results/day02/
D02-T03_AGENT_MODELS_RESULT_v0.1.md
```

---

# 57. 결과 문서 필수 내용

```text
Task ID
Status
Implemented Models
Created Files
Modified Files
Enum Reuse
Validation Rules
Evidence Traceability
Ground Truth Leakage Check
Unit Test Result
Full Test Result
Import Validation
Schema Consistency
Issues
Next Task
```

---

# 58. 결과 문서에 명시할 책임 분리

반드시 다음을 기록한다.

```text
ToolDefinition은 Registry 데이터 구조만 정의하며 Registry 로직은 구현하지 않음.

ToolExecution은 실행 기록 구조만 정의하며 Tool 실행은 구현하지 않음.

Evidence는 데이터 구조만 정의하며 민감정보 Masking 로직은 Evidence 생성 계층에서 구현 예정.

CandidateFinding/Finding은 Evidence ID를 강제하지만 실제 Analyzer/Verifier 판단은 구현하지 않음.

Ground Truth와 Benchmark 정보는 Agent Model에 포함하지 않음.
```

---

# 59. 완료 체크리스트

```text
[ ] plan.py 생성
[ ] tool.py 생성
[ ] evidence.py 생성
[ ] finding.py 생성
[ ] event.py 생성

[ ] TestPlan 구현
[ ] TestCase 구현
[ ] ToolDefinition 구현
[ ] ToolSelection 구현
[ ] ToolExecution 구현
[ ] ToolError 구현
[ ] Evidence 구현
[ ] CandidateFinding 구현
[ ] VerificationRequest 구현
[ ] Finding 구현
[ ] AgentEvent 구현

[ ] 기존 Enum 재사용
[ ] Enum 중복 정의 없음
[ ] Candidate Evidence ID 최소 1개
[ ] Finding Evidence ID 최소 1개
[ ] duration_ms 음수 거부
[ ] priority 1 이상
[ ] verification round 1 이상
[ ] event_type 제한
[ ] verification decision 제한
[ ] extra field 거부
[ ] mutable default 안전

[ ] Ground Truth 관련 필드 없음
[ ] ZAP/Semgrep 관련 필드 없음

[ ] test_agent_models.py 생성
[ ] 개별 Unit Test PASS
[ ] 전체 pytest PASS
[ ] Import PASS

[ ] 결과 문서 생성
[ ] 결과 파일명 _RESULT_ 규칙 준수
```

---

# 60. 완료 조건

다음 조건을 모두 만족하면 D02-T03 완료다.

```text
WBS D02-T03 Model 전체 구현
DATA_SCHEMA의 핵심 Field와 의미 일치
Evidence Traceability 유지
Structured Output JSON 직렬화 가능
Invalid 핵심 값 Validation
기존 Regression Test PASS
Agent 실제 로직 구현 없음
Ground Truth Leakage 없음
결과 문서 작성 완료
```

---

# 61. 변경 가능 파일

```text
secureprobe/models/plan.py
secureprobe/models/tool.py
secureprobe/models/evidence.py
secureprobe/models/finding.py
secureprobe/models/event.py
secureprobe/models/__init__.py

tests/unit/test_agent_models.py

docs/05_ai_development/codex_results/day02/
D02-T03_AGENT_MODELS_RESULT_v0.1.md
```

---

# 62. Git 검증

작업 전:

```bash
git status
```

작업 후:

```bash
git status
git diff --stat
git diff
```

변경 파일이 이번 Task 범위인지 확인한다.

---

# 63. 권장 Commit Message

```text
feat: add agent domain models
```

다음 사용 금지:

```text
git commit --amend
git push --force
```

---

# 64. 실패 처리

다음 경우 `COMPLETED`로 기록하지 않는다.

```text
WBS 대상 Model 누락
DATA_SCHEMA 핵심 Field 임의 변경
Evidence 없는 Finding 생성 허용
잘못된 Risk/Execution/Severity/Validation 값 허용
Ground Truth 정보를 Agent Model에 포함
기존 Enum 중복 정의
실제 Agent 실행 로직 구현
Unit Test 실패
전체 pytest 실패
Import 실패
```

상태:

```text
BLOCKED
또는
FAILED
```

로 기록한다.

---

# 65. 완료 보고 형식

```text
D02-T03 AGENT MODEL IMPLEMENTATION

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- TestPlan
- TestCase
- ToolDefinition
- ToolSelection
- ToolExecution
- ToolError
- Evidence
- CandidateFinding
- VerificationRequest
- Finding
- AgentEvent

Validation:
- Enum Reuse: PASS / FAIL
- Evidence Traceability: PASS / FAIL
- Candidate Evidence Required: PASS / FAIL
- Finding Evidence Required: PASS / FAIL
- ToolExecution duration: PASS / FAIL
- Test priority: PASS / FAIL
- Verification round: PASS / FAIL
- Event Type: PASS / FAIL
- Verification Decision: PASS / FAIL
- Extra Field: PASS / FAIL
- Mutable Defaults: PASS / FAIL
- Ground Truth Leakage: PASS / FAIL
- Import: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Schema Consistency: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day02/
D02-T03_AGENT_MODELS_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D02-T04 — Validation Unit Test
```

---

# 66. 작업 종료 원칙

D02-T03 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D02-T04 — Validation Unit Test
```
