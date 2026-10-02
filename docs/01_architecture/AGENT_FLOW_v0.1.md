# SecureProbe AI — AGENT FLOW v0.1

## 1. 문서 목적

본 문서는 `ARCHITECTURE_v0.1.md`에서 정의한 SecureProbe AI의 Agent Loop를
실제 구현 가능한 상태 전이와 실행 규칙으로 구체화한다.

기준 Agent Loop:

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

본 문서의 목적은 단순 순차 파이프라인이 아니라 다음을 명확히 하는 것이다.

- 각 단계의 입력과 출력
- 각 단계의 종료 조건
- Tool 실패 처리
- LLM 실패 처리
- 추가 검증 결정
- Verify 후 재실행 조건
- Finding 확정 조건
- Manual Review 전환 조건
- Agent 전체 종료 조건

본 문서는 Web Security Assessment와 Source Security Assessment에 공통으로 적용한다.

---

# 2. 기본 원칙

## 2.1 Single Agent

SecureProbe AI는 v0.1에서 단일 Agent를 사용한다.

Multi-Agent, Agent 간 협상, 역할 분산 Agent 구조는 사용하지 않는다.

## 2.2 Controlled Tool Execution

Agent는 임의 명령을 실행할 수 없다.

실행 가능한 기능은 Tool Registry에 등록된 Tool로 제한한다.

```text
Agent Decision
    ↓
Tool Registry
    ↓
Registered Tool
    ↓
Executor
```

## 2.3 Evidence First

취약점 판단은 Evidence 없이 확정하지 않는다.

```text
AI 판단만 존재
→ Candidate Finding

Tool Evidence 존재
→ 검증 가능

Tool 또는 Manual 검증 완료
→ Verified Finding
```

## 2.4 Ground Truth Isolation

Assessment 실행 중 Agent는 Ground Truth를 참조하지 않는다.

Ground Truth는 Evaluation 단계에서만 사용한다.

## 2.5 Safety First

ACTIVE Tool은 Safety Gate를 통과한 Target에서만 실행한다.

---

# 3. Assessment 실행 단위

한 번의 진단 요청을 `Assessment Run`으로 정의한다.

각 Assessment Run은 고유한 ID를 가진다.

예:

```text
assessment_id = WEB-20261002-0001
```

또는:

```text
assessment_id = SRC-20261002-0001
```

Assessment Run은 다음 전체 수명주기를 가진다.

```text
CREATED
  ↓
VALIDATING
  ↓
OBSERVING
  ↓
PLANNING
  ↓
EXECUTING
  ↓
ANALYZING
  ↓
VERIFYING
  ↓
REPORTING
  ↓
COMPLETED
```

실패 시:

```text
FAILED
```

사용자 또는 정책에 의해 차단되면:

```text
BLOCKED
```

---

# 4. 최상위 Agent State

Agent의 최상위 상태는 다음으로 제한한다.

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
FAILED
BLOCKED
```

상태는 자유 문자열이 아니라 Enum으로 관리한다.

---

# 5. 전체 상태 전이

```text
Assessment Request
        ↓
     CREATED
        ↓
   VALIDATING
     ├─ Fail Safety/Scope → BLOCKED
     └─ Pass
        ↓
    OBSERVING
     ├─ Fatal Error → FAILED
     └─ TargetContext
        ↓
     PLANNING
     ├─ LLM Error → Retry
     ├─ Invalid Schema → Retry
     └─ TestPlan
        ↓
  SELECTING_TOOL
     ├─ Tool 없음 → MANUAL_REQUIRED 또는 Test Skip
     └─ Selected Tool
        ↓
    EXECUTING
     ├─ Tool Error → Retry / Skip / Failed Test
     └─ ToolResult + Evidence
        ↓
    ANALYZING
     ├─ No Finding → Next Test
     └─ Candidate Finding
        ↓
    VERIFYING
     ├─ Additional Tool Required ─────────┐
     │                                   │
     │                                   ▼
     │                             SELECTING_TOOL
     │                                   │
     ├─ Manual Required → Finding(MANUAL_REQUIRED)
     ├─ Rejected → Finding(REJECTED)
     └─ Verified → Finding(TOOL_VERIFIED)
        ↓
   Next Planned Test?
     ├─ Yes → SELECTING_TOOL
     └─ No
        ↓
    REPORTING
        ↓
    COMPLETED
