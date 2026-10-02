# D02-T04 — Final Validation Closure v0.1

## 1. 목적

D02-T04 Validation Test Hardening까지 대부분 완료되었으나,
Day 2를 공식 종료하기 전에 다음 4개 Validation Coverage와 결과 문서 정리를 마무리한다.

이번 작업 범위는 다음으로 제한한다.

```text
1. CandidateFinding의 evidence_ids 필드 누락 검증
2. Finding의 evidence_ids 필드 누락 검증
3. Finding의 invalid validation_status 검증
4. Leakage Coverage 확장
   - TestPlan Ground Truth / Benchmark 차단
   - Finding internal reasoning 차단
```

그리고 실제 전체 테스트를 다시 실행하여
D02-T04 결과 문서를 최종 정리한다.

Production Code는 수정하지 않는다.

---

## 2. 작업 ID

기준 Task:

```text
D02-T04 — Validation Unit Test
```

최종 마무리 작업:

```text
D02-T04 — Final Validation Closure
```

이번 작업 완료 후:

```text
D02-T04 COMPLETED
DAY 2 READY TO CLOSE
```

---

## 3. 기준 문서

다음 문서를 기준으로 하며 수정하지 않는다.

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 4. 수정 대상

수정:

```text
tests/unit/test_schema_validation.py
```

갱신:

```text
docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md
```

작업지침 저장:

```text
docs/05_ai_development/codex_tasks/day02/
D02-T04_FINAL_VALIDATION_CLOSURE_v0.1.md
```

---

## 5. Production Code 수정 금지

다음 파일은 수정하지 않는다.

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

Git diff에서 위 파일 변경이 없어야 한다.

---

# 6. CandidateFinding evidence_ids 필드 누락 검증

현재 기존 Test는:

```text
evidence_ids = []
```

를 거부하는 것을 검증한다.

이번에는 **필드 자체가 누락된 경우**도 별도로 검증한다.

정상 payload 예:

```python
payload = {
    "candidate_id": "CF-600",
    "test_id": "TC-600",
    "title": "Missing security header",
    "severity": "MEDIUM",
    "location": "https://example.com",
    "reasoning_summary": "Header missing",
    "evidence_ids": ["EV-600"],
    "verification_required": True,
}
```

다음 수행:

```python
payload.pop("evidence_ids")
```

결과:

```text
ValidationError
```

이어야 한다.

기존 `test_candidate_finding_required_fields`의 parameterized list에:

```text
evidence_ids
```

를 추가해도 된다.

---

# 7. Finding evidence_ids 필드 누락 검증

현재 기존 Test는:

```text
evidence_ids = []
```

를 거부한다.

이번에는 **evidence_ids 필드 자체 누락**을 검증한다.

정상 Finding payload에서:

```python
payload.pop("evidence_ids")
```

결과:

```text
ValidationError
```

이어야 한다.

기존 `test_finding_required_fields`의 parameterized list에:

```text
evidence_ids
```

를 추가해도 된다.

---

# 8. Finding invalid validation_status 검증

다음 입력은 실패해야 한다.

```text
validation_status = "CONFIRMED"
```

정상 payload:

```text
validation_status = "TOOL_VERIFIED"
```

를 유지한 상태에서
validation_status만 `"CONFIRMED"`로 변경한다.

결과:

```text
ValidationError
```

이어야 한다.

이 Test는 다른 invalid field와 섞지 않는다.

즉:

```text
severity는 정상
assessment_type 정상
evidence_ids 정상
validation_status만 invalid
```

이어야 한다.

---

# 9. TestPlan Ground Truth Leakage 검증

SecureProbe Agent의 TestPlan에 다음 Evaluation 전용 필드가 유입되면 안 된다.

```text
ground_truth_id
expected_ground_truth
known_vulnerability
```

정상 TestPlan payload 예:

```python
payload = {
    "plan_id": "PLAN-600",
    "assessment_id": "RUN-600",
    "tests": [],
}
```

각 필드를 하나씩 추가:

```python
payload["ground_truth_id"] = "GT-01"
```

결과:

```text
ValidationError
```

이어야 한다.

---

# 10. TestPlan Benchmark Leakage 검증

