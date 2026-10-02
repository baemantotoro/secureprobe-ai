# D02-T04 — Validation Test Hardening and Full Regression Recheck v0.1

## 1. 목적

D02-T04 Validation Unit Test의 1차 구현은 완료되었으나,
기존 작업지침 대비 일부 검증 항목이 누락되었고 결과 문서의 전체 pytest 결과가
D02-T03 당시 결과와 동일하게 기록되어 있어 실제 전체 회귀 재실행 여부를 다시 확인해야 한다.

이번 작업의 목적은 다음 세 가지다.

```text
1. 누락된 Validation / Security Contract Test 보강
2. 실제 전체 `pytest -q` 재실행
3. D02-T04 결과 문서 갱신
```

이번 작업은 Test Hardening 전용이며,
Production Code는 원칙적으로 수정하지 않는다.

---

## 2. 작업 ID

기준 Task:

```text
D02-T04 — Validation Unit Test
```

보강 작업명:

```text
D02-T04 — Validation Test Hardening
```

선행 상태:

```text
D02-T01 COMPLETED
D02-T02 COMPLETED
D02-T03 COMPLETED
D02-T04 INITIAL IMPLEMENTATION COMPLETED
```

이번 보강 완료 후:

```text
D02-T04 FINAL COMPLETED
DAY 2 READY TO CLOSE
```

---

## 3. 기준 문서

다음 문서를 수정하지 않고 기준으로 사용한다.

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 4. 기존 Validation Test

현재 파일:

```text
tests/unit/test_schema_validation.py
```

현재 기본 검증은 유지한다.

기존 Test를 삭제하거나 단순화하지 않는다.

이번 작업에서는 누락된 항목을 추가한다.

---

# 5. Production Code 수정 원칙

다음 Production Code는 원칙적으로 수정하지 않는다.

```text
secureprobe/models/enums.py
secureprobe/models/assessment.py
secureprobe/models/plan.py
secureprobe/models/tool.py
secureprobe/models/evidence.py
secureprobe/models/finding.py
secureprobe/models/event.py
secureprobe/models/__init__.py
```

Validation Test가 실패하면:

```text
1. 먼저 실제 Schema Defect인지 확인
2. 결과 문서 Issues에 기록
3. Production Code를 조용히 수정하지 않음
```

명백한 Test 자체 오류만 Test에서 수정한다.

---

# 6. 이번 보강의 핵심 누락 항목

다음 검증을 추가한다.

```text
AssessmentResult Required Field
TestCase Required Field
ToolSelection Validation
ToolExecution Required Field
ToolExecution malformed output
ToolError Validation
Evidence Required Field
Evidence Sensitive Field Injection
CandidateFinding Required Field
Finding Required Field
Finding Invalid Enum
Finding Mapping Type
AgentEvent Required Field

Ground Truth Leakage
Benchmark Leakage
Internal Reasoning Injection
```

---

# 7. AssessmentResult Required Field Test

정상 기준 payload를 하나 만든 뒤,
다음 필드를 하나씩 제거하여 ValidationError를 검증한다.

```text
assessment_id
assessment_type
status
target
started_at
```

권장 방식:

```python
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
```

각 필드 누락 시:

```text
ValidationError
```

여야 한다.

---

# 8. TestCase Required Field Test

정상 TestCase payload를 기준으로 다음 필드를 각각 제거한다.

```text
test_id
category
target
reason
required_capability
risk_level
priority
```

각 누락:

```text
ValidationError
```

---

# 9. ToolSelection Validation Test

현재 D02-T04 보강에서 반드시 추가한다.

필수 필드:

```text
selection_id
test_id
tool_name
reason
risk_level
```

검증 항목:

```text
정상 생성
필수 필드 누락 → ValidationError
risk_level = "UNSAFE" → ValidationError
```

---

# 10. ToolExecution Required Field Test

정상 ToolExecution payload를 기준으로 다음 필드를 각각 제거한다.

```text
execution_id
test_id
tool_name
status
started_at
```

각 누락:

```text
ValidationError
```

---

# 11. ToolExecution Output Type Test

기존 Test는 malformed input만 일부 검증했다.

다음을 추가한다.

실패:

```text
output = ["invalid"]
output = "raw-string"
```

성공:

```text
output = {}
output = {"status": 200}
```

---

