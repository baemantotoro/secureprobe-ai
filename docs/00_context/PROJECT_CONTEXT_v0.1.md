# SecureProbe AI — PROJECT CONTEXT v0.1

## 1. 프로젝트 목적

20일 동안 취업 포트폴리오용 보안 프로젝트를 완성한다.

이 프로젝트의 목적은 단순한 취약 웹사이트 제작이나
기존 보안도구 실행이 아니다.

직접 구축한 통제된 테스트 웹 애플리케이션을 대상으로

1. 기존 무료 보안진단 도구
2. 직접 개발한 AI 기반 보안진단 Agent
3. 사람에 의한 수동 검증

결과를 비교하여

- 웹 취약점 진단 능력
- 소프트웨어 보안약점 진단 능력
- AI 활용 개발 능력
- AI Agent 설계 및 Tool Calling 능력
- 취약점 분석 및 보고서 작성 능력
- 기존 자동화 도구와 AI 진단의 차이와 한계 분석 능력

을 취업 포트폴리오로 증명한다.


# 2. 프로젝트 가칭

SecureProbe AI

SecureProbe AI는 외부 제품명이 아니라 현재 프로젝트에서
직접 개발할 AI 기반 보안진단 Agent의 가칭이다.

공개 전 동일 제품명/상표/오픈소스 존재 여부를 확인하여
필요하면 명칭을 변경한다.


# 3. 프로젝트 범위

SecureProbe AI는 크게 두 가지 진단 모드를 제공한다.

## A. Web Security Assessment

사용자가 URL을 입력한다.

필요한 경우 인증된 영역 진단을 위해 테스트 계정 정보를 입력한다.

중요:
계정 입력은 대상 시스템에 대한 진단 허가를 증명하는 용도가 아니다.
인증 후 접근 가능한 기능을 테스트하기 위한 인증정보일 뿐이다.

사용자는 별도로 다음을 확인해야 한다.

"본인은 해당 시스템의 소유자이거나
보안진단을 수행할 명시적 권한을 보유하고 있습니다."

개발/포트폴리오 단계의 Active Assessment 대상은 기본적으로

- localhost
- Docker Lab
- 사전에 Allowlist에 등록한 테스트 대상

으로 제한한다.

SecureProbe AI는 대상 웹 애플리케이션을 분석하여

- URL
- Endpoint
- Form
- Parameter
- Authentication
- Session/Cookie
- HTTP Header

등을 파악하고 필요한 보안 테스트를 계획한다.


## B. Source Security Assessment

사용자가 진단할 소스코드 폴더를 선택한다.

SecureProbe AI는

- 언어
- Framework
- 프로젝트 구조
- Controller
- Service
- Repository
- 인증/인가 설정
- 외부 입력 처리
- 데이터베이스 접근 코드
- 파일 처리
- 설정파일

등을 분석한다.

정적분석 결과와 코드 Context를 이용하여
소프트웨어 보안약점 후보를 식별하고 보고서를 작성한다.


# 4. AI Agent의 최소 구조

멀티 에이전트 시스템을 만들지 않는다.

20일 프로젝트에서는 하나의 AI Agent를 중심으로 구현한다.

기본 Agent Loop:

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

AI Agent는 단순히 기존 스캐너 결과를 요약하는 역할에 머물지 않는다.

대상 정보를 분석하여

- 무엇을 검사할 것인지 결정하고
- 적절한 Tool을 선택하고
- 결과를 분석하고
- 필요한 경우 추가 확인을 수행하고
- Finding을 생성한다.

이 조건을 만족하는 것을 AI Agent 구현의 기준으로 한다.


# 5. SecureProbe AI 주요 기능

## Web Mode

예상 기능:

- Target URL 입력
- Scope 입력
- 진단권한 확인
- 테스트 계정 입력(선택)
- 사이트 구조 탐색
- Endpoint / Parameter 수집
- HTTP Request/Response 분석
- 보안 Header 분석
- Cookie 설정 분석
- 인증/인가 관련 테스트
- 입력값 관련 취약점 테스트
- Finding 생성
- 자동 보고서 생성


## Source Mode

예상 기능:

- Source Directory 선택
- 언어/Framework 자동 감지
- 중요 Source File 식별
- 정적분석 도구 실행
- 관련 Source Context 수집
- AI 기반 결과 분석
- CWE Mapping
- OWASP Mapping
- 취약 원인 설명
- 개발 보안 가이드
- 수정방안 제안
- 자동 보고서 생성


# 6. 비교 대상 도구

## 웹 진단

SecureProbe AI Web Assessment
VS
OWASP ZAP

ZAP은 SecureProbe 내부 도구로 사용하지 않는다.

ZAP은 기존 무료 DAST 제품의 독립적인 Benchmark로 사용한다.


## Source 진단

SecureProbe AI Source Assessment
VS
Semgrep

필요하면 Dependency/Container 분석용으로 Trivy를 추가할 수 있다.


## 수동 검증

Burp Suite Community
Browser Developer Tools
Source Code Review

