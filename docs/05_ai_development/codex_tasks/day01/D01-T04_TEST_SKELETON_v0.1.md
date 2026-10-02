# D01-T04 — Test Skeleton Setup v0.1

## 1. 목적

SecureProbe AI 프로젝트의 테스트 디렉터리 구조와 최소 pytest 실행 골격을 정리한다.

이번 작업의 목적은 Day 2 이후 구현될 Data Model, Agent, Web/Source Tool, Report, Evaluation 기능에 대해
Unit Test와 Integration Test를 일관된 위치에 추가할 수 있도록 테스트 기반 구조를 준비하는 것이다.

현재 이미 존재하는 Smoke Test는 유지한다.

기존 확인 대상:

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py
```

이번 Task에서는 실제 Agent 기능이나 보안진단 기능에 대한 테스트를 작성하지 않는다.

---

## 2. 작업 ID와 근거

- WBS 기준: Day 1, Task 04
- 작업 ID: `D01-T04`
- 작업명: Test Skeleton 생성
- 우선순위: P0
- 선행 작업: `D01-T03` 완료
- Day 1 마지막 Task
- 다음 작업: `D02-T01 — 공통 Enum 구현`

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. 선행 상태 확인

작업 시작 전에 다음을 확인한다.

```text
requirements.txt 존재
pytest 설치 완료
secureprobe Package import 가능
D01-T03 Package 구조 존재
기존 Smoke Test 실행 가능
```

최소 다음 테스트가 존재하는지 확인한다.

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py
```

기존 Smoke Test가 없다면 임의로 재작성하지 말고 결과 보고서에 기록한다.

---

## 4. 목표 테스트 구조

최종적으로 최소 다음 구조를 사용한다.

```text
tests/
├── README.md
├── test_python_env_smoke.py
├── test_package_structure_smoke.py
│
├── unit/
│   └── .gitkeep
│
├── integration/
│   └── .gitkeep
│
└── fixtures/
    └── .gitkeep
```

필요한 경우 프로젝트 루트에 다음 파일을 생성할 수 있다.

```text
pytest.ini
```

단, 실제 필요성이 있을 때만 생성한다.

---

## 5. 디렉터리 역할

### `tests/unit/`

작은 단위의 순수 로직 테스트를 저장한다.

향후 대상 예:

```text
Pydantic Model Validation
Safety Gate
Tool Registry
Tool Selector
Parser
Evaluation Formula
```

이번 Task에서는 실제 Unit Test를 추가하지 않는다.

---

### `tests/integration/`

여러 Component가 연결되는 테스트를 저장한다.

향후 대상 예:

```text
Web Observer
Web Agent
Source Observer
Source Agent
Report Generator
Evaluation
```

이번 Task에서는 실제 Integration Test를 추가하지 않는다.

---

### `tests/fixtures/`

테스트용 입력 데이터와 고정 샘플을 저장한다.

향후 예:

```text
Sample HTML
Sample HTTP Response
Sample Source File
Mock LLM Response
Sample Evidence JSON
Sample Finding JSON
```

이번 Task에서는 실제 보안 Payload나 취약점 Fixture를 추가하지 않는다.

---

## 6. 기존 Smoke Test 유지 원칙

다음 파일은 삭제하거나 이동하지 않는다.

```text
tests/test_python_env_smoke.py
tests/test_package_structure_smoke.py
```

현재 위치를 그대로 유지한다.

이번 Task에서는 내용 변경도 원칙적으로 하지 않는다.

변경이 꼭 필요하면 최소 수정만 허용하며,
변경 이유를 결과 보고서에 기록한다.

---

## 7. `tests/README.md`

다음 목적의 간단한 README를 생성한다.

최소 포함 내용:

```text
테스트 디렉터리 목적
unit / integration / fixtures 역할
기존 Smoke Test 위치
pytest 실행 방법
새 테스트 추가 규칙
```

예시 실행 명령:

```bash
pytest -q
```

특정 Smoke Test:

```bash
pytest tests/test_python_env_smoke.py -q
pytest tests/test_package_structure_smoke.py -q
```

---

## 8. pytest 설정

현재 기본 `pytest` 실행이 정상이라면 별도 설정 파일을 만들지 않아도 된다.

다음 조건 중 하나가 필요할 때만 `pytest.ini`를 생성한다.

```text
testpaths 명시가 필요
향후 marker 사용 기준을 문서화할 필요
테스트 탐색이 현재 환경에서 불안정
```

필요 시 최소 설정 예:

```ini
[pytest]
testpaths = tests
```

불필요한 marker, plugin, coverage 설정은 이번 Task에 추가하지 않는다.