```

---

# 6. Phase 0 — Assessment Request

## 입력

Web:

```text
Target URL
Scope
Authorization Confirmation
Optional Test Account
```

Source:

```text
Source Directory
Scope
Optional Project Metadata
```

## 출력

```text
AssessmentRequest
```

## 필수 조건

다음 정보가 없으면 실행하지 않는다.

Web:

```text
Target URL
Assessment Mode
Authorization Confirmation
```

Source:

```text
Source Directory
Assessment Mode
```

---

# 7. Phase 1 — VALIDATING

VALIDATING 단계는 Agent 실행 전에 정책과 입력을 확인한다.

## Web Validation

확인 항목:

```text
URL 형식
Scheme
Hostname
Target Scope
Authorization Confirmation
localhost 여부
Docker/Lab 여부
Allowlist 여부
```

ACTIVE Assessment가 허용되지 않은 경우:

```text
state = BLOCKED
```

## Source Validation

확인 항목:

```text
Directory 존재
Directory 읽기 가능
허용 범위 내부인지
Repository 크기 제한
명백한 Binary-only Directory 여부
```

## 출력

```text
ValidationResult
```

---

# 8. Safety Gate

ACTIVE Web Assessment는 Safety Gate를 반드시 거친다.

기본 허용 조건:

```text
localhost
127.0.0.1
::1
Docker Lab
Explicit Allowlist
```

다음은 기본 차단한다.

```text
Unknown External Target
Public Internet Target without Allowlist
Scope 밖 Endpoint
```

Test Account는 Safety Gate를 우회하는 근거로 사용하지 않는다.

---

# 9. Phase 2 — OBSERVE

Observer는 Target Context를 만든다.

Observer는 취약점 결론을 내리지 않는다.

---

# 10. Web Observe Flow

```text
Target URL
   ↓
Initial HTTP Request
   ↓
Response Metadata
   ↓
HTML Parsing
   ↓
Link/Form/Parameter Collection
   ↓
Cookie/Header Collection
   ↓
TargetContext
```

수집 대상:

```text
URL
Method
Status Code
Content Type
Headers
Cookies
Links
Forms
Parameters
Authentication Indicators
Session Indicators
```

Observer가 발견하지 못한 Endpoint를 임의로 생성하지 않는다.

---

# 11. Source Observe Flow

```text
Source Directory
   ↓
Directory Scan
   ↓
Language Detection
   ↓
Framework Detection
   ↓
Important File Classification
   ↓
Code Context Collection
   ↓
SourceContext
```

수집 대상:

```text
Languages
Frameworks
Directory Tree
Controllers
Services
Repositories
Authentication Files
Configuration Files
Database Access
Input Handling
File Handling
```

---

# 12. Observe 종료 조건

다음 조건 중 하나를 만족하면 Observe를 종료한다.

```text
필요한 최소 Target Context 확보
설정된 최대 탐색 범위 도달
탐색 가능한 항목 소진
```

무한 크롤링은 하지 않는다.

---

# 13. Phase 3 — PLAN

Planner는 TargetContext를 기반으로 TestPlan을 생성한다.

Planner는 LLM Structured Output을 사용한다.

## Planner 입력

```text
Assessment Request
Target Context
Allowed Tool Categories
Project Security Policy
```

Ground Truth와 Benchmark 결과는 입력하지 않는다.

## Planner 출력

```text
TestPlan
```

---

# 14. Test Plan 구성

각 Test Case는 최소 다음 정보를 가진다.

```text
test_id
category
target
reason
required_capability
risk_level
priority
expected_evidence
```

예:

```json
{
  "test_id": "WEB-001",
  "category": "security_header",
  "target": "/",
  "reason": "Response security header configuration 확인",
  "required_capability": "header_inspection",
  "risk_level": "PASSIVE",
  "priority": 1,
  "expected_evidence": [
    "response_headers"
  ]
}
```

---

# 15. Plan Validation

LLM이 생성한 TestPlan은 즉시 실행하지 않는다.

다음 검사를 수행한다.

```text
Schema Validation
Unknown Category 확인
Target Scope 확인
Risk Level 확인
Tool 지원 가능성 확인
중복 Test 제거
```

검증 실패 시 Planner에 재요청한다.

---

# 16. Planner Retry 규칙

다음 경우 재시도한다.

```text
Invalid JSON
Schema Validation 실패
필수 Field 누락
등록되지 않은 Risk Level
명백한 Scope 위반
```

최대 재시도:

```text
2회
```

2회 실패하면:

```text
Assessment = FAILED
reason = PLAN_GENERATION_FAILED
```

---

# 17. Phase 4 — SELECT TOOL

Tool Selector는 TestPlan의 각 Test Case에 적합한 Tool을 선택한다.

입력:

```text
Test Case
Tool Registry
Target Context
```

출력:

```text
ToolSelection
```

---

# 18. Tool Selection 규칙

Tool은 반드시 Registry에 존재해야 한다.

예:

```text
security_header
→ header_inspector