등을 사용하여 자동진단 결과를 사람이 검증한다.


# 7. 테스트용 웹 애플리케이션

외부 실서비스를 공격하지 않는다.

직접 제작한 테스트 애플리케이션을 사용한다.

가칭:

SecureBoard Lab

주요 기능:

- 회원가입
- 로그인 / 로그아웃
- 게시판 CRUD
- 댓글
- 검색
- 파일 업로드 / 다운로드
- 마이페이지
- 회원정보 수정
- 관리자 회원관리
- REST API


# 8. Ground Truth

SecureBoard에는 통제된 취약점을 의도적으로 삽입한다.

예상 항목:

GT-01 SQL Injection
GT-02 Reflected XSS
GT-03 Stored XSS
GT-04 Broken Access Control / IDOR
GT-05 CSRF
GT-06 File Upload Validation
GT-07 Path Traversal
GT-08 Security Header
GT-09 Cookie / Session Configuration
GT-10 Information Exposure

필요에 따라 조정한다.

취약점의 수를 늘리는 것보다

- 발생 원인
- 취약 코드
- 진단방법
- Evidence
- 보안조치
- Re-Test

를 설명할 수 있는 수준으로 구현하는 것을 우선한다.


# 9. 비교평가

각 취약점은 Ground Truth 기준으로 평가한다.

TP = 실제 취약점을 탐지
FP = 취약점이 아닌 것을 취약하다고 판단
FN = 실제 취약점을 탐지하지 못함

주요 평가항목:

- Detection
- Precision
- Recall
- False Positive
- False Negative
- Assessment Time
- Report Quality

SecureProbe AI가 ZAP/Semgrep보다 반드시 좋은 결과를 내도록
실험을 설계하지 않는다.

결과가 더 낮더라도 그 원인과 AI 방식의 장단점을 분석한다.


# 10. 보고서 Finding 기본 Schema

각 Finding은 가능한 한 다음 정보를 포함한다.

- Finding ID
- 취약점명
- Severity
- Target URL 또는 Source Location
- 취약점 설명
- 발생 원인
- Evidence
- OWASP Mapping
- CWE Mapping
- 영향
- 개선방안
- 개발 가이드
- AI 판단 근거
- Validation Status


# 11. AI 활용 역량

프로젝트에서는 다음 AI 기술을 실제 구현/기록한다.

- Codex 기반 AI-assisted Development
- Task Decomposition
- Prompt Engineering
- Context Engineering
- Structured Output
- JSON Schema Validation
- Tool Calling
- Agent Loop
- AI 결과 검증
- Human-in-the-loop

중요:
"AI가 만들어 주었다"가 포트폴리오의 메시지가 아니다.

사람이

- 요구사항
- Architecture
- 보안진단 기준
- Ground Truth
- 평가방법
- 결과검증

을 설계하고,

Codex는 코드 구현, 테스트, 리팩터링, 디버깅에 활용한다.


# 12. 역할 구분

## Human

- 프로젝트 목표 결정
- 보안진단 기준 결정
- 취약점 설계
- Ground Truth 관리
- Agent Architecture 설계
- 테스트 결과 검증
- 최종 보고서 승인


## Codex

- 코드 구현 보조
- Unit Test 작성
- Integration Test 작성
- Debugging
- Refactoring
- Documentation 보조


## SecureProbe AI

- Target 분석
- Test Plan 수립
- Tool 선택
- Tool 실행
- 결과 분석
- 취약점 후보 생성
- Evidence 정리
- Report 초안 생성


# 13. 보안 및 윤리 원칙

프로젝트의 취약점 진단과 모의해킹 기능은

- 직접 소유한 시스템
- 로컬 Lab
- Docker 테스트 환경
- 명시적인 진단 허가를 받은 시스템

에서만 수행한다.

실제 외부 서비스에 대한 무단 진단을 프로젝트 범위로 하지 않는다.

다음 기능은 기본 목표에서 제외한다.

- Credential Stuffing
- 지속성 확보
- 데이터 파괴
- 데이터 외부 반출
- Malware
- 무제한 Shell 실행
- 운영환경 침해
- 서비스 장애 유발


# 14. 20일 제한

이 프로젝트는 연구용 완전 자율 AI Pentest 시스템 개발이 아니다.

20일 안에 완성 가능한 PoC를 목표로 한다.

우선순위:

1. 동작하는 SecureBoard Lab
2. Web Assessment
3. Source Assessment
4. AI Agent Loop
5. 자동 Report
6. ZAP/Semgrep 비교
7. 수동 검증
8. Portfolio 문서

범위 확대보다 완성도를 우선한다.


# 15. 최종 목표

최종 포트폴리오에서는 다음 메시지가 명확하게 보여야 한다.

"기존 보안진단 프로세스에 AI Agent를 적용해
웹 및 소스코드 진단을 자동화하고,
기존 무료 보안도구 및 수동진단 결과와 비교하여
AI 기반 보안진단의 성능과 한계를 검증하였다."
