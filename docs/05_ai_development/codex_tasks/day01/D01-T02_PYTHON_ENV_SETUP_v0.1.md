# D01-T02 — Python Environment Setup v0.1

## 1. 목적

SecureProbe AI 프로젝트의 Python 개발환경을 재현 가능하게 구성한다.

이 작업의 목적은 이후 Agent, Web Assessment, Source Assessment 구현을 시작하기 전에 다음 조건을 만족하는 안정적인 기본 개발환경을 확보하는 것이다.

- Python 버전 확인
- 가상환경 사용 가능
- 핵심 Python 의존성 설치 가능
- 의존성 목록이 파일로 관리됨
- `pytest` 실행 가능
- 프로젝트 코드 import가 가능한 최소 상태 확인

이번 작업에서는 기능 개발을 하지 않는다.

## 2. 작업 ID와 근거

- WBS 기준: Day 1, Task 02
- 작업 ID: `D01-T02`
- 작업명: Python 개발환경 구성
- 우선순위: P0
- 선행 작업: `D01-T01` 완료
- 다음 작업: `D01-T03 — SecureProbe 기본 Package 구조 생성`

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

## 3. 작업 범위

이번 Task에서 수행할 작업은 다음으로 제한한다.

```text
Python 버전 확인
가상환경 사용 방식 확정
의존성 관리 파일 작성
핵심 의존성 설치
pytest 실행 가능 여부 확인
기본 import 검증
환경 재현 절차 문서화
```

## 4. 기술 기준

SecureProbe AI는 다음 기술을 기본으로 사용한다.

```text
Language:
Python 3.x

HTTP:
httpx

HTML Parsing:
beautifulsoup4

Structured Model:
pydantic

AI Integration:
openai

Test:
pytest
```

정확한 버전은 실제 설치 환경에서 호환성을 확인한 후 고정한다.
임의로 최신 버전을 추정하여 적지 않는다.

## 5. Python 버전

현재 시스템에 설치된 Python 버전을 확인한다.

예:

```bash
python --version
```

또는:

```bash
python3 --version
```

Windows 환경에서는 필요 시:

```bash
py --version
```

을 사용할 수 있다.

가능하면 Python 3.11 이상을 우선한다.
단, 현재 시스템에서 안정적으로 사용 가능한 Python 3.x 버전이 이미 존재하면 불필요한 재설치를 강제하지 않는다.
실제 사용 버전을 결과 문서에 기록한다.

## 6. 가상환경

프로젝트 루트에서 Python 가상환경을 생성하는 방식을 사용한다.

권장 디렉터리:

```text
.venv/
```

예:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows cmd:

