# D02-T02 — Assessment Models Implementation v0.1

## 1. 목적

`DATA_SCHEMA_v0.1.md`에 정의된 Assessment 관련 데이터 모델을 실제 Pydantic Model로 구현한다.

이번 Task의 목적은 SecureProbe AI의 진단 실행 단위와 상태를 구조화하여,
이후 Agent Flow와 Web/Source Assessment가 동일한 공통 Assessment 모델을 사용하도록 하는 것이다.

구현 대상:

```text
AssessmentRequest
AssessmentRun
ValidationResult
AssessmentError
AssessmentResult
```

필요한 최소 보조 모델:

```text
AssessmentScope
Credentials
```

이번 Task에서는 TestPlan, Finding, Evidence, Tool Model, Agent 로직은 구현하지 않는다.

---

## 2. 작업 ID와 근거

- WBS 기준: Day 2, Task 02
- 작업 ID: `D02-T02`
- 작업명: Assessment Model 구현
- 우선순위: P0
- 선행 작업: `D02-T01 — 공통 Enum 구현` 완료
- 다음 작업: `D02-T03 — Agent Model 구현`

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. 구현 위치

권장 파일:

```text
secureprobe/models/assessment.py
```

필요한 경우 기존:

```text
secureprobe/models/__init__.py
```

를 최소 수정하여 새 Model을 export한다.

---

## 4. 사용 Enum

다음 기존 Enum을 재사용한다.

```text
AssessmentType
AssessmentStatus
```

필요 시:

```text
ExecutionStatus
```

를 참조할 수 있으나 이번 Assessment Model에서는 필수 사용 대상으로 간주하지 않는다.

Enum을 새로 정의하지 않는다.

---

## 5. Pydantic 기준

Pydantic v2 기준으로 구현한다.

권장 import:

```python
from pydantic import BaseModel, ConfigDict, Field, model_validator
```

실제 구현 시 필요한 것만 import한다.

불필요한 custom validator를 남발하지 않는다.

---

## 6. AssessmentScope

Web/Source 공통 Scope 모델을 만든다.

최소 필드:

```text
allowed_hosts
allowed_paths
deny_paths
include_paths
exclude_paths
```

권장 타입:

```python
list[str]
```

기본값:

```python
default_factory=list
```

예:

```python
class AssessmentScope(BaseModel):
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    deny_paths: list[str] = Field(default_factory=list)
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
```

Web과 Source에서 사용하지 않는 필드는 빈 리스트로 둘 수 있다.

---

## 7. Credentials

테스트 계정 참조용 최소 구조다.

필드:

```text
username
password_ref
```

권장 타입:

```python
username: str
password_ref: str
```

주의:

```text
Raw Password 저장 금지
실제 Secret 값 저장 금지
```

`password_ref`는 런타임 Secret Reference를 표현한다.

---

## 8. AssessmentRequest

필수 필드:

```text
assessment_type
scope
```

Web 전용 필드:

```text
target_url
authorization_confirmed
credentials
```

Source 전용 필드:

```text
source_directory
```

권장 구조:

```python
class AssessmentRequest(BaseModel):
    assessment_type: AssessmentType
    target_url: str | None = None
    source_directory: str | None = None
    scope: AssessmentScope = Field(default_factory=AssessmentScope)
    authorization_confirmed: bool = False
    credentials: Credentials | None = None
```

---

## 9. AssessmentRequest Validation 규칙

Assessment Type에 따라 최소 입력 조건을 검증한다.

### WEB

반드시 필요:

```text
target_url
```

그리고 Active Assessment 허용 전 단계의 사용자 확인용으로:

```text
authorization_confirmed
```

필드를 보존한다.

이번 Model 단계에서는 외부 URL Allowlist 정책을 판정하지 않는다.
그 정책은 Safety Gate Task에서 처리한다.

### SOURCE

반드시 필요:

```text
source_directory
```

### 금지

WEB 요청에서 `source_directory`가 있다고 해서 에러로 만들 필요는 없다.
SOURCE 요청에서 `target_url`이 있다고 해서 반드시 에러로 만들 필요도 없다.

v0.1에서는 필요한 필드 존재 여부만 강제한다.

---

## 10. 권장 AssessmentRequest Validator

가능하면 단일 `model_validator`로 구현한다.

예상 논리:

```text
if assessment_type == WEB:
    target_url 필요

if assessment_type == SOURCE:
    source_directory 필요
```

검증 실패 시 명확한 메시지를 반환한다.

예:

```text
target_url is required for WEB assessment
source_directory is required for SOURCE assessment
```

---

## 11. AssessmentRun

Assessment 실행 상태를 관리한다.

필드:

```text
assessment_id
assessment_type
status
started_at
finished_at
request
errors
```

권장 타입:

```python
assessment_id: str
assessment_type: AssessmentType
status: AssessmentStatus
started_at: datetime
finished_at: datetime | None = None
request: AssessmentRequest
errors: list[AssessmentError] = Field(default_factory=list)
```

단, `AssessmentError`의 forward reference 문제가 생기면
정의 순서를 조정한다.

---

## 12. AssessmentRun 기본값

권장:

```text
status = CREATED
finished_at = None
errors = []
```

`started_at`은 자동 기본값을 줄 수 있다.

예:

```python
Field(default_factory=lambda: datetime.now(timezone.utc))
```

UTC를 사용한다.

---

## 13. ValidationResult

Safety / Scope Validation 결과다.

필드:

```text
allowed
reason
active_assessment_allowed
validated_scope
```

권장 타입:

```python
allowed: bool
reason: str
active_assessment_allowed: bool
validated_scope: AssessmentScope | None = None
```

---

## 14. AssessmentError

필드:

```text
error_id
phase
code
message
retryable
tool_name
test_id
```

권장 타입:

```python
error_id: str
phase: str
code: str
message: str
retryable: bool
tool_name: str | None = None
test_id: str | None = None
```

이번 Task에서는 `phase`를 별도 Enum으로 만들지 않는다.

향후 필요 시 별도 결정한다.

---

## 15. AssessmentResult

최종 Assessment 요약 모델이다.

필드:

```text
schema_version
assessment_id
assessment_type
status
target
started_at
finished_at
tests_planned
tests_executed
findings
manual_review_required
errors
report_paths
```

---

## 16. AssessmentResult 타입

권장:

```python
schema_version: str = "0.1"
assessment_id: str
assessment_type: AssessmentType
status: AssessmentStatus
target: str
started_at: datetime
finished_at: datetime | None = None
tests_planned: int = 0
tests_executed: int = 0
findings: list[str] = Field(default_factory=list)
manual_review_required: list[str] = Field(default_factory=list)
errors: list[AssessmentError] = Field(default_factory=list)
report_paths: dict[str, str] = Field(default_factory=dict)
```

---

## 17. Numeric Validation

다음 값은 음수가 될 수 없다.

```text
tests_planned
tests_executed
```

Pydantic `Field(ge=0)` 사용을 권장한다.

예:

```python
tests_planned: int = Field(default=0, ge=0)
tests_executed: int = Field(default=0, ge=0)
```

---

## 18. Timestamp 원칙

`datetime` 객체를 사용한다.

저장 및 JSON 직렬화 시 ISO 8601 형태를 사용한다.

UTC를 권장한다.

예:

```text
2026-10-02T12:00:00Z
```

이번 Task에서는 별도 시간 유틸리티 모듈을 만들지 않는다.

---

## 19. Mutable Default 금지

다음 방식은 사용하지 않는다.

잘못된 예:

```python
errors: list[AssessmentError] = []
findings: list[str] = []
```

대신:

```python
Field(default_factory=list)
```

를 사용한다.

---

## 20. Extra Field 정책

v0.1에서는 예상치 못한 필드가 조용히 섞이는 것을 막기 위해
가능하면 다음 설정을 검토한다.

```python
model_config = ConfigDict(extra="forbid")
```

Assessment 관련 모델 전체에 적용할 수 있다.

단, 구현 복잡도가 커지지 않는 범위에서 적용한다.

---

## 21. 구현 대상 파일

생성:

```text
secureprobe/models/assessment.py
tests/unit/test_assessment_models.py
docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

수정 가능:

```text
secureprobe/models/__init__.py
```

---

## 22. 구현 금지 모델

이번 Task에서는 다음을 구현하지 않는다.

```text
WebTargetContext
SourceTargetContext
Endpoint
Form
CookieInfo
SourceFileRef

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

