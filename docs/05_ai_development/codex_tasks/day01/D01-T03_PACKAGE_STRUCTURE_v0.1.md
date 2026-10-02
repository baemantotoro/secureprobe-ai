# D01-T03 — SecureProbe Package Structure v0.1

## 1. 목적

SecureProbe AI의 기본 Python Package 구조를 생성한다.

이번 작업의 목적은 이후 Day 2의 Data Model, Agent Skeleton, Web/Source 기능 구현을 시작할 수 있도록
프로젝트 내부 디렉터리와 최소 Python Package 구조를 준비하는 것이다.

이번 Task에서는 실제 Agent 동작, Web Assessment, Source Assessment, Pydantic Model 구현은 하지 않는다.

핵심 목표:

```text
정해진 Architecture 기준의 Package 구조 생성
Python Package import 가능
불필요한 기능 코드 없음
기본 구조 검증 가능
```

---

## 2. 작업 ID와 근거

- WBS 기준: Day 1, Task 03
- 작업 ID: `D01-T03`
- 작업명: SecureProbe 기본 Package 구조 생성
- 우선순위: P0
- 선행 작업: `D01-T02` 완료
- 다음 작업: `D01-T04 — Test Skeleton 생성`

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
.venv 사용 가능
pytest 실행 가능
D01-T02 결과 문서 존재
```

D01-T02가 정상 완료되지 않았다면 이번 Task를 진행하지 않는다.

---

## 4. 목표 Package 구조

최종적으로 최소 다음 구조를 생성한다.

```text
secureprobe/
├── __init__.py
├── main.py
│
├── agent/
│   └── __init__.py
│
├── core/
│   └── __init__.py
│
├── web/
│   ├── __init__.py
│   └── tools/
│       └── __init__.py
│
├── source/
│   ├── __init__.py
│   └── tools/
│       └── __init__.py
│
├── models/
│   └── __init__.py
│
└── report/
    └── __init__.py
```

현재 `secureprobe/README.md`가 존재하면 유지한다.

---

## 5. Architecture와의 대응

각 Package의 역할은 다음과 같다.

### `secureprobe/agent/`

향후 구현 예정:

```text
observer.py
planner.py
selector.py
executor.py
analyzer.py
verifier.py
```

이번 Task에서는 생성하지 않는다.

### `secureprobe/core/`

향후 구현 예정:

```text
config.py
safety.py
registry.py
```

이번 Task에서는 생성하지 않는다.

### `secureprobe/web/`

Web Assessment 전용 모듈 영역이다.

향후:

```text
observer.py
tools/
```

를 구현한다.

이번 Task에서는 기능 파일을 만들지 않는다.

### `secureprobe/source/`

Source Assessment 전용 모듈 영역이다.

향후:

```text
observer.py
tools/
```

를 구현한다.

이번 Task에서는 기능 파일을 만들지 않는다.

### `secureprobe/models/`

DATA_SCHEMA_v0.1의 Pydantic Model을 구현할 영역이다.

이번 Task에서는 Model을 만들지 않는다.

### `secureprobe/report/`

JSON/Markdown Report Generator 구현 영역이다.

이번 Task에서는 Generator를 만들지 않는다.

---

## 6. `__init__.py` 원칙

각 Python Package에 최소한의 `__init__.py`를 생성한다.

기본적으로 빈 파일 또는 최소 Docstring만 사용한다.

예:

```python
"""SecureProbe AI package."""
```

불필요한 import side effect를 만들지 않는다.

예를 들어 다음과 같은 동작은 넣지 않는다.

```text
자동 Tool 등록
OpenAI Client 생성
HTTP 연결
환경변수 로딩
파일 접근
```

---

## 7. `main.py` 목적

`secureprobe/main.py`는 이번 단계에서 실제 Agent 실행을 하지 않는다.

최소한 Package Import 확인용 Entry Point 수준으로만 둔다.

예시:

```python
def main() -> None:
    """SecureProbe AI entry point placeholder."""
    print("SecureProbe AI")


if __name__ == "__main__":
    main()
```

동등한 최소 구현을 사용할 수 있다.

---

## 8. `main.py` 제한사항

다음은 구현하지 않는다.

```text
OpenAI API 호출
Agent Loop
HTTP Request
Source Scan
Tool Registry
Config Loading
Safety Gate
Finding 생성
Report 생성
```

이번 Task의 목적은 Package 구조와 Import 가능성 확인뿐이다.

---

## 9. 생성 대상

생성 가능한 파일:

```text
secureprobe/__init__.py
secureprobe/main.py

secureprobe/agent/__init__.py

secureprobe/core/__init__.py

secureprobe/web/__init__.py
secureprobe/web/tools/__init__.py

secureprobe/source/__init__.py
secureprobe/source/tools/__init__.py

secureprobe/models/__init__.py

secureprobe/report/__init__.py
```

---

## 10. 수정 가능한 기존 파일

필요한 경우 최소 수정만 허용한다.

```text
secureprobe/README.md
.gitignore
```

단, 이번 작업을 위해 수정할 필요가 없으면 변경하지 않는다.

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

설계 변경이 필요해 보이더라도 이번 Task에서 직접 변경하지 않는다.

문제만 결과 보고서에 기록한다.

---

## 12. 기능 구현 금지

이번 Task에서는 다음을 구현하지 않는다.

```text
Pydantic Models
AssessmentRequest
AssessmentRun
TestPlan
Finding
Evidence

Observer
Planner
Tool Selector
Executor
Analyzer
Verifier

Safety Gate
Tool Registry

Web Tools
Source Tools

Report Generator