```cmd
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

`.venv/`는 Git에 포함하지 않는다.
`.gitignore`에 없다면 추가한다.

## 7. 의존성 관리 방식

v0.1에서는 복잡한 패키지 관리 도구를 추가하지 않는다.

기본 방식:

```text
requirements.txt
```

권장 위치:

```text
secureprobe-ai/
└── requirements.txt
```

Poetry, Pipenv, uv 등은 이번 Task에서 새로 도입하지 않는다.
향후 필요성이 명확할 때 별도 결정한다.

## 8. 최소 의존성

초기 최소 의존성 후보:

```text
httpx
beautifulsoup4
pydantic
openai
pytest
```

필요한 경우 다음도 검토 가능하다.

```text
python-dotenv
```

단, 실제 코드에서 아직 사용하지 않는 라이브러리를 과도하게 추가하지 않는다.

## 9. 버전 고정 원칙

설치 후 실제 동작이 확인된 버전을 `requirements.txt`에 기록한다.

예시 형식:

```text
httpx==<verified-version>
beautifulsoup4==<verified-version>
pydantic==<verified-version>
openai==<verified-version>
pytest==<verified-version>
```

버전 번호를 임의로 작성하지 않는다.
실제 설치 결과를 기반으로 작성한다.

## 10. 환경변수 처리

기존 `.env.example`을 유지한다.
실제 Secret은 Git에 저장하지 않는다.

예:

```text
OPENAI_API_KEY=
```

실제 `.env` 파일은 Git에 포함하지 않는다.

다음이 `.gitignore`에 포함되어 있는지 확인한다.

```text
.env
.env.*
.venv/
```

단:

```text
!.env.example
```

규칙은 유지한다.

## 11. 구현 대상 파일

이번 Task에서 생성 또는 수정 가능한 파일:

```text
requirements.txt
.gitignore
.env.example   # 필요할 경우 최소 수정만 허용
```

결과 문서는 다음 경로에 생성한다.

```text
docs/05_ai_development/codex_results/day01/
D01-T02_PYTHON_ENV_SETUP_RESULT_v0.1.md
```

## 12. 생성 금지

이번 Task에서는 다음 파일/구조를 생성하지 않는다.

```text
secureprobe/agent/*
secureprobe/web/*
secureprobe/source/*
secureprobe/models/*
secureprobe/report/*
tests/unit/*
tests/integration/*
```

이들은 다음 Task에서 처리한다.

## 13. 기능 개발 금지

이번 작업에서는 다음을 수행하지 않는다.

```text
Agent 구현
Pydantic Model 구현
Web Observer 구현
Source Observer 구현
Tool Registry 구현
OpenAI API 호출 코드 구현
SecureBoard 구현
Ground Truth 작성
ZAP 실행
Semgrep 실행
보안진단 실행
```

## 14. 설치 절차

권장 흐름:

```text
1. Python 버전 확인
2. .venv 생성
3. 가상환경 활성화
4. pip 상태 확인
5. 핵심 의존성 설치
6. requirements.txt 작성/정리
7. import 검증
8. pytest 실행 검증
```

## 15. 설치 검증

다음 import가 성공해야 한다.

```bash
python -c "import httpx; import bs4; import pydantic; import openai; import pytest; print('OK')"
```

성공 조건:

```text
ImportError 없음
ModuleNotFoundError 없음
```

## 16. pytest 검증

아직 테스트 코드가 없더라도 `pytest` 명령 자체가 실행 가능해야 한다.

```bash
pytest --version
```

기존 테스트가 있다면:

```bash
pytest
```

를 실행한다.

테스트가 아직 없어서 수집 결과가 0개인 것은 이번 Task에서는 실패가 아니다.

## 17. 환경 재현 검증

가능하면 다음 흐름을 검증한다.

```text
새 가상환경
→ requirements.txt 설치
→ import 성공
→ pytest 실행 가능
```

예:

```bash
pip install -r requirements.txt
```

## 18. requirements.txt 품질 기준

다음을 만족해야 한다.

```text
실제로 필요한 초기 의존성만 포함
중복 package 없음
설치 가능한 버전
실제 검증된 버전
Secret 없음
로컬 절대경로 없음
```

금지:

```text
-e C:\...
file:///...
개인 로컬 경로
```

## 19. .gitignore 확인

최소 다음이 Git에서 제외되는지 확인한다.

```text
.venv/
.env
__pycache__/
.pytest_cache/
*.pyc
```

기존 규칙과 중복되더라도 불필요하게 전체 파일을 재작성하지 않는다.
최소 수정만 한다.

## 20. 보안 제한사항

다음 원칙을 유지한다.

```text
API Key Git 저장 금지
Password Git 저장 금지
Secret Git 저장 금지
Credential Git 저장 금지
실서비스 보안진단 금지
외부 Target 접근 금지
```

이번 Task에서는 외부 보안진단이 필요하지 않다.
Python package 설치를 위한 정상적인 package repository 접근만 허용한다.

## 21. 검증 명령

최소 다음 또는 동등한 명령을 실행한다.

```bash
python --version
python -m pip --version
python -m pip list
pytest --version
python -c "import httpx, bs4, pydantic, openai, pytest; print('IMPORT_OK')"
```

가상환경 내부에서 확인한다.

## 22. Git 검증

작업 전후 다음을 확인한다.

```bash
git status
git diff
```

`.venv/`가 Git 추적 대상에 나타나면 안 된다.

가능하면 다음도 확인한다.

```bash
git check-ignore .venv
git check-ignore .env
```

## 23. 결과 문서

작업 결과를 다음 파일에 기록한다.

```text
docs/05_ai_development/codex_results/day01/
D01-T02_PYTHON_ENV_SETUP_RESULT_v0.1.md
```

## 24. 결과 문서 필수 내용

최소 다음을 기록한다.

```text
Task ID
Status
Python Version
pip Version
Virtual Environment Path
Dependency Management File
Installed Dependencies
Import Validation
pytest Validation
.gitignore Validation
Modified Files
Created Files
Issues
Next Task
```

## 25. 결과 예시 형식

```text
# D01-T02 — Python Environment Setup Result v0.1

## Status

COMPLETED

## Python

Version:
<actual version>

## Virtual Environment

Path:
.venv/

## Dependency Management

requirements.txt

## Installed Dependencies

- httpx ...
- beautifulsoup4 ...
- pydantic ...
- openai ...
- pytest ...

## Validation

Import Validation:
PASS

pytest:
PASS

.gitignore:
PASS

## Modified Files

-

## Created Files

-

## Issues

None

## Next Task

D01-T03 — SecureProbe 기본 Package 구조 생성
```

## 26. 테스트 기준

이번 Task에서는 별도 Unit Test 코드를 작성하지 않는다.

대신 환경 검증 명령을 재현 가능한 테스트 기준으로 사용한다.

```text
가상환경 활성화 가능
requirements 설치 가능
필수 package import 성공
pytest 실행 가능
Secret/venv Git 제외
```

## 27. 완료 조건

다음 조건을 모두 만족해야 완료다.

```text
[ ] Python 3.x 사용 버전 확인
[ ] .venv 생성 및 사용 가능
[ ] .venv Git 제외 확인
[ ] requirements.txt 존재
[ ] 핵심 의존성 설치 성공
[ ] 실제 검증된 버전 기록
[ ] httpx import 성공
[ ] bs4 import 성공
[ ] pydantic import 성공
[ ] openai import 성공
[ ] pytest import/실행 성공
[ ] 실제 Secret Git 미포함
[ ] 결과 문서 작성
[ ] 기능 코드 구현 없음
[ ] git status 검토 완료
```

## 28. Git Commit

모든 검증을 완료한 뒤 Commit 한다.

권장 Commit Message:

```text
chore: set up python development environment
```

결과 문서가 별도 Commit이 필요한 경우:

```text
docs: record python environment setup result
```

불필요한 amend 또는 force push는 하지 않는다.

## 29. 실패 처리

다음 중 하나라도 해결되지 않으면 `COMPLETED`로 기록하지 않는다.

```text
Python 실행 불가
가상환경 생성 실패
requirements 설치 실패
필수 package import 실패
pytest 실행 불가
.venv 또는 Secret이 Git 추적됨
```

상태는:

```text
BLOCKED
또는
FAILED
```

로 기록하고 원인을 결과 문서에 남긴다.

## 30. 완료 보고 형식

```text
D01-T02 PYTHON ENVIRONMENT SETUP

Status:
COMPLETED / BLOCKED / FAILED

Python:
<version>

Virtual Environment:
<path>

Dependency File:
requirements.txt

Validation:
- Package Install: PASS / FAIL
- Import: PASS / FAIL
- pytest: PASS / FAIL
- Git Ignore: PASS / FAIL
- Secret Check: PASS / FAIL

Created Files:
-

Modified Files:
-

Result Document:
docs/05_ai_development/codex_results/day01/D01-T02_PYTHON_ENV_SETUP_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D01-T03 — SecureProbe 기본 Package 구조 생성
```

## 31. 작업 종료 원칙

이번 Task가 완료되더라도 다음 Task를 자동으로 시작하지 않는다.

다음 작업은 별도 지침으로 수행한다.

```text
D01-T03 — SecureProbe 기본 Package 구조 생성
```