# 12. ToolError Validation Test

정상:

```python
ToolError(
    code="HTTP_TIMEOUT",
    message="request timed out",
    retryable=True,
)
```

실패:

```text
code = ""
code = "   "
message = ""
message = "   "
```

가능하면 `retryable`도 비정상 타입에 대해 검증한다.

단, Pydantic coercion 특성으로 bool 변환이 허용될 경우
Test 실패를 Production Defect로 간주하지 말고 Issues에 기록한다.

---

# 13. Evidence Required Field Test

정상 Evidence payload를 기준으로 다음 필드를 하나씩 제거한다.

```text
evidence_id
assessment_id
test_id
execution_id
type
source
location
created_at
```

각 누락:

```text
ValidationError
```

---

# 14. Evidence Sensitive Field Injection Test

Evidence Top-level에 다음 필드를 추가하면 실패해야 한다.

```text
password
raw_token
authorization_header
api_key
secret_key
```

예:

```python
payload["password"] = "secret"
Evidence.model_validate(payload)
```

→ ValidationError

주의:

```text
Evidence.data 내부 Masking은 이번 Task 범위가 아니다.
```

---

# 15. CandidateFinding Required Field Test

정상 CandidateFinding payload에서 다음 필드를 하나씩 제거한다.

```text
candidate_id
test_id
title
severity
location
reasoning_summary
evidence_ids
```

각 누락:

```text
ValidationError
```

---

# 16. CandidateFinding Evidence Test 분리

기존 Test에서:

```text
severity invalid
evidence_ids=[]
```

가 동시에 들어간 경우
어떤 Contract로 실패했는지 명확하지 않을 수 있다.

따라서 별도 Test로 분리한다.

### Evidence 없는 Candidate

```text
severity = valid
evidence_ids = []
```

→ ValidationError

### Invalid Severity

```text
severity = "SEVERE"
evidence_ids = ["EV-001"]
```

→ ValidationError

---

# 17. Finding Required Field Test

정상 Finding payload에서 다음 필드를 하나씩 제거한다.

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
impact
remediation
developer_guide
ai_reasoning_summary
validation_status
```

각 누락:

```text
ValidationError
```

다음은 현재 Optional/default 정책 유지:

```text
owasp_mapping
cwe_mapping
```

---

# 18. Finding Invalid Enum Test

각 항목을 독립적으로 검증한다.

### Invalid Severity

```text
severity = "SEVERE"
```

### Invalid AssessmentType

```text
assessment_type = "DYNAMIC"
```

### Invalid ValidationStatus

```text
validation_status = "CONFIRMED"
```

모두:

```text
ValidationError
```

---

# 19. Finding Mapping Type Test

정상:

```text
owasp_mapping = []
cwe_mapping = []

owasp_mapping = ["A03:2021-Injection"]
cwe_mapping = ["CWE-89"]
```

실패:

```text
owasp_mapping = "A03:2021-Injection"
cwe_mapping = "CWE-89"
```

각 필드는 list 구조여야 한다.

---

# 20. AgentEvent Required Field Test

정상 AgentEvent payload에서 다음 필드를 하나씩 제거한다.

```text
event_id
assessment_id
event_type
timestamp
summary
```

각 누락:

```text
ValidationError
```

---

# 21. Ground Truth Leakage Test

SecureProbe Assessment Agent와 Ground Truth Evaluation 경계를 Test로 증명한다.

다음 필드를 Agent Model에 입력하면 거부되어야 한다.

```text
ground_truth_id
expected_ground_truth
known_vulnerability
```

최소 다음 Model에서 검증한다.

```text
TestPlan
CandidateFinding
Finding
```

예:

```python
payload["ground_truth_id"] = "GT-01"
with pytest.raises(ValidationError):
    Finding.model_validate(payload)
