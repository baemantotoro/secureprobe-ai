# D02-T01 — Common Enum Implementation v0.1

## 1. 목적

`DATA_SCHEMA_v0.1.md`에 정의된 SecureProbe AI 공통 Enum을 실제 Python 코드로 구현한다.

이번 Task의 목적은 이후 Assessment Model, Agent State, Tool Execution, Finding Model이 공통으로 사용할
상태값과 분류값을 단일 기준으로 고정하는 것이다.

구현 대상:

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

이번 Task에서는 Enum 외의 Pydantic Model이나 Agent 로직은 구현하지 않는다.

---

## 2. 작업 ID와 근거

- WBS 기준: Day 2, Task 01
- 작업 ID: `D02-T01`
- 작업명: 공통 Enum 구현
- 우선순위: P0
- 선행 작업: Day 1 완료
- 다음 작업: `D02-T02 — Assessment Model 구현`

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
secureprobe/models/enums.py
```

기존:

```text
secureprobe/models/__init__.py
```

는 필요한 경우 최소 수정하여 Enum을 export할 수 있다.

---

## 4. 구현 대상 Enum

### 4.1 AssessmentType

정의값:

```text
WEB
SOURCE
```

예상 형태:

```python
from enum import Enum


class AssessmentType(str, Enum):
    WEB = "WEB"
    SOURCE = "SOURCE"
```

---

### 4.2 AssessmentStatus

정의값:

```text
CREATED
VALIDATING
OBSERVING
PLANNING
SELECTING_TOOL
EXECUTING
ANALYZING
VERIFYING
REPORTING
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
BLOCKED
```

주의:

`AGENT_FLOW_v0.1.md`와 `DATA_SCHEMA_v0.1.md`의 상태값을 모두 반영한다.

---

### 4.3 RiskLevel

정의값:

```text
PASSIVE
ACTIVE
```

---

### 4.4 ExecutionStatus

정의값:

```text
SUCCESS
FAILED
TIMEOUT
BLOCKED
UNSUPPORTED
```

---

### 4.5 ValidationStatus

정의값:

```text
UNVERIFIED
TOOL_VERIFIED
MANUAL_REQUIRED
MANUAL_VERIFIED
REJECTED
```

---

### 4.6 Severity

정의값:

```text
INFO
LOW
MEDIUM
HIGH
CRITICAL
```

---

## 5. 구현 원칙

모든 Enum은 가능하면 다음 형태를 사용한다.

```python
class ExampleEnum(str, Enum):
    VALUE = "VALUE"
