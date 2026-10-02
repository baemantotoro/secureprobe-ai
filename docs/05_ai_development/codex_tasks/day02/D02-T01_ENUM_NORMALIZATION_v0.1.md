# D02-T01 — Enum Test Hardening and Result Normalization v0.1

## 1. 목적

D02-T01 공통 Enum 구현은 완료되었으나, 다음 세 가지가 작업 지침과 불일치한다.

1. Unit Test 파일이 `tests/unit/`이 아닌 `tests/` 루트에 존재
2. 일부 대표 Enum 값만 검증하고 전체 값 집합을 검증하지 않음
3. 결과 문서 파일명에 `_RESULT_` 규칙이 적용되지 않음

이번 작업의 목적은 구현된 Enum 코드는 유지하면서 테스트 구조와 결과 문서를 정규화하여
D02-T01을 최종 완료 상태로 닫는 것이다.

---

## 2. 작업 대상

현재 Unit Test:

```text
tests/test_common_enums.py
```

변경 후:

```text
tests/unit/test_enums.py
```

현재 결과 문서:

```text
docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_v0.1.md
```

변경 후:

```text
docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_RESULT_v0.1.md
```

---

## 3. Enum 구현 파일은 수정 금지

다음 파일은 이미 기준 문서와 일치하므로 이번 작업에서 수정하지 않는다.

```text
secureprobe/models/enums.py
```

현재 구현된 Enum:

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

Enum 값 자체를 추가, 삭제, rename하지 않는다.

---

## 4. Unit Test 파일 이동

다음 파일을 가능하면 Git 이력이 유지되도록 이동한다.

```text
tests/test_common_enums.py
→
tests/unit/test_enums.py
```

가능하면:

```bash
git mv tests/test_common_enums.py tests/unit/test_enums.py
```

또는 동등한 rename 방식을 사용한다.

기존 파일:

```text
tests/test_common_enums.py
```

은 최종적으로 존재하지 않아야 한다.

---

## 5. 테스트 보강 원칙

대표값 몇 개만 확인하지 않고 각 Enum의 전체 값 집합을 정확하게 검증한다.

이를 통해 이후 Enum 값이 실수로 누락되거나 추가될 경우 Unit Test가 실패하도록 한다.

---

## 6. AssessmentType 전체 값 검증

정확한 값 집합:

```text
WEB
SOURCE
```

예:

```python
assert {item.value for item in AssessmentType} == {
    "WEB",
    "SOURCE",
}
```

---

## 7. AssessmentStatus 전체 값 검증

정확한 값 집합:

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

예:

```python
assert {item.value for item in AssessmentStatus} == {
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
    "BLOCKED",
}
```

---

## 8. RiskLevel 전체 값 검증

정확한 값 집합:

```text
PASSIVE
ACTIVE
```

---

## 9. ExecutionStatus 전체 값 검증

정확한 값 집합:

```text
SUCCESS
FAILED
TIMEOUT
BLOCKED
UNSUPPORTED
```

---

## 10. ValidationStatus 전체 값 검증

정확한 값 집합:

```text
UNVERIFIED
TOOL_VERIFIED
MANUAL_REQUIRED
MANUAL_VERIFIED
REJECTED
```

---

## 11. Severity 전체 값 검증

정확한 값 집합:

```text
INFO
LOW
MEDIUM
HIGH
CRITICAL
```

---

## 12. str 기반 Enum 검증

모든 Enum이 `str` 기반으로 구현되어 있음을 확인한다.

최소 다음 형태의 테스트를 포함한다.

예:

```python
assert isinstance(AssessmentType.WEB, str)
assert isinstance(AssessmentStatus.CREATED, str)
assert isinstance(RiskLevel.PASSIVE, str)
assert isinstance(ExecutionStatus.SUCCESS, str)
assert isinstance(ValidationStatus.UNVERIFIED, str)
assert isinstance(Severity.INFO, str)
```

또한 `.value`가 정확한 문자열인지 확인한다.

예:

```python
assert AssessmentType.WEB.value == "WEB"
assert Severity.CRITICAL.value == "CRITICAL"
```

---

## 13. 권장 테스트 구조

`tests/unit/test_enums.py`는 최소 다음 성격의 테스트를 포함한다.

```text
test_assessment_type_values
test_assessment_status_values
test_risk_level_values
test_execution_status_values
test_validation_status_values
test_severity_values
test_enums_are_string_compatible
```

함수 이름은 동등한 의미라면 달라도 된다.

---

## 14. DATA_SCHEMA 정합성

다음 기준 문서의 Enum 정의와 테스트가 정확히 일치하는지 확인한다.

```text
docs/02_spec/DATA_SCHEMA_v0.1.md
```

다음 6개를 비교한다.

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

불일치를 발견하면 임의로 코드나 기준 문서를 변경하지 않는다.

결과 문서에 이슈로 기록하고 작업을 `BLOCKED` 처리한다.

---

## 15. 결과 문서 Rename

현재:

