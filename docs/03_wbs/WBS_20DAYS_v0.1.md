# SecureProbe AI — WBS 20 DAYS v0.1

## 1. 문서 목적

본 문서는 SecureProbe AI 프로젝트를 20일 안에 실제 실행 가능한 취업 포트폴리오 PoC로 완성하기 위한 작업분해구조(WBS)다.

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
```

본 WBS는 다음 원칙을 따른다.

```text
범위 확대보다 완성도 우선
Single Agent
Modular Monolith
Structured Output
Evidence 기반 Finding
Ground Truth 기반 평가
ZAP / Semgrep 독립 Benchmark
localhost / Docker / Allowlist 대상만 Active Assessment
```

---

# 2. 20일 최종 완료 목표

20일차 종료 시 다음을 실제로 보여줄 수 있어야 한다.

## 2.1 실행 가능한 SecureBoard Lab

최소 기능:

```text
회원가입
로그인 / 로그아웃
게시판 CRUD
댓글
검색
파일 업로드 / 다운로드
마이페이지
관리자 기능
REST API
```

모든 기능을 완벽하게 만들 필요는 없다.

Ground Truth 취약점과 SecureProbe 평가에 필요한 기능을 우선한다.

---

## 2.2 실행 가능한 SecureProbe AI

두 가지 모드:

```text
Web Security Assessment
Source Security Assessment
```

Agent Flow:

```text
Observe
→ Plan
→ Select Tool
→ Execute
→ Analyze
→ Verify
→ Report
```

---

## 2.3 Benchmark

```text
Web:
OWASP ZAP

