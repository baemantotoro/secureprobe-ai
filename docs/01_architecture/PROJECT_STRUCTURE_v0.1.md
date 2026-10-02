# Project Structure v0.1

## 1. Current Project Tree

```text
secureprobe-ai/
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── 00_context/
│   │   └── PROJECT_CONTEXT_v0.1.md
│   ├── 01_architecture/
│   │   ├── ARCHITECTURE_v0.1.md
│   │   ├── AGENT_FLOW_v0.1.md
│   │   └── PROJECT_STRUCTURE_v0.1.md
│   ├── 02_spec/
│   │   ├── DATA_SCHEMA_v0.1.md
│   │   └── .gitkeep
│   ├── 03_wbs/
│   │   └── WBS_20DAYS_v0.1.md
│   ├── 04_decisions/
│   │   └── TASK_001_PROJECT_INIT_REPORT.md
│   ├── 05_ai_development/
│   │   ├── codex_tasks/
│   │   │   ├── README.md
│   │   │   └── day01/
│   │   │       └── D01-T01_VALIDATE_BASELINE_DOCS_v0.1.md
│   │   └── codex_results/
│   │       └── day01/
│   │           └── D01-T01_BASELINE_VALIDATION_v0.1.md
│   └── 06_test/
│       └── .gitkeep
├── secureboard/
│   └── README.md
├── secureprobe/
│   └── README.md
├── ground_truth/
│   └── README.md
├── benchmarks/
│   ├── README.md
│   ├── zap/
│   │   └── .gitkeep
│   └── semgrep/
│       └── .gitkeep
├── evidence/
│   ├── web/
│   │   └── .gitkeep
│   └── source/
│       └── .gitkeep
├── reports/
│   ├── secureprobe/
│   │   └── .gitkeep
│   ├── benchmark/
│   │   └── .gitkeep
│   └── comparison/
│       └── .gitkeep
├── testdata/
│   ├── web/
│   │   └── .gitkeep
│   └── source/
│       └── .gitkeep
├── scripts/
│   └── .gitkeep
├── tests/
│   └── .gitkeep
└── .env.example
```

## 2. Top-level Directory Roles

- `README.md`: 프로젝트 개요와 보안 원칙을 설명한다.
- `.gitignore`: OS, IDE, 환경변수, secret, key, credential 등을 제외한다.
- `docs/`: 프로젝트 문서, 아키텍처, 명세, 작업계획, 의사결정, AI 개발 이력, 테스트 계획을 관리한다.
- `docs/05_ai_development/`: AI-assisted Development 과정에서 사용하는 Codex 작업지침과 실행 결과를 관리한다.
  - `codex_tasks/`: Codex 실행 지침
  - `codex_results/`: Codex 실행 및 검증 결과
- `secureboard/`: 자체 보안 테스트용 웹 애플리케이션의 Lab 영역이다.
- `secureprobe/`: 직접 개발하는 AI 기반 보안진단 Agent 영역이다.
- `ground_truth/`: 취약점 정답 정보와 비교 평가 기준을 보관한다.
- `benchmarks/`: OWASP ZAP, Semgrep 등 기존 도구의 결과를 저장한다.
- `evidence/`: HTTP, 소스, 스크린샷, 분석 근거와 증거 자료를 보관한다.
- `reports/`: SecureProbe, Benchmark, Comparison 산출물 저장소이다.
- `testdata/`: 웹/소스 진단용 더미 데이터 저장소이다.
- `scripts/`: 설치, 실행, 정리, 리포트 보조 스크립트 용도이다.
- `tests/`: Unit, Integration, Agent Workflow, Report Generator, Evaluation 구조용 디렉터리이다.

## 3. SecureBoard and SecureProbe Separation Principle

`secureboard/`와 `secureprobe/`는 서로 다른 책임을 가진다.

- SecureBoard Lab은 테스트 대상 애플리케이션이며, 취약점을 포함할 수 있는 제한된 환경을 제공한다.
- SecureProbe는 AI Agent 기반 보안진단 모듈로서 진단 로직을 담당한다.
- 두 영역은 기능적으로 분리되어 있으며, 서로 코드나 구현을 혼합하지 않는다.

## 4. Benchmark Tool Independent Execution Principle

Benchmark는 기존 무료 도구의 결과를 보관하기 위한 영역이다.

- Web benchmark: OWASP ZAP
- Source benchmark: Semgrep

중요한 원칙은 SecureProbe AI가 ZAP/Semgrep 결과를 그대로 받아 AI가 요약하는 구조로 만들지 않는다는 점이다.

SecureProbe와 Benchmark Tool은 동일한 테스트 대상을 각각 독립적으로 진단한다.

## 5. Ground Truth / Evidence / Report Relationship

- `ground_truth/`: 정답지 역할. 취약점 ID, 위치, 원인, 수정방법 등 비교 기준을 저장한다.
- `evidence/`: 재현 과정, HTTP 응답, 코드 스니펫, 스크린샷, 분석 근거를 기록한다.
- `reports/`: 실제 진단 보고서 및 비교 평가 결과를 저장한다.

이 구조에 따라 실제 결과는 Ground Truth와 Evidence를 기준으로 검증되며, 비교 보고서를 작성한다.

## 6. Architecture Status

현재 시스템 전체 Architecture는 아직 확정되지 않았다.

이번 단계에서는 프로젝트 구조와 책임 분리를 정리하는 초기 골격 생성에 집중한다.

실제 Agent 구조, Tool 선정, 데이터 흐름, API 연결 방식은 이후 설계 문서에서 정의한다.

`PROJECT_CONTEXT_v0.1.md`는 `docs/00_context/`에 저장되어 있으며,
SecureProbe AI 프로젝트의 기준 Context 문서로 관리한다.

## 7. Principle for Minimal Structural Change

`ARCHITECTURE_v0.1` 문서가 작성되기 전까지는 구조 변경을 최소화하고, 너무 많은 구현 세부 사항을 미리 확정하지 않는다.

이 문서는 초기 프로젝트 구조를 안정적으로 정리하기 위한 기준으로 사용되며, 이후 아키텍처 설계에서 세부 변경이 추가될 수 있다.