```text
docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_v0.1.md
```

변경:

```text
docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_RESULT_v0.1.md
```

가능하면:

```bash
git mv
```

또는 동등한 rename 방식을 사용한다.

기존 이름의 결과 문서는 최종적으로 존재하지 않아야 한다.

---

## 16. 결과 문서 상태

결과 문서의 상태는 다음을 유지한다.

```text
Status: COMPLETED
```

테스트 보강 후 실제 테스트 결과를 갱신한다.

---

## 17. 결과 문서에 추가할 검증 정보

최소 다음 항목을 확인 또는 추가한다.

```text
Unit Test Location:
tests/unit/test_enums.py

Enum Full-set Validation:
PASS

String Enum Validation:
PASS

Schema Consistency:
PASS

Full pytest:
PASS
```

실제 테스트 수는 pytest 실행 결과를 기준으로 기록한다.

임의 숫자를 작성하지 않는다.

---

## 18. 전체 회귀 테스트

수정 후 다음을 실행한다.

개별 Unit Test:

```bash
pytest tests/unit/test_enums.py -q
```

전체 테스트:

```bash
pytest -q
```

둘 다 PASS해야 한다.

---

## 19. 기존 Smoke Test 회귀 확인

전체 pytest 실행으로 다음 기존 테스트가 함께 PASS하는지 확인한다.

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py
```

기존 Smoke Test를 수정하지 않는다.

---

## 20. 변경 가능한 파일

이번 작업에서 변경 가능한 파일은 다음으로 제한한다.

```text
tests/test_common_enums.py
tests/unit/test_enums.py

docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_v0.1.md

docs/05_ai_development/codex_results/day02/
D02-T01_COMMON_ENUMS_RESULT_v0.1.md
```

Git rename 과정에 따른 삭제/생성은 허용한다.

---

## 21. 수정 금지 파일

다음 파일은 변경하지 않는다.

```text
secureprobe/models/enums.py
secureprobe/models/__init__.py

requirements.txt
.gitignore

PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

---

## 22. 기능 범위 확장 금지

이번 작업에서는 다음을 구현하지 않는다.

```text
Pydantic Model
Assessment Model
Agent State Logic
Observer
Planner
Tool Registry
Safety Gate
Web Tool
Source Tool
OpenAI API
Report Generator
```

---

## 23. Git 검증

작업 전후 다음을 확인한다.

```bash
git status
git diff --stat
git diff --summary
```

확인 항목:

```text
test_common_enums.py → unit/test_enums.py rename 여부
COMMON_ENUMS_v0.1.md → COMMON_ENUMS_RESULT_v0.1.md rename 여부
Enum 구현 파일 변경 없음
설계 문서 변경 없음
```

---

## 24. 완료 체크리스트

```text
[ ] tests/test_common_enums.py 제거
[ ] tests/unit/test_enums.py 존재

[ ] AssessmentType 전체값 검증
[ ] AssessmentStatus 전체값 검증
[ ] RiskLevel 전체값 검증
[ ] ExecutionStatus 전체값 검증
[ ] ValidationStatus 전체값 검증
[ ] Severity 전체값 검증

[ ] str 기반 Enum 검증
[ ] DATA_SCHEMA 정합성 PASS

[ ] D02-T01_COMMON_ENUMS_v0.1.md 제거
[ ] D02-T01_COMMON_ENUMS_RESULT_v0.1.md 존재

[ ] 개별 Enum Unit Test PASS
[ ] 전체 pytest PASS
[ ] 기존 Smoke Test PASS

[ ] Enum 구현 코드 변경 없음
[ ] 기능 범위 확대 없음
```

---

## 25. 완료 조건

다음 조건을 모두 만족하면 D02-T01을 최종 완료 상태로 닫는다.

```text
Unit Test 위치 규칙 준수
전체 Enum 값 집합 검증
str 기반 Enum 검증
DATA_SCHEMA와 코드 정합성 검증
결과 파일명 _RESULT_ 규칙 준수
전체 테스트 PASS
Enum 구현 코드 변경 없음
```

---

## 26. 권장 Commit Message

```text
test: harden enum validation and normalize result
```

다음은 사용하지 않는다.

```text
git commit --amend
git push --force
```

---

## 27. 완료 보고 형식

```text
D02-T01 ENUM NORMALIZATION

Status:
COMPLETED / BLOCKED / FAILED

Renamed Test:
tests/test_common_enums.py
→
tests/unit/test_enums.py

Renamed Result:
D02-T01_COMMON_ENUMS_v0.1.md
→
D02-T01_COMMON_ENUMS_RESULT_v0.1.md

Validation:
- Full Enum Sets: PASS / FAIL
- String Enum: PASS / FAIL
- Schema Consistency: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Code Change Check: PASS / FAIL

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

## 28. 작업 종료 원칙

이번 작업이 완료되면 D02-T01을 종료한다.

다음 작업을 자동 시작하지 않는다.

다음 Task:

```text
D02-T02 — Assessment Model 구현
```