Source:
Semgrep
```

SecureProbe와 독립적으로 동일 대상을 진단한다.

---

## 2.4 비교 평가

Ground Truth 기준:

```text
TP
FP
FN
Precision
Recall
Assessment Time
```

자동진단 결과와 사람의 수동검증 결과를 구분한다.

---

## 2.5 포트폴리오 산출물

최소:

```text
Architecture
Agent Flow
Data Schema
Ground Truth
Test Result
SecureProbe Report
ZAP Report
Semgrep Report
Comparison Report
Portfolio Summary
README
```

---

# 3. 전체 일정 요약

| Day | 핵심 목표 | 주요 산출물 |
|---:|---|---|
| 1 | 설계 기준 확정 및 개발환경 | 설계 검토, 환경 설정 |
| 2 | 공통 모델 / Agent Skeleton | Pydantic Model, Agent State |
| 3 | SecureBoard 기본 골격 | 실행 가능한 Lab |
| 4 | SecureBoard 인증/게시판 | 로그인, 게시판 |
| 5 | SecureBoard 파일/관리자/API | 주요 기능 완성 |
| 6 | Ground Truth 삽입 1 | GT Web 기본 취약점 |
| 7 | Ground Truth 삽입 2 / 검증 | GT 확정본 |
| 8 | Web Observer / Passive Tools | TargetContext 생성 |
| 9 | Planner / Tool Registry | TestPlan + Tool Selection |
| 10 | Web Active Tools | 제한된 Active Test |
| 11 | Analyzer / Verifier | Candidate → Finding |
| 12 | Web Report / Web E2E | Web Assessment 완주 |
| 13 | Source Observer / Tools | SourceContext 생성 |
| 14 | Source Planner / Analyzer | Source Finding |
| 15 | Source E2E / Report | Source Assessment 완주 |
| 16 | ZAP / Semgrep Benchmark | Benchmark Raw Result |
| 17 | Evaluation Engine | TP/FP/FN/Precision/Recall |
| 18 | 수동검증 / Re-Test | Manual Verification |
| 19 | 통합시험 / 수정 | Release Candidate |
| 20 | 포트폴리오 / 문서 마감 | 최종 README / 비교보고서 |

---

# 4. 개발 우선순위

우선순위는 다음과 같다.

```text
P0 = 반드시 완료
P1 = 가능하면 완료
P2 = 시간 여유가 있을 때만
```

P0 기능이 미완성인 상태에서 P1/P2 기능을 추가하지 않는다.

---

# 5. Day 1 — 설계 기준 확정 및 개발환경

## 목표

설계 문서를 실제 구현 기준으로 고정하고 Python 개발환경을 준비한다.

## Task

### D01-T01 — 기준 문서 검증

확인:

```text
PROJECT_CONTEXT_v0.1
ARCHITECTURE_v0.1
AGENT_FLOW_v0.1
DATA_SCHEMA_v0.1
```

충돌 여부를 확인한다.

### D01-T02 — Python Project 설정

예상:

```text
Python 3.x
venv
pytest
pydantic
httpx
beautifulsoup4
openai
```

정확한 버전은 구현 시점에서 requirements 파일로 고정한다.

### D01-T03 — SecureProbe 기본 Package 구조 생성

```text
secureprobe/
├── agent/
├── core/
├── web/
├── source/
├── models/
├── report/
└── main.py
```

### D01-T04 — 테스트 구조 생성

```text
tests/
├── unit/
├── integration/
└── fixtures/
```

## 검증

```text
Python 환경 실행 가능
pytest 실행 가능
package import 성공
```

## 완료 조건

```text
[ ] 개발환경 재현 가능
[ ] 기본 Package import 성공
[ ] 테스트 Skeleton 실행 성공
```

---

# 6. Day 2 — 공통 Data Model / Agent Skeleton

## 목표

DATA_SCHEMA_v0.1을 실제 Pydantic Model로 옮긴다.

## Task

### D02-T01 — 공통 Enum 구현

```text
AssessmentType
AssessmentStatus
RiskLevel
ExecutionStatus
ValidationStatus
Severity
```

### D02-T02 — Assessment Model 구현

```text
AssessmentRequest
AssessmentRun
ValidationResult
AssessmentError
AssessmentResult
```

### D02-T03 — Agent Model 구현

```text
TestPlan
TestCase
ToolDefinition
ToolSelection
ToolExecution
Evidence
CandidateFinding
VerificationRequest
Finding
AgentEvent
```

### D02-T04 — Validation Unit Test

필수 Field 누락, 잘못된 Enum 등을 테스트한다.

## 검증

```text
정상 JSON → Model 생성 성공
잘못된 JSON → Validation 실패
```

## 완료 조건

```text
[ ] 핵심 Model 구현
[ ] Schema Validation Unit Test PASS
```

---

# 7. Day 3 — SecureBoard 기본 골격

## 목표

SecureBoard Lab을 실제 실행 가능하게 만든다.

## 구현 방향

프레임워크는 구현 복잡도를 최소화한다.

예:

```text
Python + Flask
SQLite
Server-rendered HTML
```

기술 선택은 구현 전에 최종 확정한다.

## Task

### D03-T01 — SecureBoard Project 생성

### D03-T02 — DB 기본 구조

최소:

```text
users
posts
comments
files
```

### D03-T03 — 기본 UI

```text
Home
Login
Register
Board
```

### D03-T04 — Docker 또는 Local 실행방식 결정

Docker 사용 시 최소 구성만 만든다.

## 검증

```text
localhost에서 App 실행
DB 생성
Home 접근
```

## 완료 조건

```text
[ ] SecureBoard 실행 성공
[ ] 기본 DB 사용 가능
```

---

# 8. Day 4 — 인증 및 게시판

## 목표

보안진단에 필요한 핵심 업무 흐름을 만든다.

## Task

### D04-T01 — 회원가입

### D04-T02 — 로그인 / 로그아웃

### D04-T03 — 게시판 CRUD

### D04-T04 — 댓글

### D04-T05 — 검색

### D04-T06 — 일반 사용자 / 관리자 Role

## 검증

```text
회원가입
로그인
게시물 등록
조회
수정
삭제
댓글
검색
```

## 완료 조건

```text
[ ] 인증 흐름 정상
[ ] 게시판 흐름 정상
```

---

# 9. Day 5 — 파일 / 관리자 / REST API

## 목표

Ground Truth 진단용 기능을 보완한다.

## Task

### D05-T01 — 파일 업로드

### D05-T02 — 파일 다운로드

### D05-T03 — 마이페이지

### D05-T04 — 회원정보 수정

### D05-T05 — 관리자 회원관리

### D05-T06 — 최소 REST API

예:

```text
GET /api/posts
GET /api/posts/{id}
```

필요 시 Ground Truth에 맞는 API만 구현한다.

## 검증

각 기능 정상 동작 확인.

## 완료 조건

```text
[ ] SecureBoard 핵심 기능 완성
```

---

# 10. Day 6 — Ground Truth 삽입 1

## 목표

취약점을 무작정 많이 넣는 것이 아니라 비교 가능한 Ground Truth를 구현한다.

## 초기 대상

P0 후보:

```text
GT-01 SQL Injection
GT-02 Reflected XSS
GT-03 Stored XSS
GT-04 Broken Access Control / IDOR
GT-08 Security Header
GT-09 Cookie / Session Configuration
```

P1 후보:

```text
GT-05 CSRF
GT-06 File Upload Validation
GT-07 Path Traversal
GT-10 Information Exposure
```

## Task

### D06-T01 — Ground Truth Schema 작성

각 GT:

```text
ID
취약점명
Severity
Location
취약 코드
원인
재현방법
Evidence 기준
OWASP
CWE
수정방법
Re-Test 기준
```

### D06-T02 — P0 취약점 일부 구현

### D06-T03 — 정상 코드와 취약 코드 위치 기록

## 완료 조건

```text
[ ] 최소 4개 이상 실제 재현 가능
```

---

# 11. Day 7 — Ground Truth 삽입 2 / 검증

## 목표

Ground Truth를 진단 비교의 정답지로 확정한다.

## Task

### D07-T01 — 나머지 P0 구현

### D07-T02 — 가능 시 P1 일부 구현

### D07-T03 — 수동 재현

Browser / DevTools / Source Review 등을 이용한다.

### D07-T04 — Ground Truth v0.1 작성

권장 경로:

```text
ground_truth/GROUND_TRUTH_v0.1.md
```

또는 필요 시 JSON 병행.

## 완료 조건

```text
[ ] 각 GT 재현 성공
[ ] Evidence 기준 명확
[ ] 수정방법 정의
[ ] Re-Test 방법 정의
```

---

# 12. Day 8 — Web Observer / Passive Tools

## 목표

URL을 입력했을 때 TargetContext를 생성한다.

## Task

### D08-T01 — Safety Gate 기본 구현

허용:

```text
localhost
127.0.0.1
::1
Allowlist
```

### D08-T02 — http_request

### D08-T03 — endpoint_collector

### D08-T04 — form_parser

### D08-T05 — header_inspector

### D08-T06 — cookie_inspector

### D08-T07 — WebTargetContext 생성

## Unit Test

```text
localhost 허용
외부 임의 Target Active 차단
HTML Form 추출
Header 추출
Cookie Attribute 추출
```

## 완료 조건

```text
[ ] URL → WebTargetContext 생성 성공
```

---

# 13. Day 9 — Planner / Tool Registry

## 목표

AI가 TargetContext를 보고 TestPlan을 만들도록 한다.

## Task

### D09-T01 — Tool Registry

각 Tool:

```text
name
description
capability
risk_level
input_schema
output_schema
```

### D09-T02 — Planner

OpenAI API + Structured Output.

### D09-T03 — TestPlan Validation

### D09-T04 — Tool Selector

Capability 기반 Tool 선택.

### D09-T05 — Planner Retry

최대 2회.

## 테스트

Mock LLM Output을 사용한 Unit Test를 먼저 만든다.

## 완료 조건

```text
[ ] TargetContext → TestPlan
[ ] TestCase → Registered Tool
[ ] Invalid Plan Reject
```

---

# 14. Day 10 — Web Active Tools

## 목표

Ground Truth 검증에 필요한 최소 Active Tool을 구현한다.

## P0 Tool 후보

```text
input_test_runner
access_control_tester
path_request_tester
upload_validation_tester
```

실제 구현 Tool은 Ground Truth에 맞춰 줄일 수 있다.

## 원칙

```text
Safety Gate 통과 Target만 실행
Scope 밖 요청 금지
파괴적 Payload 금지
서비스 장애 유발 금지
```

## 테스트

SecureBoard에 대해서만 Integration Test.

## 완료 조건

```text
[ ] 최소 SQLi/XSS/Access Control 중 핵심 Active Test 동작
[ ] Safety Gate 우회 불가
```

---

# 15. Day 11 — Analyzer / Verifier

## 목표

Tool 실행 결과를 Finding으로 바꾸는 핵심 Agent 판단 Loop를 완성한다.

## Task

### D11-T01 — Analyzer

입력:

```text
TargetContext
TestCase
ToolResult
Evidence
```

출력:

```text
No Finding
또는
CandidateFinding
```

### D11-T02 — Verifier

Decision:

```text
ACCEPT_TOOL_VERIFIED
REQUEST_ADDITIONAL_TOOL
REQUEST_MANUAL_REVIEW
REJECT
```

### D11-T03 — Additional Verification Loop

최대 2회.

### D11-T04 — Evidence 연결

Finding → Evidence IDs.

## 완료 조건

```text
[ ] Candidate 생성 가능
[ ] 추가 Tool 검증 가능
[ ] TOOL_VERIFIED / MANUAL_REQUIRED / REJECTED 구분 가능
```

---

# 16. Day 12 — Web Report / Web E2E

## 목표

Web Assessment 전체 흐름을 처음부터 끝까지 실행한다.

## E2E Flow

```text
URL 입력
↓
Safety Gate
↓
Observe
↓
Plan
↓
Tool Select
↓
Execute
↓
Analyze
↓
Verify
↓
Report
```

## Task

### D12-T01 — Assessment Orchestrator

### D12-T02 — JSON Report

### D12-T03 — Markdown Report

### D12-T04 — Audit Event 기록

## Integration Test

SecureBoard 대상 전체 Web Assessment 1회.

## 완료 조건

```text
[ ] Web Assessment E2E 성공
[ ] JSON 생성
[ ] Markdown 생성
[ ] Evidence Trace 가능
```

---

# 17. Day 13 — Source Observer / Source Tools

## 목표

Source Directory에서 SourceContext를 생성한다.

## Tool

```text
directory_scanner
file_reader
language_detector
framework_detector
source_search
code_context_collector
pattern_checker
```

## Task

### D13-T01 — Directory Scope Validation

### D13-T02 — Ignore Rule

```text
.git
node_modules
target
dist
venv
binary
```

### D13-T03 — Language / Framework Detection

### D13-T04 — 중요 파일 분류

### D13-T05 — SourceTargetContext 생성

## 완료 조건

```text
[ ] SecureBoard Source → SourceContext
```

---

# 18. Day 14 — Source Planner / Analyzer

## 목표

AI가 SourceContext를 보고 검사 계획을 만들고 코드 Evidence를 분석한다.

## Task

### D14-T01 — Source TestPlan

### D14-T02 — Source Tool Selection

### D14-T03 — Pattern / Context Evidence

### D14-T04 — Source Candidate Finding

### D14-T05 — 추가 Context Verification

예:

```text
pattern_checker
→ Candidate
→ file_reader
→ 주변 Context
→ Verified / Manual Required
```

## 완료 조건

```text
[ ] Source Candidate Finding 생성
[ ] Evidence File/Line 추적 가능
```

---

# 19. Day 15 — Source E2E / Report

## 목표

Source Security Assessment 전체를 완주한다.

## Task

### D15-T01 — Source Orchestrator 연결

### D15-T02 — Source Report

### D15-T03 — Web/Source 공통 Agent 구조 정리

중복 코드를 제거하되 대규모 Refactoring은 하지 않는다.

## Integration Test

SecureBoard source를 대상으로 실행.

## 완료 조건

```text
[ ] Source Assessment E2E 성공
[ ] JSON/Markdown Report 생성
```

---

# 20. Day 16 — ZAP / Semgrep Benchmark

## 목표

SecureProbe와 기존 무료 Tool을 동일 대상에서 독립 실행한다.

## ZAP

대상:

```text
SecureBoard Lab
```

결과:

```text
benchmarks/zap/
```

## Semgrep

대상:

```text
SecureBoard Source
```

결과:

```text
benchmarks/semgrep/
```

## Task

### D16-T01 — ZAP 실행 절차 문서화

### D16-T02 — ZAP 결과 보관

### D16-T03 — Semgrep 실행 절차 문서화

### D16-T04 — Semgrep 결과 보관

### D16-T05 — BenchmarkFinding Normalization

## 완료 조건

```text
[ ] ZAP 결과 확보
[ ] Semgrep 결과 확보
[ ] SecureProbe 입력으로 사용하지 않았음을 확인
```

---

# 21. Day 17 — Evaluation Engine

## 목표

Ground Truth 기준으로 실제 성능을 계산한다.

## Task

### D17-T01 — Detection Matching Rule

```text
Ground Truth ↔ Finding
```

위치와 취약점 종류를 이용한다.

### D17-T02 — TP / FP / FN 계산

### D17-T03 — Precision / Recall

```text
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
```

### D17-T04 — Scanner별 Summary

```text
SecureProbe Web
ZAP
SecureProbe Source
Semgrep
```

### D17-T05 — Assessment Time 기록

## 완료 조건

```text
[ ] 비교표 자동 또는 재현 가능하게 생성
```

---

# 22. Day 18 — 수동 검증 / Re-Test

## 목표

자동진단 결과를 사람이 검증한다.

## 도구

```text
Browser Developer Tools
Burp Suite Community
Source Code Review
```

필요한 범위에서만 사용한다.

## Task

### D18-T01 — SecureProbe Finding 검증

### D18-T02 — ZAP Finding 검증

### D18-T03 — Semgrep Finding 검증

### D18-T04 — False Positive 확인

### D18-T05 — False Negative 확인

### D18-T06 — 일부 취약점 수정 후 Re-Test

가능하면 1~2개 대표 취약점으로 증명한다.

## 완료 조건

```text
[ ] 자동/수동 결과 구분
[ ] FP/FN 원인 기록
```

---

# 23. Day 19 — 통합시험 / 수정 / Freeze

## 목표

기능 추가를 멈추고 전체 품질을 확보한다.

## Task

### D19-T01 — 전체 E2E 재실행

```text
SecureBoard
SecureProbe Web
SecureProbe Source
ZAP
Semgrep
Evaluation
```

### D19-T02 — Unit Test 전체 실행

### D19-T03 — Integration Test 전체 실행

### D19-T04 — 오류 수정

### D19-T05 — Scope Freeze

이날부터 신규 기능 추가 금지.

## 완료 조건

```text
[ ] 주요 Test PASS
[ ] E2E 재현 가능
[ ] Release Candidate 확보
```

---

# 24. Day 20 — Portfolio / 최종 문서

## 목표

코드가 아니라 채용 담당자가 이해할 수 있는 포트폴리오로 완성한다.

## Task

### D20-T01 — README 최종 정리

포함:

```text
문제 정의
왜 만들었는가
Architecture
Agent Flow
실행 방법
Demo
평가 방법
결과
한계
```

### D20-T02 — Comparison Report

예:

```text
SecureProbe vs ZAP
SecureProbe vs Semgrep
```

### D20-T03 — Portfolio Summary

강조할 역량:

```text
보안진단 설계
AI Agent 설계
Tool Calling
Structured Output
Evidence 기반 검증
Ground Truth 실험 설계
기존 Tool Benchmark
AI-assisted Development
```

### D20-T04 — 한계와 개선점

과장하지 않는다.

예:

```text
SPA 탐색 한계
Source 분석 범위 한계
LLM 판단 오류 가능성
Ground Truth 규모 한계
PoC 수준 Tool Coverage
```

### D20-T05 — 최종 Demo 검증

처음 보는 환경에서 실행 가능한지 확인.

## 완료 조건

```text
[ ] Portfolio 문서 완성
[ ] Demo 시나리오 완성
[ ] Git Repository 정리
```

---

# 25. 핵심 Milestone

## M1 — Day 2

```text
Architecture + Schema + Agent Skeleton 완료
```

## M2 — Day 7

```text
SecureBoard + Ground Truth 완료
```

## M3 — Day 12

```text
Web Assessment E2E 완료
```

## M4 — Day 15

```text
Source Assessment E2E 완료
```

## M5 — Day 18

```text
Benchmark + Evaluation + Manual Verification 완료
```

## M6 — Day 20

```text
Portfolio Release 완료
```

---

# 26. Scope Cut Rule

일정이 밀릴 경우 다음 순서로 제거한다.

## 먼저 제거

```text
P2 UI 개선
추가 취약점
추가 Tool
복잡한 Report Styling
Full Browser Automation
Trivy 추가
PDF Report
```

## 다음 제거

```text
P1 Ground Truth 일부
P1 Active Tool 일부
```

## 절대 제거하지 않음

```text
Agent Loop
Web Assessment E2E
Source Assessment E2E
Evidence
Finding
Ground Truth
ZAP 비교
Semgrep 비교
TP/FP/FN
Precision/Recall
Portfolio 결과
```

---

# 27. Ground Truth 목표 수량

초기 목표:

```text
P0: 6개
P1: 최대 4개
총 최대: 10개
```

그러나 일정이 밀리면:

```text
6개를 정확하게 구현·검증
>
10개를 불완전하게 구현
```

을 우선한다.

---

# 28. Web Tool 목표 수량

v0.1 최소:

```text
http_request
endpoint_collector
form_parser
header_inspector
cookie_inspector
input_test_runner
access_control_tester
```

필요 시 일부 기능을 하나의 Tool에 통합할 수 있다.

---

# 29. Source Tool 목표 수량

v0.1 최소:

```text
directory_scanner
file_reader
language_detector
framework_detector
source_search
code_context_collector
pattern_checker
```

---

# 30. Agent 구현 최소 증명 시나리오

Portfolio Demo에서는 최소 다음 흐름을 보여준다.

## Web

```text
SecureBoard URL 입력
↓
Target 관찰
↓
AI Test Plan
↓
header_inspector 선택
↓
Evidence 확보
↓
Candidate Finding
↓
추가 검증
↓
TOOL_VERIFIED Finding
↓
Report
```

## Source

```text
SecureBoard Source 선택
↓
언어 / Framework 탐지
↓
AI Test Plan
↓
pattern_checker
↓
Candidate Finding
↓
file_reader로 추가 Context
↓
Finding
↓
Report
```

이 두 사례만 명확히 보여도 Agent 구조 증명 가치가 높다.

---

# 31. 테스트 정책

모든 중요 Task에는 최소 하나의 검증방법이 있어야 한다.

## Unit Test 대상

```text
Pydantic Model
Safety Gate
Tool Registry
Tool Selector
Parser
Source Scanner
Evaluation Formula
```

## Integration Test 대상

```text
Web Observer
Web Agent
Source Observer
Source Agent
Report Generator
Evaluation
```

## E2E

```text
SecureBoard → SecureProbe Web → Report
SecureBoard Source → SecureProbe Source → Report
```

---

# 32. Codex Task 분해 원칙

Codex에는 하루 전체를 한 번에 맡기지 않는다.

각 작업은 가능하면 다음 정도로 나눈다.

```text
TASK-xxx
목적
입력
출력
파일
구현 요구사항
제한사항
테스트 기준
완료 조건
```

한 Task에서 너무 많은 파일을 수정하지 않는다.

---

# 33. Git 운영 원칙

권장:

```text
main
```

초기 PoC에서는 복잡한 Git Flow를 도입하지 않는다.

Task 단위 Commit을 사용한다.

예:

```text
feat: add assessment models
feat: add safety gate
feat: add web observer
test: add web observer integration tests
docs: add ground truth v0.1
```

---

# 34. 문서 Version 관리

중요 문서는 버전을 유지한다.

```text
PROJECT_CONTEXT_v0.1
ARCHITECTURE_v0.1
AGENT_FLOW_v0.1
DATA_SCHEMA_v0.1
WBS_20DAYS_v0.1
GROUND_TRUTH_v0.1
```

기존 결정을 변경하면 관련 문서와 충돌 여부를 확인한다.

---

# 35. 위험요소

## R1 — SecureBoard 구현에 시간 과다

대응:

```text
UI 최소화
기능 최소화
Ground Truth 중심
```

## R2 — LLM Structured Output 불안정

대응:

```text
Pydantic Validation
Retry 제한
Mock 기반 Test
```

## R3 — Web Tool 범위 확대

대응:

```text
Ground Truth와 직접 연결되는 Tool만 구현
```

## R4 — Source Analyzer 과도한 복잡성

대응:

```text
AST 전체 구현 금지
Pattern + Context + AI 분석
```

## R5 — 비교평가 시점 지연

대응:

```text
Day 16 이전에 기능 개발 종료
```

## R6 — Portfolio 작성 시간 부족

대응:

```text
개발 과정 중 Evidence와 문서 지속 기록
Day 20에 처음 작성하지 않음
```

---

# 36. 프로젝트 진행 상태 표기

진행상태는 다음 값만 사용한다.

```text
NOT_STARTED
IN_PROGRESS
COMPLETED
BLOCKED
DEFERRED
```

---

# 37. 일일 종료 체크

매일 종료 시 기록:

```text
오늘 완료 Task
미완료 Task
Test 결과
발견된 문제
설계 변경 여부
다음 Day 진입 가능 여부
```

---

# 38. 최종 Definition of Done

SecureProbe AI v0.1은 다음 조건을 모두 만족할 때 완료다.

```text
[ ] SecureBoard Lab 실행 가능
[ ] Ground Truth 재현 가능
[ ] Web Assessment E2E 실행 가능
[ ] Source Assessment E2E 실행 가능
[ ] AI Test Plan 생성
[ ] Tool Selection 수행
[ ] Tool 실제 실행
[ ] Evidence 생성
[ ] Analyzer Candidate 생성
[ ] Verifier 추가 검증 결정 가능
[ ] Finding Validation Status 기록
[ ] JSON Report 생성
[ ] Markdown Report 생성
[ ] ZAP Benchmark 확보
[ ] Semgrep Benchmark 확보
[ ] TP/FP/FN 계산
[ ] Precision/Recall 계산
[ ] Manual Verification 기록
[ ] SecureProbe가 놓친 결과도 기록
[ ] Portfolio README 완성
[ ] 실행/재현 방법 문서화
```

---

# 39. 20일 프로젝트 성공 기준

이 프로젝트의 성공은 다음이 아니다.

```text
취약점을 가장 많이 찾는 것
ZAP보다 무조건 높은 성능
Semgrep보다 무조건 높은 성능
완전 자율 Pentest 시스템
```

성공 기준은 다음이다.

```text
설계한 AI Agent가 실제로 동작하고,
Evidence 기반으로 Web/Source Finding을 생성하며,
기존 도구 및 Ground Truth와 비교하여
AI 기반 보안진단의 성능과 한계를 재현 가능하게 설명할 수 있는 것
```

---

# 40. 다음 작업

본 WBS가 확정되면 실제 개발은 Day 1부터 시작한다.

첫 구현 작업은 다음 순서로 시작한다.

```text
D01-T01 기준 문서 검증
D01-T02 Python 개발환경
D01-T03 SecureProbe 기본 Package 구조
D01-T04 Test Skeleton
```

Codex 지침은 각 Task별로 별도로 생성한다.
