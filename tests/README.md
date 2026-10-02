# Test Suite

## 목적

이 디렉터리는 SecureProbe AI 프로젝트의 테스트 기반을 정리한다.

- 환경 검증 Smoke Test
- 패키지 구조 검증 Smoke Test
- 이후 Unit Test 추가 공간
- 이후 Integration Test 추가 공간
- Fixture 데이터 보관 공간

## 구조

```text
tests/
├── README.md
├── test_python_env_smoke.py
├── test_package_structure_smoke.py
├── unit/
│   └── .gitkeep
├── integration/
│   └── .gitkeep
├── fixtures/
│   └── .gitkeep
└── __pycache__/
```

## 역할

### unit/

순수 로직 테스트를 보관한다.

예시:
- Pydantic model validation
- Safety gate
- Tool registry
- Evaluation formula

### integration/

여러 component가 연결되는 흐름을 검증한다.

예시:
- Web observer flow
- Source observer flow
- Report rendering flow

### fixtures/

테스트 입력 데이터와 고정 샘플을 보관한다.

## 실행 방법

```bash
pytest -q
```

특정 smoke test:

```bash
pytest tests/test_python_env_smoke.py -q
pytest tests/test_package_structure_smoke.py -q
```

## 규칙

- 기존 Smoke Test는 삭제하거나 이동하지 않는다.
- 기능 구현은 별도 Task에서 진행한다.
- 테스트 파일명은 의미 있는 이름으로 작성한다.
- 테스트 코드는 실제 보안 취약점 재현 payload를 넣지 않는다.
