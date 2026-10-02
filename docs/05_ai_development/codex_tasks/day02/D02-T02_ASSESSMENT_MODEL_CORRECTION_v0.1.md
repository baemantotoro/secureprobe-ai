# D02-T02 — Assessment Model Correction and Test Hardening v0.1

## 1. 목적

D02-T02 Assessment Model 구현은 완료되었으나, 다음 설계/지침 불일치가 확인되었다.

1. `AssessmentRequest`에서 `authorization_confirmed=False`를 ValidationError로 처리하고 있음
2. 일부 Unit Test가 요구사항을 충분히 검증하지 않음
3. `AssessmentRun.assessment_type`의 필수성 여부가 DATA_SCHEMA 정의와 다를 수 있음

이번 작업의 목적은 Assessment Model의 책임을 설계 문서와 일치시키고 테스트를 보강하여
D02-T02를 최종 완료 상태로 닫는 것이다.

기능 범위는 Assessment Model Layer 안에서만 유지한다.

---

## 2. 핵심 설계 원칙

`AssessmentRequest`는 입력 데이터 구조를 표현한다.

다음 필드는 사용자의 확인 상태를 보존하는 용도다.

```text
authorization_confirmed
```

이 값이 `False`라고 해서 Model 생성 자체를 실패시키지 않는다.

실제 Active Assessment 허용/차단은 향후 Safety Gate가 담당한다.

정확한 책임 분리:

```text
AssessmentRequest
→ 입력값 구조화

Safety Gate
→ authorization_confirmed + target scope 기반 ALLOW / BLOCK 판단
```

---

## 3. 수정 대상 파일

수정 가능:

```text
secureprobe/models/assessment.py
tests/unit/test_assessment_models.py

docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

필요한 경우:

```text
secureprobe/models/__init__.py
```

는 export 변경이 있을 때만 수정 가능하다.

---

## 4. Authorization Validation 수정

현재 `AssessmentRequest`에 다음 취지의 코드가 있다.

```python
if self.authorization_confirmed is not True:
    raise ValueError(
        "authorization_confirmed must be true for WEB assessment"
    )
```

이 검증을 제거한다.

WEB Assessment의 Model-level 필수 조건은 다음만 유지한다.

```text
assessment_type == WEB
→ target_url 필수
```

SOURCE Assessment:

```text
assessment_type == SOURCE
→ source_directory 필수
```

`authorization_confirmed`는 bool 값으로 저장만 한다.

기본값:

```python
False
```

를 유지할 수 있다.

---

## 5. Safety Gate 책임 명시

이번 Task에서는 Safety Gate를 구현하지 않는다.

다만 결과 문서에 다음을 명확히 기록한다.

```text
authorization_confirmed 값의 정책 판정은 Assessment Model이 아니라
향후 Safety Gate에서 처리한다.
```

---

## 6. WEB Request Test 보강

다음 테스트를 반드시 추가 또는 수정한다.

### 정상

```text
assessment_type = WEB
target_url 존재
authorization_confirmed = False
```

Model 생성 성공해야 한다.

예:

```python
request = AssessmentRequest(
    assessment_type=AssessmentType.WEB,
    target_url="http://localhost:8080",
    authorization_confirmed=False,
)

assert request.authorization_confirmed is False
```

---

## 7. WEB target_url Validation 유지

다음은 계속 ValidationError여야 한다.

```text
assessment_type = WEB
target_url 없음
```

---

## 8. SOURCE Validation 유지

다음은 ValidationError:

```text
assessment_type = SOURCE
source_directory 없음
```

다음은 성공:

```text
assessment_type = SOURCE
source_directory 존재
```

---

## 9. Credentials Raw Password 검증

`Credentials`에는 다음 필드만 존재해야 한다.

```text
username
password_ref
```

다음 필드는 존재하지 않아야 한다.

```text
password
```

테스트 예:

```python
assert "password" not in Credentials.model_fields
assert "username" in Credentials.model_fields
assert "password_ref" in Credentials.model_fields
```

---

## 10. Mutable Default Isolation Test

서로 다른 instance 사이에서 list/dict 기본값이 공유되지 않아야 한다.

최소 다음 모델을 검증한다.

```text
AssessmentScope
AssessmentRun.errors
AssessmentResult.findings
AssessmentResult.manual_review_required
AssessmentResult.errors
AssessmentResult.report_paths
```

예:

```python
a = AssessmentResult(...)
b = AssessmentResult(...)