다음 Benchmark 전용 필드도 TestPlan에서 거부한다.

```text
benchmark_result
zap_result
semgrep_result
```

예:

```python
payload["zap_result"] = {"alert": "SQL Injection"}
```

결과:

```text
ValidationError
```

이어야 한다.

이 Test의 목적은 다음 원칙 증명이다.

```text
ZAP / Semgrep 결과는 SecureProbe Agent 입력으로 사용하지 않는다.
```

---

# 11. Finding Internal Reasoning Injection 검증

현재 CandidateFinding에 대해 다음 필드 거부가 검증되어 있다.

```text
chain_of_thought
full_reasoning
hidden_reasoning
internal_reasoning
```

이번에는 Finding에도 동일 정책을 검증한다.

정상 Finding payload에 각 필드를 하나씩 추가한다.

예:

```python
payload["chain_of_thought"] = "..."
```

결과:

```text
ValidationError
```

이어야 한다.

허용되는 것은:

```text
ai_reasoning_summary
```

뿐이다.

---

# 12. 기존 Leakage Test 유지

기존 다음 Test는 삭제하거나 약화하지 않는다.

```text
Finding Ground Truth leakage
Finding Benchmark leakage
CandidateFinding internal reasoning rejection
```

이번 작업은 Coverage 확장이다.

---

# 13. Test 함수 권장 구조

다음처럼 분리 가능하다.

```text
test_candidate_finding_missing_evidence_ids_rejected
test_finding_missing_evidence_ids_rejected
test_finding_invalid_validation_status_rejected
test_testplan_ground_truth_and_benchmark_leakage_rejected
test_finding_internal_reasoning_fields_rejected
```

기존 parameterized test를 확장하는 방식도 허용한다.

중요한 것은 각 Contract가 독립적으로 검증되는 것이다.

---

# 14. 개별 Validation Test 실행

수정 후 반드시 실행:

```bash
pytest tests/unit/test_schema_validation.py -q
```

실제 결과 수를 기록한다.

예:

```text
<actual> passed in X.XXs
```

이전 `70 passed` 값을 재사용하지 않는다.

---

# 15. Day 2 Unit Test 실행

다음 실행:

```bash
pytest tests/unit -q
```

실제 결과를 기록한다.

---

# 16. 전체 Regression Test 실행

다음 실행:

```bash
pytest -q
```

실제 전체 결과를 기록한다.

이전:

```text
97 passed
```

값을 복사하지 않는다.

이번 변경 후 실제 결과를 사용한다.

---

# 17. Import Validation

다음 실행:

```bash
python -c "from secureprobe.models import AssessmentRequest, AssessmentResult, TestPlan, ToolSelection, ToolExecution, ToolError, Evidence, CandidateFinding, Finding, AgentEvent; print('IMPORT_OK')"
```

결과:

```text
IMPORT_OK
```

이어야 한다.

---

# 18. Schema Consistency 확인

다음 Model을 DATA_SCHEMA_v0.1 기준으로 다시 확인한다.

```text
CandidateFinding
Finding
TestPlan
```

확인 항목:

```text
Evidence ID 필수
Ground Truth 필드 없음
Benchmark 필드 없음
Internal reasoning 필드 없음
```

결과:

```text
Schema Consistency: PASS
```

---

# 19. Security Contract 최종 상태

결과 문서에 반드시 다음 항목을 각각 기록한다.

```text
Raw Password Injection: PASS
Evidence-less Candidate: PASS
Evidence-less Finding: PASS
Missing Candidate evidence_ids: PASS
Missing Finding evidence_ids: PASS
Invalid Finding validation_status: PASS
Ground Truth Leakage: PASS
Benchmark Leakage: PASS
Internal Reasoning Injection: PASS
Extra Field Rejection: PASS
```

---

# 20. Production Code Changed 확인

Git diff에서 다음이 변경되지 않았는지 확인한다.

```text
secureprobe/models/*
```

결과 문서:

```text
Production Code Changed: No
```

---

# 21. 결과 문서 정리

다음 파일을 최종 갱신한다.

```text
docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md
```

---

# 22. 결과 문서 필수 항목

최종 문서에 다음 항목이 모두 있어야 한다.