---

## 9. 생성 대상

기본 생성 대상:

```text
tests/README.md
tests/unit/.gitkeep
tests/integration/.gitkeep
tests/fixtures/.gitkeep
```

선택적 생성:

```text
pytest.ini
```

---

## 10. 수정 가능한 파일

필요 시 최소 수정 가능:

```text
.gitignore
tests/README.md
pytest.ini
```

기존 Smoke Test는 원칙적으로 수정하지 않는다.

---

## 11. 수정 금지 파일

다음 기준 문서는 수정하지 않는다.

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

SecureProbe 기능 코드도 수정하지 않는다.

```text
secureprobe/*
```

단, 테스트 실패 원인이 기존 Package Skeleton의 명백한 오타인 경우
임의 수정하지 말고 결과 보고서에 문제를 기록한다.

---

## 12. 기능 구현 금지

이번 Task에서는 다음을 구현하지 않는다.

```text
Pydantic Model
Agent State
Observer
Planner
Tool Selector
Executor
Analyzer
Verifier
Safety Gate
Tool Registry
Web Tool
Source Tool
Report Generator
Evaluation Engine
SecureBoard
Ground Truth
```

---

## 13. 보안 테스트 작성 금지

이번 단계에서는 실제 공격 Payload나 취약점 재현 테스트를 만들지 않는다.

예:

```text
SQL Injection Payload Test
XSS Payload Test
Path Traversal Test
File Upload Attack Test
IDOR Active Test
```

이런 테스트는 해당 기능 구현 Task에서
localhost / SecureBoard Lab 기준으로 별도 작성한다.

---

## 14. 테스트 이름 규칙

향후 테스트 파일은 다음 규칙을 권장한다.

Unit:

```text
tests/unit/test_<module_name>.py
```

Integration:

```text
tests/integration/test_<flow_name>.py
```

Fixture:

```text
tests/fixtures/<fixture_name>
```

Smoke Test는 현재 Root 위치를 유지한다.

---

## 15. 테스트 함수 이름 규칙

권장:

```python
def test_<expected_behavior>():
    ...
```

예:

```text
test_invalid_assessment_type_is_rejected
test_localhost_is_allowed
test_unknown_tool_is_rejected
```

이번 Task에서는 예시만 문서화하고 실제 기능 테스트를 만들지 않는다.

---

## 16. Fixture 원칙

향후 Fixture에는 실제 Secret이나 운영 데이터가 포함되어서는 안 된다.

금지:

```text
실제 Password
API Key
Session Token
Authorization Header
개인정보
운영 Source Code
```

Fixture는 자체 생성한 Dummy Data 또는 SecureBoard Lab 데이터만 사용한다.

---

## 17. Smoke Test 실행

현재 존재하는 두 Smoke Test를 각각 실행한다.

예:

```bash
pytest tests/test_python_env_smoke.py -q
pytest tests/test_package_structure_smoke.py -q
```

두 테스트 모두 PASS해야 한다.

---

## 18. 전체 pytest 실행

다음 명령을 실행한다.

```bash
pytest -q
```

현재 전체 테스트가 모두 PASS해야 한다.

새로 만든 `.gitkeep`과 README는 테스트 수에 영향을 주지 않는다.

---

## 19. 테스트 수 기록

실제 실행 결과에서 다음을 기록한다.

```text
Collected Tests
Passed
Failed
Skipped
Warnings
```

임의로 숫자를 작성하지 않는다.

실제 pytest 결과를 기준으로 기록한다.

---

## 20. 테스트 디렉터리 추적 확인

Git이 다음 디렉터리를 추적할 수 있어야 한다.

```text
tests/unit/
tests/integration/
tests/fixtures/
```

빈 디렉터리는 Git이 관리하지 않으므로 `.gitkeep`을 사용한다.

---

## 21. 결과 문서

작업 결과를 다음 경로에 생성한다.

```text
docs/05_ai_development/codex_results/day01/
D01-T04_TEST_SKELETON_RESULT_v0.1.md
```

이번 Task부터 결과 파일명에 `_RESULT_`를 반드시 포함한다.

---

## 22. 결과 문서 필수 항목

최소 다음을 기록한다.

```text
Task ID
Status
Created Directories
Created Files
Modified Files
Existing Smoke Tests
pytest Version
Smoke Test Result
Full Test Result
Collected / Passed / Failed / Skipped
Scope Check
Issues
Day 1 Completion Decision
Next Task
```

---

## 23. 결과 문서 예시

