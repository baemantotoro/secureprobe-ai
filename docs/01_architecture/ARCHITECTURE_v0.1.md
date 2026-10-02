# SecureProbe AI — ARCHITECTURE v0.1

## 1. 문서 목적

본 문서는 SecureProbe AI PoC의 전체 시스템 구조와 주요 컴포넌트의 책임을 정의한다.

프로젝트 목표는 20일 안에 다음 두 가지 진단 기능을 갖춘 실행 가능한 PoC를 완성하는 것이다.

1. Web Security Assessment
2. Source Security Assessment

SecureProbe AI는 기존 보안도구의 결과를 단순히 LLM이 요약하는 구조가 아니다.

SecureProbe AI 자체가 다음 Agent Loop를 수행해야 한다.

```text
Observe
  ↓
Plan
  ↓
Select Tool
  ↓
Execute
  ↓
Analyze
  ↓
Verify
  ↓
Report
```

---

# 2. Architecture Goals

본 Architecture는 다음 목표를 우선한다.

## 2.1 구현 가능성

20일 안에 완성 가능한 구조를 사용한다.

복잡한 Multi-Agent Architecture, Autonomous Exploitation Framework, RAG Platform 등은 기본 범위에서 제외한다.

## 2.2 검증 가능성

AI가 취약점이라고 판단한 결과는 가능한 경우 Tool Evidence 또는 사람이 확인할 수 있는 근거를 남긴다.

## 2.3 Benchmark 독립성

다음 도구는 SecureProbe AI 내부 Scanner로 사용하지 않는다.

```text
Web Benchmark    = OWASP ZAP
Source Benchmark = Semgrep
```

SecureProbe와 Benchmark는 동일한 대상에 대해 독립적으로 실행한다.

## 2.4 재현성

Assessment 과정에서 다음 내용을 기록할 수 있어야 한다.

```text
Target
Test Plan
Selected Tool
Tool Input
Tool Output
Evidence
AI Analysis
Verification Result
Finding
Report
```

---

# 3. 전체 시스템 구성

```text
                      ┌─────────────────────────┐
                      │          User           │
                      └────────────┬────────────┘
                                   │
                         Assessment Request
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │     SecureProbe AI      │
                      │                         │
                      │      Agent Engine       │
                      └────────────┬────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                 ▼                                   ▼
       ┌───────────────────┐               ┌───────────────────┐
       │  Web Assessment   │               │ Source Assessment │
       │      Tools        │               │      Tools        │
       └─────────┬─────────┘               └─────────┬─────────┘
                 │                                   │
                 ▼                                   ▼
       ┌───────────────────┐               ┌───────────────────┐
       │  SecureBoard Lab  │               │ Source Directory  │
       └───────────────────┘               └───────────────────┘

                 │                                   │
                 └──────────────┬────────────────────┘
                                ▼
                       ┌───────────────────┐
                       │ Evidence / Finding│
                       └─────────┬─────────┘
                                 ▼
                       ┌───────────────────┐
                       │ Report Generator  │
                       └───────────────────┘
```

Benchmark는 별도 실행 영역으로 유지한다.

```text
SecureBoard Lab ───────→ OWASP ZAP
Source Directory ──────→ Semgrep

SecureProbe Result
        +
Benchmark Result
        +
Ground Truth
        ↓
Comparison Evaluation
```

---

# 4. 주요 Component

## 4.1 User Interface / Assessment Interface

사용자가 진단 요청을 입력한다.

Web Assessment 입력 예:

```text
Target URL
Assessment Scope
Authorization Confirmation
Test Account (optional)
```

Source Assessment 입력 예:

```text
Source Directory
Assessment Scope
Optional Project Information
```

초기 PoC에서는 복잡한 Web UI보다 단순한 UI 또는 API 기반 구조를 우선한다.

---

# 5. Agent Engine

SecureProbe AI의 핵심이다.

Agent Engine은 다음 책임을 갖는다.

```text
Target 관찰
↓
Assessment Plan 생성
↓
필요 Tool 결정
↓
Tool 실행 요청
↓
결과 해석
↓
추가 검증 여부 결정
↓
Finding 생성
↓
Report 생성
```

Agent는 하나의 중앙 Agent를 사용한다.

Multi-Agent 구조는 사용하지 않는다.

---

# 6. Agent 내부 구조

```text
Agent Engine

├── Observer
├── Planner
├── Tool Selector
├── Executor
├── Analyzer
├── Verifier
└── Reporter
```

---

# 7. Observer

Observer는 Target에 대한 초기 정보를 수집한다.

Observer의 목적은 취약점을 바로 판단하는 것이 아니라 Assessment에 필요한 Context를 구성하는 것이다.

## Web Observer

수집 대상:

```text
URL
HTTP Method
Endpoint
Form
Parameter
Cookie
Session
Header
Authentication 여부
Link
Content Type
```