```

이유:

```text
JSON 직렬화 편의
Pydantic 호환성
Structured Output 사용
문서 정의값과 문자열 일치
```

Enum 값은 소문자로 변경하지 않는다.

예:

```text
WEB → 유지
PASSIVE → 유지
TOOL_VERIFIED → 유지
```

---

## 6. 문자열 값 변경 금지

다음과 같이 문서에 정의된 문자열을 임의 변경하지 않는다.

잘못된 예:

```text
"web"
"source"
"tool-verified"
"manual required"
```

정확한 정의값을 사용한다.

---

## 7. Enum 중복 정의 금지

다른 파일에 동일 Enum을 별도로 만들지 않는다.

모든 공통 Enum은 다음 한 파일을 기준으로 한다.

```text
secureprobe/models/enums.py
```

향후 다른 Model은 이 파일에서 import한다.

---

## 8. `__init__.py` export

필요하면 다음 Enum을 export한다.

예:

```python
from .enums import (
    AssessmentStatus,
    AssessmentType,
    ExecutionStatus,
    RiskLevel,
    Severity,
    ValidationStatus,
)
```

그리고 필요 시:

```python
__all__ = [
    "AssessmentType",
    "AssessmentStatus",
    "RiskLevel",
    "ExecutionStatus",
    "ValidationStatus",
    "Severity",
]
```

단, 현재 프로젝트 스타일이 단순 import를 선호하면 `__all__`은 필수가 아니다.

---

## 9. Pydantic Model 구현 금지

이번 Task에서는 다음 객체를 구현하지 않는다.

```text
AssessmentRequest
AssessmentRun
ValidationResult
AssessmentError
AssessmentResult
TestPlan
TestCase
Finding
Evidence
ToolDefinition
ToolSelection
ToolExecution
```

이들은 이후 Task에서 구현한다.

---

## 10. Agent 구현 금지

다음 파일은 생성하지 않는다.

```text
secureprobe/agent/observer.py
secureprobe/agent/planner.py
secureprobe/agent/selector.py
secureprobe/agent/executor.py
secureprobe/agent/analyzer.py
secureprobe/agent/verifier.py
```

---

## 11. Web / Source 기능 구현 금지

다음 기능은 이번 Task 범위가 아니다.

```text
Web Observer
Source Observer
HTTP Tool
Source Tool
Safety Gate
Tool Registry
OpenAI API
Report Generator
```

---

## 12. Unit Test 파일

다음 파일을 생성한다.

```text
tests/unit/test_enums.py
```

---

## 13. Unit Test 요구사항

최소 다음을 검증한다.

### AssessmentType

```text
WEB 존재
SOURCE 존재
문자열 값 일치
```

### AssessmentStatus

모든 정의값 존재 확인.

### RiskLevel

```text
PASSIVE
ACTIVE
```

### ExecutionStatus

모든 정의값 존재 확인.

### ValidationStatus

모든 정의값 존재 확인.

### Severity

모든 정의값 존재 확인.

---

## 14. 문자열 호환성 테스트

각 Enum이 `str` 기반인지 확인한다.

예:

```python
assert AssessmentType.WEB.value == "WEB"
assert str(AssessmentType.WEB.value) == "WEB"
```

필요하면:

```python
assert isinstance(AssessmentType.WEB, str)
```

도 검증한다.

---

## 15. Enum 값 집합 테스트

가능하면 각 Enum의 실제 값 집합을 정확히 검증한다.

예:

```python
assert {item.value for item in RiskLevel} == {
    "PASSIVE",
    "ACTIVE",
}
```

이 방식으로 누락/추가 값을 탐지한다.

---

## 16. Schema 기준 검증

`DATA_SCHEMA_v0.1.md`의 정의와 테스트 코드가 일치해야 한다.

특히 다음 항목을 비교한다.

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

문서와 코드가 불일치하면 코드 임의 수정 전에 결과 보고서에 기록한다.

---

## 17. 회귀 테스트

기존 테스트 전체를 실행한다.

```bash
pytest -q
```

D01 Smoke Test 포함 전체 PASS해야 한다.

---

## 18. 개별 Unit Test 실행

다음 또는 동등한 명령을 실행한다.

```bash
pytest tests/unit/test_enums.py -q
```

PASS해야 한다.

---

## 19. Import 검증

다음 import가 성공해야 한다.

```bash
python -c "from secureprobe.models.enums import AssessmentType, AssessmentStatus, RiskLevel, ExecutionStatus, ValidationStatus, Severity; print('IMPORT_OK')"
```

---

## 20. 변경 가능한 파일

이번 Task에서 생성 또는 수정 가능한 파일:

```text
secureprobe/models/enums.py
secureprobe/models/__init__.py
tests/unit/test_enums.py
docs/05_ai_development/codex_results/day02/D02-T01_COMMON_ENUMS_RESULT_v0.1.md
```

필요한 경우 `day02/` 디렉터리를 생성한다.

---

## 21. 수정 금지 파일

다음 기준 문서는 수정하지 않는다.

```text
PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

설계 충돌을 발견하면 코드에서 조용히 보정하지 않는다.

결과 보고서에 문제를 기록한다.

---

## 22. 테스트 외 범위 확장 금지