```text
# D01-T04 — Test Skeleton Result v0.1

## Status

COMPLETED

## Created Directories

- tests/unit/
- tests/integration/
- tests/fixtures/

## Created Files

- tests/README.md
- tests/unit/.gitkeep
- tests/integration/.gitkeep
- tests/fixtures/.gitkeep

## Existing Smoke Tests

- tests/test_python_env_smoke.py
- tests/test_package_structure_smoke.py

## Validation

Python Environment Smoke:
PASS

Package Structure Smoke:
PASS

Full pytest:
PASS

## Test Summary

Collected:
<actual>

Passed:
<actual>

Failed:
<actual>

Skipped:
<actual>

## Scope Check

기능 테스트 구현 없음.

## Day 1 Completion

READY / NOT READY

## Issues

None

## Next Task

D02-T01 — 공통 Enum 구현
```

---

## 24. Day 1 종료 검증

D01-T04 완료 후 Day 1 전체 상태를 확인한다.

Day 1 완료 항목:

```text
D01-T01 기준 문서 검증
D01-T02 Python 개발환경
D01-T03 SecureProbe Package 구조
D01-T04 Test Skeleton
```

모두 완료된 경우 결과 문서에:

```text
DAY 1 STATUS: COMPLETED
```

를 기록한다.

하나라도 실패했다면:

```text
DAY 1 STATUS: INCOMPLETE
```

로 기록하고 이유를 남긴다.

---

## 25. 완료 체크리스트

```text
[ ] tests/README.md 존재
[ ] tests/unit/.gitkeep 존재
[ ] tests/integration/.gitkeep 존재
[ ] tests/fixtures/.gitkeep 존재

[ ] 기존 test_python_env_smoke.py 유지
[ ] 기존 test_package_structure_smoke.py 유지

[ ] Python Environment Smoke PASS
[ ] Package Structure Smoke PASS
[ ] 전체 pytest PASS

[ ] SecureProbe 기능 코드 변경 없음
[ ] 기준 문서 변경 없음
[ ] 실제 보안 공격 테스트 추가 없음

[ ] 결과 문서 생성
[ ] 결과 문서 파일명에 _RESULT_ 포함
[ ] Day 1 완료 여부 기록
```

---

## 26. 완료 조건

다음 조건을 모두 만족하면 D01-T04를 완료 처리한다.

```text
테스트 디렉터리 Skeleton 생성
pytest 전체 실행 성공
기존 Smoke Test 유지 및 PASS
새 기능 테스트 구현 없음
기준 문서 변경 없음
결과 보고서 작성
Day 1 완료 여부 판정
```

---

## 27. Git 검증

작업 전후 확인:

```bash
git status
git diff
```

Commit 전 변경 파일이 이번 Task 범위에 한정되는지 확인한다.

예상 변경 범위:

```text
tests/
docs/05_ai_development/codex_results/day01/
pytest.ini  # 필요한 경우에만
```

---

## 28. 권장 Commit Message

```text
test: add test project skeleton
```

Task 결과 문서를 같은 Commit에 포함해도 된다.

---

## 29. 금지 작업

다음은 사용하지 않는다.

```text
git commit --amend
git push --force
```

Git History를 불필요하게 재작성하지 않는다.

---

## 30. 실패 처리

다음 중 하나라도 발생하면 `COMPLETED`로 기록하지 않는다.

```text
기존 Smoke Test 실패
전체 pytest 실패
SecureProbe 기능 코드 수정
기준 설계 문서 임의 수정
실제 공격용 Test 추가
테스트 Skeleton이 WBS와 불일치
```

상태는:

```text
BLOCKED
또는
FAILED
```

로 기록한다.

---

## 31. 완료 보고 형식

```text
D01-T04 TEST SKELETON

Status:
COMPLETED / BLOCKED / FAILED

Created Directories:
-

Created Files:
-

Modified Files:
-

Validation:
- Python Environment Smoke: PASS / FAIL
- Package Structure Smoke: PASS / FAIL
- Full pytest: PASS / FAIL
- Scope Check: PASS / FAIL

Test Summary:
- Collected:
- Passed:
- Failed:
- Skipped:

Result Document:
docs/05_ai_development/codex_results/day01/D01-T04_TEST_SKELETON_RESULT_v0.1.md

Day 1 Status:
COMPLETED / INCOMPLETE

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D02-T01 — 공통 Enum 구현
```

---

## 32. 작업 종료 원칙

D01-T04가 완료되면 Day 1을 종료한다.

다음 작업은 자동으로 시작하지 않는다.

Day 2 첫 작업은 별도 지침으로 수행한다.

```text
D02-T01 — 공통 Enum 구현
```