GroundTruthFinding
BenchmarkFinding
EvaluationRecord
EvaluationSummary
```

---

## 23. Agent 기능 구현 금지

다음은 구현하지 않는다.

```text
Observer
Planner
Tool Selector
Executor
Analyzer
Verifier
Safety Gate
Tool Registry
Report Generator
```

---

## 24. Unit Test

다음 파일:

```text
tests/unit/test_assessment_models.py
```

최소 다음을 검증한다.

---

## 25. AssessmentScope Test

검증:

```text
기본 생성 성공
모든 list 기본값이 빈 리스트
입력값 저장 성공
```

---

## 26. Credentials Test

검증:

```text
username 저장
password_ref 저장
```

Raw Password 필드는 존재하지 않아야 한다.

가능하면:

```python
assert "password" not in Credentials.model_fields
```

형태로 확인한다.

---

## 27. AssessmentRequest WEB Test

정상 케이스:

```text
assessment_type = WEB
target_url 존재
```

생성 성공.

실패 케이스:

```text
assessment_type = WEB
target_url 없음
```

ValidationError 발생.

---

## 28. AssessmentRequest SOURCE Test

정상 케이스:

```text
assessment_type = SOURCE
source_directory 존재
```

생성 성공.

실패 케이스:

```text
assessment_type = SOURCE
source_directory 없음
```

ValidationError 발생.

---

## 29. Authorization Field Test

WEB Request에서:

```text
authorization_confirmed
```

값이 정상 저장되는지 확인한다.

이번 Task에서는 `False`라고 해서 Model Validation 실패로 만들지 않는다.

실제 허용/차단은 Safety Gate에서 판단한다.

---

## 30. AssessmentRun Test

검증:

```text
기본 status = CREATED
finished_at = None
errors = []
assessment_type 저장
request 저장
```

---

## 31. ValidationResult Test

검증:

```text
allowed True/False 저장
active_assessment_allowed 저장
validated_scope optional
```

---

## 32. AssessmentError Test

검증:

```text
필수 필드 저장
tool_name optional
test_id optional
retryable 저장
```

---

## 33. AssessmentResult Test

검증:

```text
schema_version 기본값 "0.1"
tests_planned 기본값 0
tests_executed 기본값 0
findings 기본 빈 리스트
manual_review_required 기본 빈 리스트
errors 기본 빈 리스트
report_paths 기본 빈 dict
```

---

## 34. Negative Count Test

다음은 ValidationError여야 한다.

```text
tests_planned = -1
tests_executed = -1
```

---

## 35. Mutable Default Isolation Test

서로 다른 Model Instance 간 list/dict 기본값이 공유되지 않는지 확인한다.

예:

```text
result_a.findings.append(...)
result_b.findings는 비어 있어야 함
```

---

## 36. Extra Field Test

`extra="forbid"`를 적용한 경우
정의되지 않은 필드 입력 시 ValidationError를 확인한다.

적용하지 않았다면 이 테스트는 생략 가능하지만,
결과 문서에 정책을 기록한다.

---

## 37. JSON Serialization Test

최소 하나의 Model에 대해 JSON 직렬화가 성공해야 한다.

예:

```python
payload = request.model_dump(mode="json")
```

Enum과 datetime이 JSON 친화적으로 변환되는지 확인한다.

---

## 38. Import Test

다음 import가 성공해야 한다.

```bash
python -c "from secureprobe.models import AssessmentRequest, AssessmentRun, ValidationResult, AssessmentError, AssessmentResult; print('IMPORT_OK')"
```

---

## 39. 개별 Unit Test 실행

```bash
pytest tests/unit/test_assessment_models.py -q
```

PASS해야 한다.

---

## 40. 전체 회귀 테스트

```bash
pytest -q
```

기존 Smoke Test와 Enum Test를 포함한 전체 테스트가 PASS해야 한다.

실제 결과를 결과 문서에 기록한다.

---

## 41. 기존 Enum 회귀 확인

다음 테스트가 계속 PASS해야 한다.

```text
tests/unit/test_enums.py
```

Enum 구현을 변경하지 않는다.

---

## 42. Schema Consistency 확인

`DATA_SCHEMA_v0.1.md`에서 다음 섹션과 비교한다.

```text
AssessmentRequest
AssessmentScope
Credentials
AssessmentRun
ValidationResult
AssessmentError
AssessmentResult
```

필드명과 의미를 임의 변경하지 않는다.

---

## 43. 변경 가능한 파일

이번 Task 범위:

```text
secureprobe/models/assessment.py
secureprobe/models/__init__.py
tests/unit/test_assessment_models.py

docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

---

## 44. 수정 금지 파일

다음 파일은 수정하지 않는다.

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

## 45. 결과 문서

다음 파일을 반드시 생성한다.

```text
docs/05_ai_development/codex_results/day02/
D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md
```

---

## 46. 결과 문서 필수 내용

```text
Task ID
Status
Implemented Models
Created Files
Modified Files
Validation Rules
Unit Test Result
Full Test Result
Import Validation
Schema Consistency
Extra Field Policy
Issues
Next Task
```

---

## 47. 결과 문서 예시

```text
# D02-T02 — Assessment Models Result v0.1

## Status

COMPLETED

## Implemented Models

- AssessmentScope
- Credentials
- AssessmentRequest
- AssessmentRun
- ValidationResult
- AssessmentError
- AssessmentResult

## Validation

WEB target_url required:
PASS

SOURCE source_directory required:
PASS

Negative counts rejected:
PASS

Mutable defaults isolated:
PASS

Import:
PASS

Unit Test:
PASS

Full pytest:
PASS

Schema Consistency:
PASS

## Issues

None

## Next Task

D02-T03 — Agent Model 구현
```

---

## 48. 완료 체크리스트

```text
[ ] assessment.py 생성
[ ] AssessmentScope 구현
[ ] Credentials 구현
[ ] AssessmentRequest 구현
[ ] AssessmentRun 구현
[ ] ValidationResult 구현
[ ] AssessmentError 구현
[ ] AssessmentResult 구현

[ ] WEB target_url 검증
[ ] SOURCE source_directory 검증
[ ] Negative count 방지
[ ] Mutable Default 안전 처리
[ ] Enum 재사용
[ ] Raw Password 필드 없음

[ ] test_assessment_models.py 생성
[ ] 개별 Unit Test PASS
[ ] 전체 pytest PASS
[ ] Import PASS
[ ] DATA_SCHEMA 정합성 PASS

[ ] TestPlan 구현 없음
[ ] Finding 구현 없음
[ ] Evidence 구현 없음
[ ] Agent 기능 구현 없음

[ ] 결과 문서 생성
[ ] 결과 문서 파일명에 _RESULT_ 포함
```

---

## 49. 완료 조건

다음 조건을 모두 만족하면 D02-T02 완료다.

```text
Assessment 관련 Model 구현
DATA_SCHEMA와 필드 의미 일치
Type별 필수 입력 검증
Unit Test PASS
전체 Regression Test PASS
범위 확대 없음
결과 문서 작성 완료
```

---

## 50. Git 검증

작업 전후:

```bash
git status
git diff
```

Commit 전에 변경 파일이 이번 Task 범위 내인지 확인한다.

---

## 51. 권장 Commit Message

```text
feat: add assessment domain models
```

결과 문서를 같은 Commit에 포함해도 된다.

---

## 52. 실패 처리

다음 경우 완료 처리하지 않는다.

```text
WEB Request가 target_url 없이 생성됨
SOURCE Request가 source_directory 없이 생성됨
음수 tests count 허용
Mutable Default 공유 발생
Enum 중복 정의
DATA_SCHEMA 필드 임의 변경
Unit Test 실패
전체 pytest 실패
범위 밖 Model 구현
```

상태:

```text
BLOCKED
또는
FAILED
```

로 기록한다.

---

## 53. 완료 보고 형식

```text
D02-T02 ASSESSMENT MODEL IMPLEMENTATION

Status:
COMPLETED / BLOCKED / FAILED

Implemented Models:
- AssessmentScope
- Credentials
- AssessmentRequest
- AssessmentRun
- ValidationResult
- AssessmentError
- AssessmentResult

Created Files:
-

Modified Files:
-

Validation:
- WEB Request Validation: PASS / FAIL
- SOURCE Request Validation: PASS / FAIL
- Negative Count Validation: PASS / FAIL
- Mutable Defaults: PASS / FAIL
- Import: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Schema Consistency: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day02/D02-T02_ASSESSMENT_MODELS_RESULT_v0.1.md

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

## 54. 작업 종료 원칙

D02-T02 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D02-T03 — Agent Model 구현
```