```

---

# 22. Benchmark Leakage Test

다음 필드는 Agent Model에 들어가면 안 된다.

```text
benchmark_result
zap_result
semgrep_result
```

최소 다음 Model에서 검증:

```text
TestPlan
Finding
```

예:

```python
payload["zap_result"] = {"alert": "SQL Injection"}
```

→ ValidationError

이 Test는 다음 설계 원칙을 증명한다.

```text
ZAP / Semgrep 결과를 SecureProbe Agent 입력으로 사용하지 않는다.
```

---

# 23. Internal Reasoning Injection Test

다음 필드는 Structured Output Model에 허용하지 않는다.

```text
chain_of_thought
full_reasoning
hidden_reasoning
internal_reasoning
```

최소 다음 Model:

```text
CandidateFinding
Finding
```

각 extra field 입력:

```text
ValidationError
```

허용되는 것은:

```text
CandidateFinding.reasoning_summary
Finding.ai_reasoning_summary
```

뿐이다.

---

# 24. Extra Field Global Coverage 확인

최종적으로 다음 Domain마다 최소 1개 extra field 거부 Test가 있어야 한다.

```text
Assessment
Plan
Tool
Evidence
Finding
Event
```

현재 Coverage가 부족하면 추가한다.

---

# 25. Mutable Default Coverage 보강

기존 Test 외에 Agent 영역에서 최소 하나 더 확인한다.

권장:

```text
Evidence.data
Finding.owasp_mapping
Finding.cwe_mapping
```

예:

```python
finding_a.owasp_mapping.append("A03")
assert finding_b.owasp_mapping == []
```

Assessment 영역과 Agent 영역 모두
instance 간 mutable object가 공유되지 않음을 보장한다.

---

# 26. JSON Serialization Coverage 확인

최종적으로 다음 Model의 JSON serialization을 확인한다.

```text
AssessmentRequest
AssessmentResult
TestPlan
ToolExecution
Evidence
Finding
AgentEvent
```

모든 Model에 별도 Test를 만들 필요는 없으나,
최소 이 목록이 하나 이상의 Test에서 실제로 실행돼야 한다.

검증:

```text
Enum → string
datetime → JSON-compatible ISO datetime
nested model → dict
```

---

# 27. JSON Round-trip

다음 두 Model은 반드시 round-trip을 유지한다.

```text
AssessmentRequest
Finding
```

형태:

```python
payload = model.model_dump(mode="json")
restored = Model.model_validate(payload)
```

---

# 28. Datetime Validation 보강

최소 다음 두 종류 이상 유지한다.

```text
Evidence.created_at = "not-a-date"
AgentEvent.timestamp = "tomorrow"
```

→ ValidationError

가능하면:

```text
ToolExecution.started_at
AssessmentResult.started_at
```

중 하나를 추가해도 된다.

---

# 29. Whitespace-only Validation 보강

최소 다음 Domain에서 검증한다.

```text
TestCase.test_id = "   "
ToolDefinition.tool_name = "   "
Finding.finding_id = "   "
ToolError.code = "   "
```

`str_strip_whitespace=True + min_length=1` 정책이
실제로 작동해야 한다.

---

# 30. Test 함수 설계

한 Test 함수 안에 지나치게 많은 검증을 넣지 않는다.

실패 시 원인이 바로 드러나도록
다음 수준으로 나눌 것을 권장한다.

```text
test_assessment_result_required_fields
test_test_case_required_fields
test_tool_selection_validation
test_tool_execution_required_fields
test_tool_error_validation
test_evidence_required_fields
test_evidence_sensitive_field_rejection
test_candidate_required_fields
test_finding_required_fields
test_finding_enum_validation
test_finding_mapping_types
test_agent_event_required_fields
test_ground_truth_leakage_rejected
test_benchmark_leakage_rejected
test_internal_reasoning_fields_rejected
```

함수명은 동일 의미면 달라도 된다.

---

# 31. Validation Test 개별 실행

먼저:

```bash
pytest tests/unit/test_schema_validation.py -q
```

실행한다.

실제 출력 결과를 기록한다.

예:

```text
XX passed in X.XXs
```

숫자를 추정하거나 이전 결과를 재사용하지 않는다.

---

# 32. Day 2 Unit Test 전체 실행

다음 실행:

```bash
pytest tests/unit -q
```

실제 결과를 기록한다.

---

# 33. 전체 Regression Test

반드시 새로 실행한다.

```bash
pytest -q
```

중요:

```text
D02-T03 당시 "27 passed" 결과를 재사용하지 않는다.
```

D02-T04에서 Test가 추가되었으므로
전체 Test 수는 기존보다 증가하는 것이 정상이다.

실제 pytest 출력값을 그대로 결과 문서에 기록한다.

---

# 34. 전체 pytest 결과 검증

최소 다음 Test 파일이 collection 되는지 확인한다.

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py

tests/unit/test_enums.py
tests/unit/test_assessment_models.py
tests/unit/test_agent_models.py
tests/unit/test_schema_validation.py
```