cookie_configuration
→ cookie_inspector

source_pattern
→ pattern_checker
```

등록된 Tool이 없다면 임의 Tool을 생성하지 않는다.

대신:

```text
execution_status = UNSUPPORTED
validation_status = MANUAL_REQUIRED
```

로 처리할 수 있다.

---

# 19. Tool Risk Check

Tool 실행 직전에 Risk Level을 다시 확인한다.

```text
PASSIVE
→ 기본 실행 가능

ACTIVE
→ Safety Gate 상태 확인
```

Safety Gate가 ALLOW가 아니면 ACTIVE Tool을 실행하지 않는다.

---

# 20. Phase 5 — EXECUTE

Executor는 선택된 Tool을 실제 호출한다.

Executor는 Tool의 입력/출력을 기록한다.

기록 대상:

```text
tool_name
tool_input
started_at
finished_at
duration
success
tool_output
error
```

---

# 21. Tool Execution Result

모든 Tool은 공통 Wrapper 결과를 반환한다.

```text
SUCCESS
FAILED
TIMEOUT
BLOCKED
UNSUPPORTED
```

Tool 자체 결과와 실행 상태를 구분한다.

예:

```text
Tool 실행은 성공했지만
취약한 Header를 찾지 못함
```

은:

```text
execution_status = SUCCESS
finding_candidate = false
```

이다.

---

# 22. Tool Retry 규칙

Tool Retry는 제한적으로 수행한다.

재시도 가능한 경우:

```text
Temporary Network Error
Timeout
Transient File Read Error
```

재시도하지 않는 경우:

```text
Scope Block
Permission Denied
Invalid Input
Tool Unsupported
Safety Gate Denied
```

기본 최대 Retry:

```text
1회
```

---

# 23. Phase 6 — ANALYZE

Analyzer는 다음을 입력으로 받는다.

```text
TargetContext
TestCase
ToolSelection
ToolResult
Evidence
```

Analyzer는 Candidate Finding을 생성하거나 Finding 없음으로 판단한다.

---

# 24. Analyzer 출력

두 가지 중 하나다.

## A. No Finding

```text
candidate = null
analysis_result = NO_FINDING
```

## B. Candidate Finding

```text
analysis_result = CANDIDATE_FINDING
candidate_finding = ...
```

Candidate는 아직 확정 Finding이 아니다.

---

# 25. Analyzer 제한

Analyzer는 다음을 하면 안 된다.

```text
Tool Output에 없는 HTTP Response 생성
존재하지 않는 Code Line 생성
실행하지 않은 Payload 결과 주장
Ground Truth 기반 결론 생성
```

Evidence에 없는 내용은 추론과 사실을 구분하여 기록한다.

---

# 26. Phase 7 — VERIFY

Verifier는 Candidate Finding을 검증한다.

Verifier의 핵심 질문:

```text
현재 Evidence만으로 Finding을 확정할 수 있는가?
추가 Tool 검증이 필요한가?
사람 검증이 필요한가?
Candidate를 기각해야 하는가?
```

---

# 27. Verification Decision

Verifier는 다음 중 하나를 선택한다.

```text
ACCEPT_TOOL_VERIFIED
REQUEST_ADDITIONAL_TOOL
REQUEST_MANUAL_REVIEW
REJECT
```

---

# 28. Additional Verification Loop

추가 검증이 필요하면 Agent는 Tool Selection으로 돌아간다.

```text
Candidate Finding
      ↓
Verifier
      ↓
REQUEST_ADDITIONAL_TOOL
      ↓
Tool Selector
      ↓
Executor
      ↓
Analyzer
      ↓
Verifier
```

이 흐름이 SecureProbe AI의 핵심 Agent Loop다.

---

# 29. Verification Loop 제한

무한 반복을 막기 위해 Finding 하나당 추가 검증 횟수를 제한한다.

기본값:

```text
max_verification_rounds = 2
```

최대 횟수에 도달했지만 확정할 수 없다면:

```text
validation_status = MANUAL_REQUIRED
```

---

# 30. Verification 예 — Header

```text
header_inspector 실행
       ↓
X-Content-Type-Options 없음
       ↓
Candidate Finding
       ↓
Evidence의 실제 Response Header 재확인
       ↓
TOOL_VERIFIED
```

---

# 31. Verification 예 — Source

```text
pattern_checker
       ↓
위험한 SQL 문자열 구성 발견
       ↓