a.findings.append("FIND-1")

assert b.findings == []
```

---

## 11. Extra Field Policy Test

현재 공통 Base Model에서:

```python
ConfigDict(extra="forbid")
```

를 사용한다면 테스트로 증명한다.

예:

```python
with pytest.raises(ValidationError):
    AssessmentScope(unknown_field="x")
```

최소 하나 이상의 Assessment 관련 Model에서 검증한다.

---

## 12. JSON Serialization Test

최소 하나의 Model이 JSON 친화적으로 직렬화되는지 확인한다.

권장 대상:

```text
AssessmentRequest
AssessmentResult
```

예:

```python
payload = request.model_dump(mode="json")
assert payload["assessment_type"] == "WEB"
```

datetime이 포함된 Result도 JSON mode에서 문자열로 변환되는지 확인할 수 있다.

---

## 13. Negative Count 검증 보강

기존:

```text
tests_planned = -1
```

외에 다음도 ValidationError여야 한다.

```text
tests_executed = -1
```

두 필드를 각각 검증한다.

---

## 14. AssessmentRun.assessment_type 정합성

현재 구현은:

```python
assessment_type: AssessmentType | None = None
```

이고 request에서 자동 동기화한다.

`DATA_SCHEMA_v0.1.md`에서는 `assessment_type`이 AssessmentRun 필드로 존재한다.

이번 Task에서는 다음 두 방안 중 하나를 선택하되,
문서와 구현 일관성을 우선한다.

### 권장안 A

`assessment_type`을 필수 입력으로 강제하지 않고
`request.assessment_type`에서 자동 설정하는 현재 편의 동작을 유지한다.

대신 결과 문서에 다음을 명시한다.

```text
AssessmentRun.assessment_type은 DATA_SCHEMA 필드이지만
runtime convenience를 위해 request에서 자동 파생한다.
```

그리고 다음 정합성 검증을 추가한다.

```text
assessment_type이 명시된 경우 request.assessment_type과 불일치하면 ValidationError
```

예:

```python
AssessmentRun(
    assessment_type=AssessmentType.SOURCE,
    request=web_request,
)
```

→ ValidationError

### 대안 B

`assessment_type`을 필수 필드로 변경하고 자동 동기화를 제거한다.

이 경우 DATA_SCHEMA와 더 엄격하게 일치하지만
중복 입력이 생긴다.

### 선택 원칙

v0.1에서는 **권장안 A**를 우선한다.

이유:

```text
중복 입력 방지
request와 run 간 타입 불일치 방지
runtime 편의성
```

단, 명시된 값과 request 값이 충돌하면 반드시 실패시킨다.

---

## 15. AssessmentRun Validator

권장 논리:

```text
if assessment_type is None:
    assessment_type = request.assessment_type
else:
    assessment_type == request.assessment_type 이어야 함
```

불일치 시:

```text
assessment_type must match request.assessment_type
```

등 명확한 ValidationError를 발생시킨다.

---

## 16. Unit Test 추가 항목

`tests/unit/test_assessment_models.py`에 최소 다음 검증을 포함한다.

```text
WEB target_url required
WEB authorization_confirmed=False accepted
SOURCE source_directory required
Credentials raw password field absent
AssessmentRun type auto-sync
AssessmentRun type mismatch rejected
Negative tests_planned rejected
Negative tests_executed rejected
Mutable defaults isolated
Extra fields rejected
JSON serialization works
```

---

## 17. 기존 테스트 유지

기존 Enum Unit Test:

```text
tests/unit/test_enums.py
```

기존 Smoke Test:

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py
```

를 수정하지 않는다.

---

## 18. 전체 테스트

개별:

```bash
pytest tests/unit/test_assessment_models.py -q
```

전체:

```bash
pytest -q
```