이번 Task에서는 다음을 추가하지 않는다.

```text
pytest plugin
coverage tool
lint tool
mypy
ruff
pre-commit
```

필요성이 생기면 별도 Task에서 검토한다.

---

## 23. 결과 문서 경로

반드시 다음 파일을 생성한다.

```text
docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_RESULT_v0.1.md
```

이번 Task부터 결과 파일명은 `_RESULT_` 규칙을 유지한다.

---

## 24. 결과 문서 필수 내용

최소 다음을 기록한다.

```text
Task ID
Status
Implemented Enums
Created Files
Modified Files
Unit Test Result
Full Test Result
Import Validation
Schema Consistency
Issues
Next Task
```

---

## 25. 결과 문서 예시

```text
# D02-T01 — Common Enums Result v0.1

## Status

COMPLETED

## Implemented Enums

- AssessmentType
- AssessmentStatus
- RiskLevel
- ExecutionStatus
- ValidationStatus
- Severity

## Created Files

- secureprobe/models/enums.py
- tests/unit/test_enums.py

## Modified Files

- secureprobe/models/__init__.py

## Validation

Unit Test:
PASS

Full pytest:
PASS

Import:
PASS

Schema Consistency:
PASS

## Issues

None

## Next Task

D02-T02 — Assessment Model 구현
```

---

## 26. 완료 체크리스트

```text
[ ] enums.py 생성
[ ] AssessmentType 구현
[ ] AssessmentStatus 구현
[ ] RiskLevel 구현
[ ] ExecutionStatus 구현
[ ] ValidationStatus 구현
[ ] Severity 구현

[ ] 모든 값이 DATA_SCHEMA_v0.1과 일치
[ ] str 기반 Enum 사용

[ ] test_enums.py 생성
[ ] Enum 값 집합 테스트
[ ] 문자열 값 테스트
[ ] import 검증 PASS
[ ] 개별 Unit Test PASS
[ ] 전체 pytest PASS

[ ] Pydantic Model 구현 없음
[ ] Agent 기능 구현 없음
[ ] Web/Source 기능 구현 없음

[ ] 결과 문서 생성
[ ] 결과 문서 파일명에 _RESULT_ 포함
```

---

## 27. 완료 조건

다음 조건을 모두 만족하면 D02-T01을 완료 처리한다.

```text
공통 Enum 6종 구현
문서 정의값과 100% 일치
Unit Test PASS
전체 Regression Test PASS
기능 범위 확대 없음
결과 문서 작성 완료
```

---

## 28. Git 검증

작업 전후:

```bash
git status
git diff
```

Commit 전에 변경 범위가 이번 Task와 일치하는지 확인한다.

---

## 29. 권장 Commit Message

```text
feat: add common domain enums
```

결과 문서를 동일 Commit에 포함해도 된다.

---

## 30. 실패 처리

다음 경우 `COMPLETED`로 기록하지 않는다.

```text
Enum 값이 DATA_SCHEMA와 불일치
Unit Test 실패
전체 pytest 실패
기존 Smoke Test 실패
불필요한 Pydantic Model 구현
Agent 기능 추가
설계 문서 임의 수정
```

상태:

```text
BLOCKED
또는
FAILED
```

로 기록한다.

---

## 31. 완료 보고 형식

```text
D02-T01 COMMON ENUM IMPLEMENTATION

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- AssessmentType
- AssessmentStatus
- RiskLevel
- ExecutionStatus
- ValidationStatus
- Severity

Created Files:
-

Modified Files:
-

Validation:
- Import: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Schema Consistency: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day02/D02-T01_COMMON_ENUMS_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D02-T02 — Assessment Model 구현
```

---

## 32. 작업 종료 원칙

D02-T01 완료 후 다음 Task를 자동으로 시작하지 않는다.

다음 작업은 별도 지침으로 수행한다.

```text
D02-T02 — Assessment Model 구현
```