예상 출력:

```text
TargetContext
```

## Source Observer

수집 대상:

```text
Language
Framework
Directory Structure
Important Files
Controller
Service
Repository
Authentication Code
Database Access Code
Input Processing
File Handling
Configuration
```

예상 출력:

```text
SourceContext
```

---

# 8. Planner

Planner는 Observer가 만든 Context를 이용해 Test Plan을 생성한다.

Planner는 LLM을 활용한다.

예:

```json
{
  "target": "http://localhost:8080",
  "tests": [
    {
      "test_id": "WEB-001",
      "category": "security_header",
      "target": "/",
      "reason": "HTTP response header inspection required"
    }
  ]
}
```

Planner의 역할은 다음과 같다.

```text
무엇을 검사할 것인가
왜 검사하는가
어떤 Target에 수행할 것인가
어떤 Tool 종류가 필요한가
```

실제 Tool 실행은 Planner가 직접 수행하지 않는다.

---

# 9. Tool Selector

Planner가 생성한 Test Plan을 기준으로 실행할 Tool을 결정한다.

예:

```text
Test Type:
security_header

Selected Tool:
http_header_inspector
```

Tool 선택 결과는 Structured Output으로 기록한다.

---

# 10. Executor

Executor는 실제 Tool을 호출한다.

중요한 원칙:

LLM이 임의의 시스템 명령을 직접 실행하지 않는다.

실행 가능한 Tool은 사전에 등록된 Tool Registry에서만 선택한다.

```text
LLM
 ↓
Tool Selection
 ↓
Tool Registry
 ↓
Approved Tool
 ↓
Execution
```

이 구조를 통해 Tool Calling을 통제한다.

---

# 11. Tool Registry

SecureProbe가 실행할 수 있는 Tool을 등록하는 영역이다.

예:

```text
ToolRegistry

Web Tools
├── http_request
├── endpoint_collector
├── form_parser
├── header_inspector
├── cookie_inspector
├── auth_session_inspector
└── input_test_runner

Source Tools
├── directory_scanner
├── file_reader
├── language_detector
├── framework_detector
├── source_search
├── code_context_collector
└── pattern_checker
```

각 Tool은 최소 다음 정보를 가진다.

```text
Tool Name
Description
Input Schema
Output Schema
Risk Level
Active / Passive
```

---

# 12. Web Assessment Architecture

Web Assessment 흐름:

```text
Target URL
   ↓
Safety Gate
   ↓
Web Observer
   ↓
Target Context
   ↓
AI Planner
   ↓
Web Test Plan
   ↓
Tool Selector
   ↓
Web Tools
   ↓
HTTP Evidence
   ↓
Analyzer
   ↓
Verifier
   ↓
Finding
```

---

# 13. Web Tool 원칙

Web Assessment 내부 Tool은 ZAP을 사용하지 않는다.

초기 구현은 Python 기반의 제한된 HTTP 도구를 우선한다.

권장 기술:

```text
Python
httpx
BeautifulSoup
urllib.parse
```

필요 시 Session/Cookie 유지 기능을 제공한다.

JavaScript-heavy SPA 전체 자동 탐색은 v0.1 범위에 포함하지 않는다.

브라우저 자동화가 반드시 필요한 경우 이후 별도 결정한다.

---

# 14. Web Security Test 범위

20일 PoC에서는 모든 Web 취약점을 자동 공격하는 구조를 만들지 않는다.

우선 Ground Truth와 직접 연결되는 테스트를 구현한다.

후보:

```text
Security Header
Cookie Configuration
Reflected Input Behavior
Stored Input Behavior
Access Control / IDOR
Basic SQL Injection behavior
File Upload Validation
Path Traversal
Information Exposure
CSRF-related indicators
```

각 테스트는 SecureBoard Lab을 기준으로 검증한다.

---

# 15. Source Assessment Architecture

```text
Source Directory
   ↓
Source Observer
   ↓
Project Context
   ↓
AI Planner
   ↓
Source Test Plan
   ↓
Tool Selector
   ↓
Source Tools
   ↓
Code Evidence
   ↓
Analyzer
   ↓
Verifier
   ↓
Finding
```

---

# 16. Source Tool 원칙

SecureProbe Source Assessment 내부에서 Semgrep 결과를 입력받아 분석하는 방식은 사용하지 않는다.

SecureProbe는 자체적으로 다음 기능을 수행한다.

```text
Directory 탐색
파일 분류
언어 탐지
Framework 탐지
위험 코드 검색
관련 Source Context 수집
AI Context 분석
```

PoC 단계에서는 완전한 Compiler 수준 AST Analyzer를 자체 구현하지 않는다.

초기 Source Tool은 다음 수준으로 제한한다.