둘 다 PASS해야 한다.

---

## 19. Schema Consistency 재검증

다음 문서를 기준으로 비교한다.

```text
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
```

특히 다음 의미가 유지되는지 확인한다.

```text
AssessmentRequest = 입력 구조
Safety Gate = 허용/차단 정책
AssessmentRun = 실행 상태
AssessmentResult = 최종 요약
```

---

## 20. 결과 문서 갱신

다음 결과 문서를 수정한다.

```text
docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

상태:

```text
Status: COMPLETED
```

유지.

최소 다음 내용을 추가한다.

```text
Authorization Policy:
Model accepts authorization_confirmed=False.
Actual allow/block decision is delegated to Safety Gate.

AssessmentRun Type Policy:
assessment_type is derived from request when omitted.
Explicit mismatch is rejected.

Validation:
- WEB target_url required: PASS
- authorization_confirmed=False accepted: PASS
- SOURCE source_directory required: PASS
- Raw password field absent: PASS
- Negative counts rejected: PASS
- Mutable defaults isolated: PASS
- Extra fields rejected: PASS
- JSON serialization: PASS
- AssessmentRun type consistency: PASS
- Unit Test: PASS
- Full pytest: PASS
```

실제 테스트 수는 실제 pytest 출력 기준으로 기록한다.

---

## 21. 수정 금지 범위

다음은 수정하지 않는다.

```text
secureprobe/models/enums.py

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

## 22. 기능 범위 확장 금지

이번 작업에서 구현하지 않는다.

```text
Safety Gate 실제 코드
Tool Registry
TestPlan
TestCase
Evidence
Finding
AgentEvent
Planner
Observer
Executor
Analyzer
Verifier
Web Tool
Source Tool
```

---

## 23. 완료 체크리스트

```text
[ ] authorization_confirmed=True 강제 Validation 제거
[ ] WEB target_url required 유지
[ ] SOURCE source_directory required 유지

[ ] authorization_confirmed=False Model 생성 성공
[ ] Credentials에 raw password field 없음
[ ] tests_planned 음수 거부
[ ] tests_executed 음수 거부
[ ] Mutable Default isolation 검증
[ ] extra="forbid" 검증
[ ] JSON serialization 검증

[ ] AssessmentRun type 자동 동기화
[ ] 명시적 type mismatch 거부

[ ] 개별 Unit Test PASS
[ ] 전체 pytest PASS
[ ] 결과 문서 갱신
[ ] 범위 확대 없음
```

---

## 24. 완료 조건

다음 조건을 모두 만족하면 D02-T02를 최종 종료한다.

```text
Model과 Safety Policy 책임 분리
AssessmentRun 타입 정합성 보장
Validation Coverage 보강
전체 테스트 PASS
DATA_SCHEMA 의미 유지
결과 문서 갱신
```

---

## 25. Git 검증

작업 전후:

```bash
git status
git diff
```

예상 변경 범위:

```text
secureprobe/models/assessment.py
tests/unit/test_assessment_models.py
docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

---

## 26. 권장 Commit Message

```text
fix: align assessment validation with safety gate
```

다음은 사용하지 않는다.

```text
git commit --amend
git push --force
```

---

## 27. 완료 보고 형식

```text
D02-T02 ASSESSMENT MODEL CORRECTION

Status:
COMPLETED / BLOCKED / FAILED

Changes:
- authorization policy separation
- AssessmentRun type consistency
- validation test hardening

Validation:
- WEB target_url: PASS / FAIL
- authorization_confirmed=False: PASS / FAIL
- SOURCE source_directory: PASS / FAIL
- Raw Password Field: PASS / FAIL
- Negative Counts: PASS / FAIL
- Mutable Defaults: PASS / FAIL
- Extra Fields: PASS / FAIL
- JSON Serialization: PASS / FAIL
- Run Type Consistency: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Schema Consistency: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D02-T03 — Agent Model 구현
```

---

## 28. 작업 종료 원칙

이번 작업 완료 후 D02-T02를 종료한다.

다음 Task를 자동 시작하지 않는다.

```text
D02-T03 — Agent Model 구현
```