```text
Task ID
Status
Validation Scope
Final Added Coverage
Security Contract
Production Code Changed
Schema Validation Test Result
Day 2 Unit Test Result
Full pytest Result
Import Validation
Schema Consistency
Issues
Day 2 Completion Decision
Next Task
```

---

# 23. 결과 문서 권장 형식

```text
# D02-T04 — Validation Unit Test Result v0.1

## Status

COMPLETED

## Final Added Coverage

- CandidateFinding missing evidence_ids rejected
- Finding missing evidence_ids rejected
- Invalid Finding validation_status rejected
- TestPlan Ground Truth leakage rejected
- TestPlan Benchmark leakage rejected
- Finding internal reasoning fields rejected

## Security Contract

Raw Password Injection:
PASS

Evidence-less Candidate:
PASS

Evidence-less Finding:
PASS

Missing Candidate evidence_ids:
PASS

Missing Finding evidence_ids:
PASS

Invalid Finding validation_status:
PASS

Ground Truth Leakage:
PASS

Benchmark Leakage:
PASS

Internal Reasoning Injection:
PASS

Extra Field Rejection:
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

Import Validation:
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

# 24. 완료 체크리스트

```text
[ ] CandidateFinding missing evidence_ids
[ ] Finding missing evidence_ids
[ ] Finding invalid validation_status
[ ] TestPlan Ground Truth leakage
[ ] TestPlan Benchmark leakage
[ ] Finding internal reasoning injection

[ ] 기존 Leakage Test 유지
[ ] Schema Validation Test 재실행
[ ] tests/unit 재실행
[ ] pytest -q 전체 재실행
[ ] 실제 Test Count 기록
[ ] Import Validation PASS
[ ] Schema Consistency PASS
[ ] Production Code Changed: No
[ ] 결과 문서 최종 갱신
```

---

# 25. 완료 조건

다음 조건을 모두 만족하면 D02-T04를 최종 종료한다.

```text
남은 4개 Coverage gap 해소
Security Contract 전체 PASS
Validation Test PASS
Day 2 Unit Test PASS
Full Regression PASS
Import PASS
Schema Consistency PASS
Production Code 변경 없음
결과 문서 최종 정리
```

---

# 26. Day 2 종료 조건

이번 작업 완료 후:

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

로 기록한다.

---

# 27. 변경 가능 파일

```text
tests/unit/test_schema_validation.py

docs/05_ai_development/codex_results/day02/
D02-T04_VALIDATION_UNIT_TEST_RESULT_v0.1.md

docs/05_ai_development/codex_tasks/day02/
D02-T04_FINAL_VALIDATION_CLOSURE_v0.1.md
```

---

# 28. 수정 금지 파일

```text
secureprobe/models/*
PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

---

# 29. 기능 범위 확장 금지

다음은 구현하지 않는다.

```text
SecureBoard
Safety Gate
Observer
Planner
Tool Registry
Executor
Analyzer
Verifier
Report
Ground Truth
Benchmark
Evaluation Engine
```

---

# 30. Git 검증

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
Production Code 변경 없음
Validation Test 보강
Result Document 갱신
Task Document 추가
```

---

# 31. 권장 Commit Message

```text
test: finalize day 2 validation coverage
```

사용 금지:

```text
git commit --amend
git push --force
```

---

# 32. 완료 보고 형식

```text
D02-T04 FINAL VALIDATION CLOSURE

Status:
COMPLETED / BLOCKED / FAILED

Final Coverage:
- Candidate missing evidence_ids: PASS / FAIL
- Finding missing evidence_ids: PASS / FAIL
- Finding invalid validation_status: PASS / FAIL
- TestPlan Ground Truth leakage: PASS / FAIL
- TestPlan Benchmark leakage: PASS / FAIL
- Finding internal reasoning injection: PASS / FAIL

Validation:
- Schema Validation: PASS / FAIL
- Day 2 Unit: PASS / FAIL
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

# 33. 작업 종료 원칙

이번 Task 완료 후 추가 Validation 확장은 하지 않는다.

결과 확인 후 Day 2를 공식 종료하고
Day 3 SecureBoard 구현으로 이동한다.