```text
File / Directory Inspection
Keyword / Pattern Search
Context Extraction
Configuration Inspection
Simple Language-aware Analysis
```

AI는 해당 Evidence를 함께 분석한다.

---

# 17. Semgrep의 위치

Semgrep은 SecureProbe Agent 내부 Tool이 아니다.

구조:

```text
Source Directory
       │
       ├──────────→ SecureProbe Source Assessment
       │
       └──────────→ Semgrep
```

결과는 마지막 Evaluation 단계에서만 비교한다.

---

# 18. Analyzer

Analyzer는 Tool 결과와 Target Context를 이용해 취약점 후보를 생성한다.

입력:

```text
Target Context
Test Plan
Tool Result
Evidence
```

출력:

```text
Candidate Finding
```

Analyzer는 Tool 결과에 없는 사실을 Evidence로 만들 수 없다.

---

# 19. Verifier

Verifier는 Candidate Finding의 신뢰도를 확인한다.

검증 방식은 Finding 종류에 따라 다르다.

예:

```text
Header Finding
→ 실제 HTTP Response Header 확인

Source Finding
→ 실제 Code Location 확인

Access Control Finding
→ 다른 권한/세션 요청 결과 비교
```

검증 상태 예:

```text
UNVERIFIED
TOOL_VERIFIED
MANUAL_REQUIRED
MANUAL_VERIFIED
REJECTED
```

AI 판단만으로 `VERIFIED` 상태를 부여하지 않는다.

---

# 20. Evidence Model

Evidence는 Finding을 뒷받침하는 실제 근거이다.

Web 예:

```text
Request
Response
Header
Parameter
Status Code
Response Fragment
```

Source 예:

```text
File Path
Line
Code Snippet
Matched Pattern
Related Context
```

Evidence는 Finding과 연결 가능한 ID를 가진다.

---

# 21. Finding Model

Finding의 최소 구조:

```text
Finding ID
Vulnerability Name
Severity
Assessment Type
Location
Description
Cause
Evidence
OWASP Mapping
CWE Mapping
Impact
Remediation
Developer Guide
AI Reasoning Summary
Validation Status
```

세부 JSON Schema는 별도의 `DATA_SCHEMA_v0.1.md`에서 정의한다.

---

# 22. Report Generator

Report Generator는 Verified Finding 또는 Manual Review가 필요한 Finding을 기반으로 보고서를 생성한다.

보고서 종류:

```text
SecureProbe Web Assessment Report
SecureProbe Source Assessment Report
Benchmark Report
Comparison Report
```

---

# 23. Ground Truth

Ground Truth는 SecureBoard Lab에 의도적으로 구현된 취약점의 정답 데이터다.

SecureProbe는 Assessment 실행 중 Ground Truth를 읽으면 안 된다.

즉:

```text
SecureProbe Assessment
         X
    Ground Truth
```

진단 완료 후 Evaluation 단계에서만 Ground Truth와 비교한다.

```text
SecureProbe Result
       +
Ground Truth
       ↓
Evaluation
```

이 구조를 지켜야 평가 결과의 신뢰성이 유지된다.

---

# 24. Evaluation Architecture

비교 대상:

```text
SecureProbe AI
OWASP ZAP
Semgrep
Manual Verification
Ground Truth
```

평가 지표:

```text
TP
FP
FN
Precision
Recall
Assessment Time
Report Quality
```

SecureProbe가 기존 도구보다 더 좋은 결과를 내도록 Ground Truth를 편향시키지 않는다.

---

# 25. Safety Gate

Web Active Assessment 전에 반드시 Safety Gate를 통과해야 한다.

```text
Assessment Request
       ↓
Safety Gate
       ↓
ALLOW / DENY
```

기본 허용 대상:

```text
localhost
127.0.0.1
Docker Lab
Explicit Allowlist
```

그 외 대상은 Active Assessment를 기본 차단한다.

Test Account 입력은 허가 증명이 아니다.

---

# 26. Tool Risk Level

Tool은 최소 다음 두 종류로 분류한다.

```text
PASSIVE
ACTIVE
```

예:

```text
Header Inspection        PASSIVE
HTML Parsing             PASSIVE
Source File Reading      PASSIVE

SQLi Validation Request  ACTIVE
Input Mutation           ACTIVE
Upload Test              ACTIVE
Access Control Test      ACTIVE
```

ACTIVE Tool은 Safety Gate를 통과한 Target에 대해서만 실행한다.

---

# 27. LLM 책임과 비책임

LLM이 담당:

```text
Target Context 해석
Test Plan 생성
Tool 선택 판단
Tool 결과 분석
추가 검증 결정
Finding 설명
Remediation 설명
Report 작성
```

LLM이 직접 담당하지 않는 것:

```text
임의 Shell 실행
임의 네트워크 연결
Ground Truth 접근
무제한 Payload 생성
운영 시스템 침해
데이터 파괴
Persistence
Credential Stuffing
```

---

# 28. 권장 SecureProbe 내부 구조

초기 구현 구조:

```text
secureprobe/
├── agent/
│   ├── observer.py
│   ├── planner.py
│   ├── selector.py
│   ├── executor.py
│   ├── analyzer.py
│   └── verifier.py
│
├── core/
│   ├── config.py
│   ├── safety.py
│   └── registry.py
│
├── web/
│   ├── observer.py
│   └── tools/
│
├── source/
│   ├── observer.py
│   └── tools/
│
├── models/
│   ├── target.py
│   ├── plan.py
│   ├── evidence.py
│   └── finding.py
│
├── report/
│   └── generator.py
│
└── main.py
```

이 구조는 구현 과정에서 필요에 따라 최소한의 조정은 가능하지만, 책임 분리는 유지한다.

---

# 29. 구현 기술 권장안

SecureProbe AI:

```text
Language:
Python 3.x

HTTP:
httpx

HTML Parsing:
BeautifulSoup

Structured Model:
Pydantic

AI Integration:
OpenAI API

Test:
pytest

Report:
Markdown + JSON
```

PoC에서는 PDF Report 생성은 필수 기능으로 두지 않는다.

먼저 JSON과 Markdown Report가 안정적으로 생성되도록 한다.

---

# 30. SecureBoard 관계

SecureBoard는 SecureProbe 내부 Component가 아니다.

```text
SecureBoard
=
Assessment Target
```

SecureBoard의 코드와 SecureProbe의 코드는 분리한다.

SecureBoard는 Ground Truth 기반 취약점 재현 환경을 제공한다.

---

# 31. Benchmark 관계

```text
                  ┌── SecureProbe
SecureBoard ──────┤
                  └── OWASP ZAP

                  ┌── SecureProbe
Source Directory ─┤
                  └── Semgrep
```

어느 한쪽의 결과도 다른 진단기의 입력으로 사용하지 않는다.

---

# 32. 데이터 흐름

전체 데이터 흐름:

```text
Assessment Request
        ↓
Safety / Scope Validation
        ↓
Observer
        ↓
Target Context
        ↓
Planner
        ↓
Test Plan
        ↓
Tool Selector
        ↓
Tool Executor
        ↓
Tool Result
        ↓
Evidence
        ↓
Analyzer
        ↓
Candidate Finding
        ↓
Verifier
        ↓
Finding
        ↓
Report
```

---

# 33. AI Agent 인정 기준

본 프로젝트에서 SecureProbe AI를 AI Agent라고 정의하기 위한 최소 조건:

```text
1. Target을 관찰한다.
2. AI가 Test Plan을 생성한다.
3. 필요한 Tool을 선택한다.
4. Tool이 실제 실행된다.
5. 실행 결과를 분석한다.
6. 필요 시 추가 검증을 결정한다.
7. Evidence와 Finding을 생성한다.
8. Report를 생성한다.
```

다음 구조는 Agent로 인정하지 않는다.

```text
ZAP 실행
   ↓
결과 JSON
   ↓
LLM 요약
```

또는:

```text
Semgrep 실행
   ↓
결과 JSON
   ↓
LLM 설명
```

---

# 34. v0.1에서 제외할 Architecture

20일 프로젝트 범위를 보호하기 위해 다음은 제외한다.

```text
Multi-Agent
Vector Database
Full RAG Platform
Autonomous Exploitation Framework
Exploit Chaining
Persistence
Post Exploitation
Malware Analysis Platform
Distributed Scanner
Kubernetes
Message Queue
Microservice Architecture
Complex Event Bus
Full Browser Automation
```

필요성이 입증될 때만 이후 버전에서 검토한다.

---

# 35. Architecture Decision Summary

현재 Architecture의 핵심 결정은 다음과 같다.

```text
Agent:
Single Agent

Architecture:
Modular Monolith

SecureProbe Runtime:
Python

Agent Loop:
Observe
→ Plan
→ Select Tool
→ Execute
→ Analyze
→ Verify
→ Report

Web Scanner:
Custom lightweight tools

Source Scanner:
Custom inspection/context tools

ZAP:
Independent Web Benchmark

Semgrep:
Independent Source Benchmark

Ground Truth:
Evaluation-only

LLM Output:
Structured Output

Tool Execution:
Registry-based controlled execution

Active Assessment:
localhost / Docker / Allowlist only

Evidence:
Required for Finding

Report:
JSON + Markdown first
```

---

# 36. 다음 설계 문서

본 Architecture가 확정된 후 다음 문서를 작성한다.

```text
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
```

그 이후:

```text
docs/03_wbs/WBS_20DAYS_v0.1.md
```

를 작성하고 실제 구현 Task로 분해한다.