Candidate Finding
       ↓
file_reader로 주변 코드 Context 확보
       ↓
입력값이 실제 Query로 연결되는지 분석
       ↓
TOOL_VERIFIED 또는 MANUAL_REQUIRED
```

---

# 32. Verification 예 — Access Control

```text
User A Request
      ↓
Resource Response
      ↓
User B Session으로 동일 Resource 요청
      ↓
결과 비교
      ↓
Unauthorized Access 확인
      ↓
TOOL_VERIFIED
```

단, ACTIVE 검증은 Safety Gate 통과 Target에서만 수행한다.

---

# 33. Finding Validation Status

Finding 상태는 다음으로 제한한다.

```text
UNVERIFIED
TOOL_VERIFIED
MANUAL_REQUIRED
MANUAL_VERIFIED
REJECTED
```

AI 분석만으로 `TOOL_VERIFIED`를 부여할 수 없다.

---

# 34. Test Case 반복

하나의 Test Case가 종료되면 다음 Test Case를 실행한다.

```text
Current Test Complete
       ↓
Remaining Tests?
   ├─ Yes → SELECTING_TOOL
   └─ No  → REPORTING
```

---

# 35. Dynamic Additional Test

Analyzer 또는 Verifier가 추가 Test 필요성을 판단할 수 있다.

단, 다음 조건을 모두 만족해야 한다.

```text
기존 Assessment Scope 내부
등록된 Tool로 수행 가능
Risk Policy 준수
추가 검증 목적이 명확
```

추가 Test는 TestPlan에 기록 후 실행한다.

즉, 숨겨진 임의 행동을 허용하지 않는다.

---

# 36. Dynamic Test 제한

Assessment Run당 동적 추가 Test 수를 제한한다.

초기값:

```text
max_dynamic_tests = 5
```

20일 PoC에서는 복잡한 장기 자율 탐색을 하지 않는다.

---

# 37. Phase 8 — REPORT

모든 Test Case 처리가 끝나면 Report 단계로 이동한다.

입력:

```text
Assessment Metadata
Target Context Summary
Executed Test Cases
Evidence
Findings
Errors
Manual Review Items
```

출력:

```text
JSON Assessment Result
Markdown Assessment Report
```

---

# 38. Report 포함 내용

최소 포함:

```text
Assessment ID
Assessment Type
Target
Scope
Started / Finished Time
Executed Tests
Findings
Validation Status
Evidence Reference
Errors / Skipped Tests
Manual Review Required
```

---

# 39. Assessment 종료 조건

다음 조건을 만족하면 COMPLETED 처리한다.

```text
모든 실행 가능한 Test Case 종료
Finding 상태 결정
Report 생성 성공
```

Finding이 0개여도 Assessment는 성공할 수 있다.

---

# 40. FAILED 조건

다음과 같은 치명적 오류는 Assessment를 FAILED 처리한다.

```text
Target Context 생성 불가
TestPlan 생성 최종 실패
필수 Model Validation 실패
Report 생성 불가
내부 Agent State 손상
```

일부 Tool 실패만으로 Assessment 전체를 실패 처리하지 않는다.

---

# 41. BLOCKED 조건

다음은 BLOCKED다.

```text
Active Assessment Safety Gate 거부
Scope Validation 실패
권한 확인 필수 조건 불충족
```

BLOCKED와 FAILED는 구분한다.

---

# 42. Partial Success

일부 Test가 실패해도 나머지가 정상 수행되면 Assessment는 완료할 수 있다.

예:

```text
Overall Status = COMPLETED_WITH_WARNINGS
```

v0.1에서 사용할 전체 상태:

```text
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
BLOCKED
```

---

# 43. Error Model

Error는 최소 다음 정보를 기록한다.

```text
error_id
phase
code
message
retryable
tool_name
test_id
```

내부 Stack Trace는 사용자 Report에 그대로 노출하지 않는다.

---

# 44. LLM 호출 실패

LLM 호출 실패 시:

```text
Retryable API Error
→ 1회 재시도

Invalid Structured Output
→ 최대 2회 재요청

지속 실패
→ 해당 Phase 실패
```

LLM 실패로 임의 자유 텍스트 fallback을 사용하지 않는다.

Structured Output 검증을 유지한다.

---

# 45. Agent 실행 Budget

무한 실행 방지를 위해 Run 단위 Budget을 둔다.

v0.1 권장값:

```text
max_plan_tests = 20
max_dynamic_tests = 5
max_verification_rounds_per_finding = 2
max_tool_retry = 1
max_planner_retry = 2
```

실제 구현 시 설정값으로 분리한다.

---

# 46. Web Agent Flow

```text
Web Assessment Request
        ↓