필요하면:

```bash
pytest --collect-only -q
```

로 collection을 확인할 수 있다.

단, 필수 명령은 아니다.

---

# 35. Test Count Consistency

결과 문서에 기록하는 Test 수는
실제 실행 결과와 일치해야 한다.

예:

```text
Schema Validation:
<actual> passed

Day 2 Unit:
<actual> passed

Full Regression:
<actual> passed
```

이전 문서의 숫자를 복사하지 않는다.

---

# 36. Import Regression

다음 명령을 실행한다.

```bash
python -c "from secureprobe.models import AssessmentRequest, AssessmentResult, TestPlan, ToolSelection, ToolExecution, ToolError, Evidence, CandidateFinding, Finding, AgentEvent; print('IMPORT_OK')"
```

결과:

```text
IMPORT_OK
```

---

# 37. Schema Consistency

Test 완료 후 다시 확인한다.

```text
Enum
Assessment
Plan
Tool
Evidence
Finding
Event
```

`DATA_SCHEMA_v0.1.md`의 필드와 의미를 기준으로 한다.

문서와 코드 간 중대한 불일치가 새로 발견되면:

```text
Schema Consistency: FAIL
Status: BLOCKED
```

로 기록한다.

---

# 38. Security Contract 최종 확인

결과 문서에 다음을 반드시 명시한다.

```text
Raw Password Injection Rejected
Evidence-less Candidate Rejected
Evidence-less Finding Rejected
Ground Truth Leakage Rejected
Benchmark Leakage Rejected
Internal Reasoning Injection Rejected
Extra Field Rejected
```

각 항목:

```text
PASS / FAIL
```

로 기록한다.

---

# 39. Production Code Unchanged 확인

Git diff로 다음 파일이 변경되지 않았는지 확인한다.

```text
secureprobe/models/enums.py
secureprobe/models/assessment.py
secureprobe/models/plan.py
secureprobe/models/tool.py
secureprobe/models/evidence.py
secureprobe/models/finding.py
secureprobe/models/event.py
secureprobe/models/__init__.py
```

결과 문서:

```text
Production Code Changed: No
```

가 되어야 한다.

실제로 변경됐다면 이유를 명확히 기록한다.

---

# 40. 결과 문서 갱신

다음 파일을 수정한다.

```text
docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md
```

기존 문서를 교체하거나 갱신한다.

새 결과 파일을 추가 생성하지 않는다.

---

# 41. 결과 문서 필수 내용

최소 다음 구조를 포함한다.

```text
Task ID
Status
Validation Scope
Added Validation Coverage
Security Contract
Production Code Changed
Schema Validation Test Result
Day 2 Unit Test Result
Full Regression Result
Import Validation
Schema Consistency
Issues
Day 2 Completion Decision
Next Task
```

---

# 42. 결과 문서 권장 예시

```text
# D02-T04 — Validation Unit Test Result v0.1

## Status

COMPLETED

## Added Validation Coverage

- AssessmentResult required fields
- TestCase required fields
- ToolSelection validation
- ToolExecution required fields
- ToolError validation
- Evidence required fields
- Evidence sensitive field rejection
- CandidateFinding required fields
- Finding required fields
- Finding enum validation
- Finding mapping validation
- AgentEvent required fields
- Ground Truth leakage rejection
- Benchmark leakage rejection
- Internal reasoning field rejection

## Security Contract

Raw Password Injection:
PASS

Evidence-less Candidate:
PASS

Evidence-less Finding:
PASS

Ground Truth Leakage:
PASS

Benchmark Leakage:
PASS

Internal Reasoning Injection:
PASS

Extra Field:
PASS

## Production Code Changed

No

## Test Result

Schema Validation:
<actual> passed

Day 2 Unit:
<actual> passed

Full pytest:
<actual> passed

Import:
PASS

Schema Consistency:
PASS

## Issues

None

## Day 2 Completion

READY TO CLOSE

## Next Task

D03-T01 — SecureBoard Project 생성
```

---

# 43. 완료 체크리스트