OpenAI API
ZAP
Semgrep
SecureBoard
Ground Truth
```

---

## 13. Package Import 검증

구조 생성 후 최소 다음 Import가 성공해야 한다.

```bash
python -c "import secureprobe"
```

다음도 성공해야 한다.

```bash
python -c "import secureprobe.agent; import secureprobe.core; import secureprobe.web; import secureprobe.source; import secureprobe.models; import secureprobe.report; print('IMPORT_OK')"
```

---

## 14. Entry Point 검증

다음 또는 동등한 방법으로 실행한다.

```bash
python -m secureprobe.main
```

실패 없이 종료되어야 한다.

출력 내용 자체는 중요하지 않다.

---

## 15. Import Side Effect 검증

단순 Package Import 시 다음이 발생하면 안 된다.

```text
외부 HTTP 요청
OpenAI API 요청
파일 생성
DB 연결
환경변수 필수 요구
보안진단 실행
```

---

## 16. 테스트 코드 생성 여부

이번 Task에서는 새로운 Unit Test 파일을 생성하지 않는다.

D01-T04에서 Test Skeleton을 별도로 생성한다.

다만 기존 `tests/test_python_env_smoke.py`가 있다면 실행해 회귀 여부를 확인한다.

---

## 17. 회귀 검증

기존 환경 테스트가 존재하면 실행한다.

예:

```bash
pytest tests/test_python_env_smoke.py -q
```

성공해야 한다.

---

## 18. 디렉터리 구조 검증

가능한 경우 다음 또는 동등한 명령으로 구조를 확인한다.

Windows:

```powershell
tree secureprobe /F
```

Linux/macOS:

```bash
find secureprobe -maxdepth 3 -type f
```

---

## 19. 결과 문서

작업 결과를 반드시 다음 경로에 작성한다.

```text
docs/05_ai_development/codex_results/day01/
D01-T03_PACKAGE_STRUCTURE_RESULT_v0.1.md
```

이번 Task부터 결과 파일명은 반드시 `_RESULT_` 규칙을 사용한다.

---

## 20. 결과 문서 필수 내용

최소 다음을 포함한다.

```text
Task ID
Status
Created Directories
Created Files
Modified Files
Import Validation
Entry Point Validation
Regression Test
Scope Check
Issues
Next Task
```

---

## 21. 결과 문서 예시

```text
# D01-T03 — Package Structure Result v0.1

## Status

COMPLETED

## Created Directories

- secureprobe/agent/
- secureprobe/core/
- secureprobe/web/tools/
- secureprobe/source/tools/
- secureprobe/models/
- secureprobe/report/

## Created Files

- secureprobe/__init__.py
- secureprobe/main.py
...

## Import Validation

PASS

## Entry Point Validation

PASS

## Regression Test

PASS

## Scope Check

기능 구현 없음.

## Issues

None

## Next Task

D01-T04 — Test Skeleton 생성
```

---

## 22. 검증 체크리스트

```text
[ ] secureprobe/__init__.py 존재
[ ] secureprobe/main.py 존재

[ ] secureprobe/agent/__init__.py 존재
[ ] secureprobe/core/__init__.py 존재

[ ] secureprobe/web/__init__.py 존재
[ ] secureprobe/web/tools/__init__.py 존재

[ ] secureprobe/source/__init__.py 존재
[ ] secureprobe/source/tools/__init__.py 존재

[ ] secureprobe/models/__init__.py 존재
[ ] secureprobe/report/__init__.py 존재

[ ] import secureprobe 성공
[ ] 하위 Package import 성공
[ ] python -m secureprobe.main 성공
[ ] 기존 Python 환경 smoke test PASS
[ ] 기능 구현 없음
[ ] 기준 문서 변경 없음
[ ] 결과 문서 작성
```

---

## 23. 완료 조건

다음 조건을 모두 만족하면 완료다.

```text
Package 구조가 Architecture와 일치
모든 Package Import 성공
Entry Point 실행 성공
기존 D01-T02 환경 검증 유지
Agent/Web/Source 기능 구현 없음
Pydantic Model 구현 없음
결과 문서 생성
Git diff 검토 완료
```

---

## 24. Git 검증

작업 전후:

```bash
git status
git diff
```

Commit 전에 변경 파일이 이번 Task 범위 내인지 확인한다.

기준 문서가 수정되어 있으면 원인을 확인하고 되돌린다.

---

## 25. 권장 Commit Message

```text
chore: add secureprobe package structure
```

결과 문서를 별도 Commit으로 분리할 필요는 없다.

한 Task의 코드/구조 및 결과 문서는 하나의 Commit으로 관리해도 된다.

---

## 26. 금지 작업

```text
git commit --amend
git push --force
```

불필요한 Git History 재작성은 하지 않는다.

---

## 27. 실패 처리

다음 경우 COMPLETED로 기록하지 않는다.

```text
Package Import 실패
Entry Point 실행 실패
설계와 다른 Package 구조 생성
Agent 기능 코드 추가
Web/Source 기능 코드 추가
기준 문서 임의 변경
```

상태:

```text
BLOCKED
또는
FAILED
```

로 기록한다.

---

## 28. 완료 보고 형식

```text
D01-T03 SECUREPROBE PACKAGE STRUCTURE

Status:
COMPLETED / BLOCKED / FAILED

Created Directories:
-

Created Files:
-

Modified Files:
-

Validation:
- Package Import: PASS / FAIL
- Subpackage Import: PASS / FAIL
- Entry Point: PASS / FAIL
- Environment Regression: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day01/D01-T03_PACKAGE_STRUCTURE_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D01-T04 — Test Skeleton 생성
```

---

## 29. 작업 종료 원칙

이번 Task 완료 후 다음 Task를 자동으로 시작하지 않는다.

다음 작업은 별도 지침으로 수행한다.

```text
D01-T04 — Test Skeleton 생성
```