Scope / Safety Validation
        ↓
Web Observer
        ↓
Web TargetContext
        ↓
AI Planner
        ↓
Web TestPlan
        ↓
for each TestCase
        ↓
Tool Selector
        ↓
Web Tool
        ↓
HTTP Evidence
        ↓
Analyzer
        ↓
Candidate?
 ┌──────┴──────┐
No            Yes
│              ↓
│          Verifier
│              ↓
│       Additional Check?
│        ┌─────┴─────┐
│       Yes          No
│        ↓            ↓
│    Tool Selector   Finding
│
└──────────────→ Next Test
                     ↓
                  Report
```

---

# 47. Source Agent Flow

```text
Source Assessment Request
        ↓
Directory Validation
        ↓
Source Observer
        ↓
SourceContext
        ↓
AI Planner
        ↓
Source TestPlan
        ↓
for each TestCase
        ↓
Tool Selector
        ↓
Source Tool
        ↓
Code Evidence
        ↓
Analyzer
        ↓
Candidate?
 ┌──────┴──────┐
No            Yes
│              ↓
│          Verifier
│              ↓
│       Additional Context?
│        ┌─────┴─────┐
│       Yes          No
│        ↓            ↓
│      Tool          Finding
│
└──────────────→ Next Test
                     ↓
                  Report
```

---

# 48. Benchmark와의 Flow 분리

SecureProbe Agent Flow 내부에는 ZAP과 Semgrep이 존재하지 않는다.

```text
SecureProbe Agent Flow
        │
        └── SecureProbe Result

ZAP
        └── ZAP Result

Semgrep
        └── Semgrep Result
```

Evaluation 단계에서만 비교한다.

---

# 49. Ground Truth와의 Flow 분리

```text
Assessment 실행 중:
SecureProbe ──X── Ground Truth

Assessment 완료 후:
SecureProbe Result
       +
Ground Truth
       ↓
Evaluation
```

---

# 50. Manual Verification

자동 검증이 불충분한 Finding은 다음 상태로 Report한다.

```text
MANUAL_REQUIRED
```

사람이 확인한 이후에만:

```text
MANUAL_VERIFIED
```

로 변경할 수 있다.

자동 Assessment와 Human Validation 결과는 구분하여 기록한다.

---

# 51. Audit Trail

Agent Run은 최소 다음 이벤트를 기록한다.

```text
ASSESSMENT_CREATED
VALIDATION_COMPLETED
OBSERVATION_COMPLETED
PLAN_CREATED
TOOL_SELECTED
TOOL_EXECUTED
CANDIDATE_CREATED
VERIFICATION_REQUESTED
FINDING_CREATED
REPORT_CREATED
ASSESSMENT_COMPLETED
```

Portfolio에서는 이 Audit Trail을 이용해 Agent가 실제 판단과 Tool Calling을 수행했음을 보여줄 수 있다.

---

# 52. 권장 코드 책임 매핑

```text
secureprobe/agent/observer.py
→ Observe orchestration

secureprobe/agent/planner.py
→ Test Plan 생성

secureprobe/agent/selector.py
→ Tool 선택

secureprobe/agent/executor.py
→ Tool 실행 Wrapper

secureprobe/agent/analyzer.py
→ Tool 결과 분석

secureprobe/agent/verifier.py
→ 추가 검증 결정

secureprobe/core/safety.py
→ Safety Gate

secureprobe/core/registry.py
→ Tool Registry

secureprobe/report/generator.py
→ Report 생성
```

---

# 53. v0.1 완료 기준

Agent Flow 구현은 최소 다음이 재현되어야 한다.

```text
1. Target Context가 생성된다.
2. AI가 Structured TestPlan을 생성한다.
3. TestCase에 따라 Tool이 선택된다.
4. 실제 Tool이 실행된다.
5. Evidence가 저장된다.
6. AI가 Candidate Finding을 생성한다.
7. Verifier가 추가 검증 여부를 결정한다.
8. 필요 시 Tool을 한 번 더 실행한다.
9. Validation Status를 가진 Finding이 생성된다.
10. JSON/Markdown Report가 생성된다.
```

---

# 54. 다음 문서와의 관계

본 문서의 데이터 객체는 다음 문서에서 JSON Schema 수준으로 정의한다.

```text
docs/02_spec/DATA_SCHEMA_v0.1.md
```

구현 순서는 이후:

```text
docs/03_wbs/WBS_20DAYS_v0.1.md
```

에서 Task 단위로 분해한다.