```text
[ ] AssessmentResult required field test
[ ] TestCase required field test
[ ] ToolSelection validation
[ ] ToolExecution required field test
[ ] ToolExecution output type test
[ ] ToolError validation
[ ] Evidence required field test
[ ] Evidence sensitive field injection test
[ ] CandidateFinding required field test
[ ] Candidate evidence-only failure test
[ ] Candidate invalid severity test
[ ] Finding required field test
[ ] Finding invalid severity test
[ ] Finding invalid assessment type test
[ ] Finding invalid validation status test
[ ] Finding mapping type test
[ ] AgentEvent required field test

[ ] Ground Truth leakage test
[ ] Benchmark leakage test
[ ] Internal reasoning injection test

[ ] Mutable default coverage
[ ] JSON serialization coverage
[ ] JSON round-trip
[ ] malformed datetime
[ ] whitespace-only validation

[ ] schema validation test 실행
[ ] tests/unit 전체 실행
[ ] pytest -q 전체 실행
[ ] actual test count 기록
[ ] import validation
[ ] schema consistency

[ ] Production Code 변경 없음
[ ] 결과 문서 갱신
```

---

# 44. 완료 조건

다음 조건을 모두 만족해야 완료다.

```text
누락 Validation Coverage 보강
Security Contract Test 완료
Ground Truth / Benchmark Leakage 차단 증명
Internal Reasoning Injection 차단 증명
개별 Validation Test PASS
Day 2 Unit Test PASS
전체 pytest PASS
실제 Test Count 기록
Production Code 불필요 변경 없음
Schema Consistency PASS
결과 문서 갱신
```

---

# 45. Day 2 최종 종료 조건

이번 보강 작업 완료 후:

```text
D02-T01 COMPLETED
D02-T02 COMPLETED
D02-T03 COMPLETED
D02-T04 COMPLETED
```

이면:

```text
DAY 2 — COMPLETED
```

로 종료한다.

Day 2 완료 시 다음 Milestone 상태:

```text
M1 — Architecture + Schema + Agent Skeleton
```

중 Day 2 범위를 충족한 것으로 기록한다.

---

# 46. 변경 가능 파일

이번 작업의 예상 변경 파일:

```text
tests/unit/test_schema_validation.py

docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md
```

작업지침 저장 시:

```text
docs/05_ai_development/codex_tasks/day02/
D02-T04_VALIDATION_TEST_HARDENING_v0.1.md
```

---

# 47. 수정 금지 파일

```text
secureprobe/models/*
PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

---

# 48. 기능 범위 확장 금지

이번 작업에서는 다음을 구현하지 않는다.

```text
SecureBoard
Safety Gate
Observer
Planner
Tool Registry
Tool Selector
Executor
Analyzer
Verifier
Report
Ground Truth
Benchmark
Evaluation Engine
```

---

# 49. Git 검증

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

확인:

```text
Production Model 변경 없음
test_schema_validation.py 보강
D02-T04 결과 문서 갱신
기준 문서 변경 없음
```

---

# 50. 권장 Commit Message

```text
test: harden schema validation coverage
```

다음 사용 금지:

```text
git commit --amend
git push --force
```

---

# 51. 완료 보고 형식

```text
D02-T04 VALIDATION TEST HARDENING

Status:
COMPLETED / BLOCKED / FAILED

Added Coverage:
- Required Fields: PASS / FAIL
- ToolSelection: PASS / FAIL
- ToolError: PASS / FAIL
- Evidence Security: PASS / FAIL
- Candidate Contract: PASS / FAIL
- Finding Contract: PASS / FAIL
- Event Contract: PASS / FAIL
- Ground Truth Leakage: PASS / FAIL
- Benchmark Leakage: PASS / FAIL
- Internal Reasoning Injection: PASS / FAIL

Validation:
- Schema Validation Test: PASS / FAIL
- Day 2 Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Schema Consistency: PASS / FAIL
- Production Code Unchanged: PASS / FAIL

Test Count:
- Schema Validation: <actual>
- Day 2 Unit: <actual>
- Full pytest: <actual>

Result Document:
docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Day 2:
COMPLETED / NOT READY

Next Task:
D03-T01 — SecureBoard Project 생성
```

---

# 52. 작업 종료 원칙

이번 보강 완료 후 다음 Task를 자동 시작하지 않는다.

GitHub 반영 상태와 실제 Test 결과를 확인한 뒤
Day 2를 공식 종료한다.
