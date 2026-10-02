# D08-T02 — http_request Tool Implementation v0.1

## 1. 목적

SecureProbe AI Web Assessment에서 사용할 첫 번째 실제 HTTP Tool인
`http_request`를 구현한다.

이 Tool의 목적은 취약점 공격이 아니라
Web Observer 및 후속 Passive Tool이 사용할 수 있는
기본 HTTP Response Evidence를 안전하게 수집하는 것이다.

기본 흐름:

```text
AssessmentRequest
    ↓
Safety Gate (Passive Validation)
    ↓
http_request
    ↓
HTTP Response
    ↓
Structured ToolExecution / Output
```

이번 Task에서는 공격 Payload, 입력 변조, 인증 우회, SQLi/XSS 검증 등을 구현하지 않는다.

---

## 2. 작업 ID와 근거

- WBS 기준: Day 8, Task 02
- 작업 ID: `D08-T02`
- 작업명: `http_request`
- 우선순위: P0
- 선행 작업:
  - D08-T01 Safety Gate 완료
- 다음 작업:
  - D08-T03 — endpoint_collector

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. 핵심 원칙

`http_request`는 다음 원칙을 따른다.

```text
PASSIVE Tool
실제 HTTP 요청 수행
Safety Gate를 우회하지 않음
GET / HEAD 중심
요청 수 제한
Timeout 필수
Response Body 전체 무제한 저장 금지
민감 Header / Cookie 값 저장 최소화
Redirect 무제한 추적 금지
Redirect 대상 재검증
Shell / Browser 사용 금지
```

---

## 4. 구현 위치

권장 파일:

```text
secureprobe/web/tools/http_request.py
```

필요 시 수정:

```text
secureprobe/web/tools/__init__.py
```

Unit Test:

```text
tests/unit/test_http_request.py
```

Integration Test는 이번 Task에서 필수 아님.

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T02_HTTP_REQUEST_RESULT_v0.1.md
```

---

# 5. 기존 구성 재사용

다음 기존 요소를 재사용한다.

```text
AssessmentRequest
AssessmentScope
ToolExecution
ToolError
ExecutionStatus
validate_web_target
```

새로운 중복 Model을 만들지 않는다.

---

# 6. Tool Risk Level

`http_request`는 기본적으로:

```text
RiskLevel.PASSIVE
```

로 간주한다.

이번 Task에서는 ToolDefinition Registry 등록은 구현하지 않는다.

Tool Registry 연결은 Day 9에서 수행한다.

---

# 7. 허용 HTTP Method

v0.1 허용:

```text
GET
HEAD
```

이번 Task에서 차단:

```text
POST
PUT
PATCH
DELETE
OPTIONS
TRACE
CONNECT
```

이유:

```text
D08-T02는 Passive HTTP 수집용 Tool
상태 변경 가능 요청은 후속 Active Tool에서 별도 구현
```

---

# 8. Public API 권장안

권장 함수:

```python
async def http_request(
    *,
    assessment_request: AssessmentRequest,
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    follow_redirects: bool = False,
    timeout_seconds: float = 5.0,
    max_body_bytes: int = 65536,
    allowlist: set[str] | None = None,
) -> ToolExecution:
    ...
```

동기 방식도 가능하지만,
프로젝트에서 `httpx.AsyncClient`를 사용할 경우 async 방식을 권장한다.

한 Task 안에서 sync/async 두 방식을 모두 구현하지 않는다.

---

# 9. Safety Gate 연계

요청 전 반드시:

```python
validate_web_target(
    request,
    active=False,
    allowlist=allowlist,
)
```

와 동등한 Passive Validation을 수행한다.

Safety Gate 결과:

```text
allowed=False
```

이면 HTTP 요청을 보내지 않는다.

반환:

```text
ExecutionStatus.BLOCKED
```

을 사용한다.

---

# 10. Target URL 일치 정책

`assessment_request.target_url`와 실제 `url`은
동일 Assessment Target 범위 안이어야 한다.

최소 정책:

```text
최초 요청 URL의 Host
==
assessment_request.target_url의 Host
```

또는:

```text
request.scope.allowed_hosts
```

에 명시된 Host.

단, `scope.allowed_hosts` 자체가 Authorization 증명은 아니다.

역할:

```text
Safety Gate → 해당 Host를 요청해도 되는지 판단
Scope       → Assessment 내부에서 어디까지 요청할지 제한
```

두 책임을 구분한다.

---

# 11. Scope Host 정책

권장:

```text
target_url host가 기본 Assessment Host
```

추가 Host 요청은:

```text
AssessmentScope.allowed_hosts
```

에 포함되어 있어야 한다.

예:

```text
assessment target:
http://localhost:5000

allowed_hosts:
["localhost"]
```

허용.

다음은 임의 확장 금지:

```text
target:
localhost

actual request:
example.com
```

---

# 12. URL 검증

각 요청 URL은 다음을 만족해야 한다.

```text
http / https
userinfo 없음
hostname 존재
malformed URL 아님
```

가능하면 Safety Gate의 기존 parsing/canonicalization 정책을 재사용한다.

동일 보안 로직을 복사하여 중복 구현하지 않는다.

---

# 13. Redirect 기본 정책

기본:

```text
follow_redirects=False
```

로 한다.

자동 무제한 Redirect는 금지한다.

---

# 14. Redirect 허용 시 정책

`follow_redirects=True`를 지원한다면
httpx의 무제한 자동 redirect를 그대로 사용하지 않는다.

권장:

```text
max_redirects = 3
```

각 Redirect마다:

```text
Location URL 파싱
↓
Safety Gate Passive Validation
↓
Scope Host Validation
↓
허용 시 다음 요청
```

을 수행한다.

---

# 15. Redirect Host Escape 차단

다음 예:

```text
http://localhost
→ 302 Location: https://example.com
```

Scope/Allowlist에 허용되지 않은 Host라면
Redirect를 따라가지 않는다.

반환은:

```text
BLOCKED
또는
현재 Response까지만 SUCCESS + redirect metadata
```

중 하나로 일관되게 선택한다.

권장:

```text
BLOCKED
```

그리고 ToolError code:

```text
REDIRECT_OUT_OF_SCOPE
```

---

# 16. Redirect Loop 방지

Redirect 추적 시:

```text
최대 3회
```

를 기본값으로 한다.

초과:

```text
ExecutionStatus.FAILED
ToolError.code = "TOO_MANY_REDIRECTS"
```

---

# 17. Timeout

기본:

```text
5초
```

권장 허용 범위:

```text
0.1 ~ 30초
```

30초 초과 timeout을 입력하면
Validation 또는 내부 Clamp 중 하나를 선택한다.

권장:

```text
ValueError / ValidationError 성격의 명확한 실패
```

숨겨서 무제한 대기하지 않는다.

---

# 18. Response Body 크기 제한

Response 전체를 무제한 메모리에 저장하지 않는다.

기본:

```text
max_body_bytes = 65536
```

즉:

```text
64 KiB
```

정도만 Evidence/Output용으로 보관한다.

---

# 19. Response Body 정책

Output에는 다음 정도만 유지한다.

```text
body_excerpt
body_truncated
content_length
```

예:

```json
{
  "body_excerpt": "<html>...</html>",
  "body_truncated": true,
  "content_length": 125000
}
```

전체 Body 저장은 이번 Task 범위가 아니다.

---

# 20. Binary Response

다음과 같은 Binary Content는
본문 전체 decode를 시도하지 않는다.

예:

```text
application/octet-stream
image/*
video/*
audio/*
application/pdf
```

권장:

```text
body_excerpt = null
또는 안전한 짧은 binary metadata
```

이번 Task에서는 파일 저장을 하지 않는다.

---

# 21. Text Decode

Text Response는 다음 기준으로 처리한다.

```text
httpx response.text
```

또는 안전한 encoding 처리.

Decode 오류가 발생해도 Tool 전체가 crash하지 않도록 한다.

---

# 22. Output Schema

이번 Task에서는 DATA_SCHEMA의 HttpResponseOutput 예를 따른다.

최소 Output:

```text
status_code
headers
content_type
body_excerpt
elapsed_ms
```

추가 권장:

```text
final_url
redirect_chain
body_truncated
content_length
```

---

# 23. 별도 Pydantic Output Model

필요하면 다음 파일 내부에 최소 Model을 정의할 수 있다.

```text
secureprobe/web/tools/http_request.py
```

예:

```python
class HttpResponseOutput(BaseModel):
    status_code: int
    headers: dict[str, str]
    content_type: str | None
    body_excerpt: str | None
    elapsed_ms: int
    final_url: str
    redirect_chain: list[str]
    body_truncated: bool
    content_length: int | None
```

하지만 이번 Task에서 불필요하게
전체 Tool Model 패키지를 새로 만들지 않는다.

---

# 24. ToolExecution 사용

실행 결과는 기존:

```text
ToolExecution
```

Model을 사용한다.

예:

```text
execution_id
test_id
tool_name
input
status
started_at
finished_at
duration_ms
output
error
```

---

# 25. execution_id

자동 생성 가능.

예:

```text
EXEC-<uuid>
```

또는 내부 UUID 기반 문자열.

이번 Task에서 ID 포맷을 지나치게 복잡하게 만들지 않는다.

---

# 26. test_id

호출자가 제공할 수 있도록 하는 것을 권장한다.

Public API에:

```python
test_id: str
```

를 추가해도 된다.

기본값 자동 생성도 가능하지만
Agent Flow와 Traceability를 위해 호출자 전달을 권장한다.

---

# 27. Tool Name

고정:

```text
http_request
```

---

# 28. Request Header 정책

Caller가 제한된 Header를 전달할 수 있다.

허용 예:

```text
Accept
Accept-Language
User-Agent
Referer
If-None-Match
If-Modified-Since
```

이번 v0.1에서는 Header Allowlist를 너무 크게 만들지 않는다.

---

# 29. 민감 Request Header

다음 Header를 사용자가 직접 raw 값으로 전달하는 구조는 기본 금지한다.

```text
Authorization
Proxy-Authorization
Cookie
Set-Cookie
X-Api-Key
API-Key
```

인증 Session은 후속 인증 처리 Task에서
런타임 Secret/Session 관리와 함께 구현한다.

---

# 30. Default User-Agent

권장:

```text
SecureProbeAI/0.1
```

처럼 Tool 식별 가능한 값을 사용한다.

브라우저 위장 User-Agent를 기본값으로 사용하지 않는다.

---

# 31. Response Header 저장 정책

Response Header는 Structured Output에 포함 가능하다.

단 다음 민감 Header 값은 Masking 또는 제외한다.

예:

```text
Set-Cookie
Authorization
Proxy-Authorization
WWW-Authenticate
```

특히 `Set-Cookie` 전체 raw 값 저장은 피한다.

이번 Task에서는:

```text
Set-Cookie 값 → "***MASKED***"
```

정도면 충분하다.

---

# 32. Header Canonicalization

Output Header key는
httpx에서 제공하는 문자열 값을 그대로 사용해도 된다.

대소문자 표준화를 과도하게 구현하지 않는다.

---

# 33. Cookie 정책

이번 Tool은 Cookie Jar 기반 인증 Session을 구현하지 않는다.

즉:

```text
persistent cookie session 없음
```

Cookie Attribute 분석은:

```text
D08-T06 — cookie_inspector
```

에서 수행한다.

---

# 34. TLS 정책

기본:

```text
verify=True
```

로 한다.

`verify=False` 옵션을 Public API로 노출하지 않는다.

테스트 환경에서 자체서명 인증서가 필요해도
이번 Task에서는 TLS 검증 비활성화를 추가하지 않는다.

---

# 35. Proxy 정책

환경 Proxy 자동 사용 여부는 명시적으로 통제한다.

권장:

```python
trust_env=False
```

를 사용한다.

이유:

```text
예상치 못한 시스템 Proxy 경유 방지
재현성
```

---

# 36. HTTP Client 설정 권장

예:

```python
httpx.AsyncClient(
    timeout=timeout_seconds,
    follow_redirects=False,
    trust_env=False,
)
```

Redirect는 직접 처리하는 것을 권장한다.

---

# 37. Connection Limits

v0.1에서는 단일 요청 중심이므로
복잡한 Connection Pool 설정은 필요 없다.

병렬 스캐너 구현 금지.

---

# 38. Retry 정책

이번 Task에서는 자동 Retry를 구현하지 않는다.

이유:

```text
Agent / Tool retry 정책은 별도 상위 계층에서 관리
AGENT_FLOW의 max_tool_retry와 책임 분리
```

Timeout/Network Error는 그대로 ToolExecution에 기록한다.

---

# 39. Error Mapping

최소 다음 Error를 구조화한다.

```text
SAFETY_BLOCKED
METHOD_NOT_ALLOWED
TIMEOUT
NETWORK_ERROR
INVALID_URL
REDIRECT_OUT_OF_SCOPE
TOO_MANY_REDIRECTS
RESPONSE_TOO_LARGE
```

실제 사용하는 subset만 구현 가능.

---

# 40. Timeout Error

httpx timeout:

```text
ExecutionStatus.TIMEOUT
```

ToolError:

```text
code = "HTTP_TIMEOUT"
retryable = True
```

---

# 41. Network Error

연결 실패/DNS 실패 등:

```text
ExecutionStatus.FAILED
```

ToolError:

```text
code = "NETWORK_ERROR"
retryable = True
```

이번 Tool 내부에서 DNS를 직접 수행하지 않지만,
httpx가 실제 연결 시 resolver를 사용할 수 있음은 정상이다.

중요:

```text
Safety Gate 자체는 DNS I/O 없음
http_request는 실제 HTTP Tool이므로 네트워크 I/O 있음
```

---

# 42. Invalid Method

허용하지 않는 Method 입력:

```text
POST
DELETE
...
```

이면 실제 HTTP 요청을 보내지 않는다.

반환:

```text
ExecutionStatus.BLOCKED
```

또는 명확한 입력 오류.

권장 ToolError:

```text
METHOD_NOT_ALLOWED
```

---

# 43. Safety Block

Safety Gate 실패:

```text
ExecutionStatus.BLOCKED
```

ToolError:

```text
code="SAFETY_BLOCKED"
retryable=False
```

---

# 44. No Ground Truth

Tool input/output에 다음 정보 포함 금지:

```text
ground_truth_id
known_vulnerability
expected_ground_truth
zap_result
semgrep_result
benchmark_result
```

---

# 45. No Vulnerability Judgment

`http_request` 자체가 다음 판단을 하지 않는다.

```text
취약함
SQL Injection
XSS
Security Misconfiguration
```

이 Tool은 HTTP Evidence 수집만 한다.

취약점 판단은 Analyzer 단계 책임이다.

---

# 46. Unit Test 원칙

실제 인터넷 사이트를 Unit Test에서 호출하지 않는다.

다음 방식 사용:

```text
httpx.MockTransport
```

또는 동등한 로컬 Mock.

Unit Test는 deterministic 해야 한다.

---

# 47. MockTransport 권장

가능하면 `httpx.MockTransport`를 사용한다.

새 dependency를 추가하지 않는다.

---

# 48. Unit Test — GET Success

Mock:

```text
200 OK
Content-Type: text/html
body: <html>hello</html>
```

검증:

```text
ExecutionStatus.SUCCESS
status_code=200
body_excerpt 포함
elapsed_ms >= 0
```

---

# 49. Unit Test — HEAD Success

HEAD 요청 성공 검증.

Body 저장하지 않아도 됨.

---

# 50. Unit Test — Unsupported Method

```text
POST
DELETE
```

입력 시 MockTransport가 호출되지 않아야 한다.

검증:

```text
BLOCKED / METHOD_NOT_ALLOWED
```

---

# 51. Unit Test — Safety Block

외부 Target + Active 관련 우회는 이번 Tool이 Passive Gate를 호출하므로
중요한 것은 invalid/malformed target이 실제 Transport까지 도달하지 않는 것이다.

또한 Assessment target Host와 실제 url Host가 다르면
Scope 정책으로 차단한다.

---

# 52. Unit Test — Out-of-Scope Host

Assessment:

```text
target_url=http://localhost
```

Tool 요청:

```text
https://example.com
```

결과:

```text
BLOCKED
```

MockTransport 호출 없음.

---

# 53. Unit Test — allowed_hosts

Assessment Target:

```text
http://localhost
```

Scope:

```text
allowed_hosts=["secureboard.local"]
```

Allowlist에도:

```text
secureboard.local
```

이 명시된 경우에만
추가 Host 요청을 허용하도록 한다.

Scope만으로 Authorization을 부여하면 안 된다.

---

# 54. Unit Test — Timeout

MockTransport로 직접 Timeout 예외를 발생시키거나
동등하게 시뮬레이션한다.

검증:

```text
ExecutionStatus.TIMEOUT
ToolError.code == "HTTP_TIMEOUT"
```

---

# 55. Unit Test — Network Error

Mock:

```text
httpx.ConnectError
```

검증:

```text
ExecutionStatus.FAILED
ToolError.code == "NETWORK_ERROR"
```

---

# 56. Unit Test — Body Truncation

64 KiB보다 큰 Text Body Mock.

검증:

```text
body_excerpt 길이 제한
body_truncated=True
```

전체 Body를 output에 저장하지 않음.

---

# 57. Unit Test — Binary Response

예:

```text
Content-Type: application/octet-stream
```

검증:

```text
body_excerpt 없음 또는 제한된 안전 표현
Tool crash 없음
```

---

# 58. Unit Test — Header Masking

Mock Response:

```text
Set-Cookie: session=super-secret
```

Output:

```text
session=super-secret
```

값이 그대로 존재하면 안 된다.

예:

```text
Set-Cookie: ***MASKED***
```

---

# 59. Unit Test — Redirect Disabled

302 응답.

기본:

```text
follow_redirects=False
```

이면:

```text
302 Response 반환
```

하고 두 번째 요청 없음.

---

# 60. Unit Test — Redirect In Scope

follow_redirects=True.

```text
localhost/a
→ localhost/b
```

최대 redirect 정책 내에서 허용.

---

# 61. Unit Test — Redirect Out of Scope

```text
localhost
→ example.com
```

결과:

```text
BLOCKED
REDIRECT_OUT_OF_SCOPE
```

두 번째 외부 요청이 실행되지 않아야 한다.

---

# 62. Unit Test — Redirect Loop

Mock:

```text
/a → /b
/b → /a
```

redirect limit 초과 시:

```text
FAILED
TOO_MANY_REDIRECTS
```

---

# 63. Query / Fragment

Query는 실제 요청에 포함 가능.

Fragment는 HTTP 요청에 전송되지 않는 것이 정상이다.

추가로 복잡한 Fragment 처리를 구현하지 않는다.

---

# 64. Input Mutation 금지

이번 Tool은 User Input을 자동 변형하지 않는다.

금지:

```text
' OR '1'='1
<script>
../
payload generation
parameter fuzzing
```

---

# 65. Request Count

단일 Tool 호출 당:

```text
기본 1 request
redirect 포함 최대 4 request
```

권장.

Crawler가 아니다.

---

# 66. Logging

Raw Authorization/Cookie/Secret 값을 로그에 기록하지 않는다.

이번 Task에서 별도 Logging Framework 추가 금지.

---

# 67. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T02_HTTP_REQUEST_RESULT_v0.1.md
```

---

# 68. Result Document 필수 내용

```text
Task ID
Status
Public API
Created Files
Modified Files
Allowed Methods
Safety Gate Integration
Scope Host Policy
Redirect Policy
Timeout Policy
Body Limit
Header Masking
TLS Policy
Proxy Policy
Network I/O
Unit Test Result
Full Regression Result
Import Validation
Issues
Next Task
```

---

# 69. 개별 Test 실행

```bash
pytest tests/unit/test_http_request.py -q
```

PASS해야 한다.

---

# 70. 전체 Regression

```bash
pytest -q
```

현재 기준 Full Regression:

```text
212 passed
```

새 Test 추가 후 실제 결과를 기록한다.

기존 숫자를 복사하지 않는다.

---

# 71. Import Test

실제 API에 맞게:

```bash
python -c "from secureprobe.web.tools.http_request import http_request; print('IMPORT_OK')"
```

PASS.

---

# 72. 변경 가능 파일

```text
secureprobe/web/tools/http_request.py
secureprobe/web/tools/__init__.py

tests/unit/test_http_request.py

docs/05_ai_development/codex_results/day08/
D08-T02_HTTP_REQUEST_RESULT_v0.1.md
```

`__init__.py` 수정은 필요한 경우에만.

---

# 73. 수정 금지

```text
secureprobe/core/safety.py
secureprobe/models/*
secureprobe/agent/*
secureprobe/source/*
secureprobe/report/*

secureboard/*

PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

Safety Gate 결함을 발견하면 이번 Task에서 임의 수정하지 않고 Issues에 기록한다.

---

# 74. Dependency 정책

현재:

```text
httpx==0.28.1
```

이 이미 requirements에 존재한다.

새 dependency를 추가하지 않는다.

---

# 75. 완료 체크리스트

```text
[ ] http_request.py 생성
[ ] GET 지원
[ ] HEAD 지원
[ ] POST/PUT/PATCH/DELETE 차단

[ ] Safety Gate Passive Validation 연계
[ ] Assessment Host Scope 검증
[ ] allowed_hosts와 authorization 책임 분리

[ ] timeout 적용
[ ] max body size 적용
[ ] binary response 안전 처리
[ ] response header masking
[ ] verify=True
[ ] trust_env=False

[ ] redirect 기본 비활성
[ ] redirect limit
[ ] redirect target 재검증
[ ] redirect out-of-scope 차단

[ ] Timeout Error 구조화
[ ] Network Error 구조화
[ ] Safety Block 구조화

[ ] Ground Truth 정보 없음
[ ] Benchmark 정보 없음
[ ] 취약점 판단 없음
[ ] Payload mutation 없음

[ ] MockTransport Unit Test
[ ] GET PASS
[ ] HEAD PASS
[ ] Unsupported Method PASS
[ ] Scope Block PASS
[ ] Timeout PASS
[ ] Network Error PASS
[ ] Body Truncation PASS
[ ] Binary Response PASS
[ ] Header Masking PASS
[ ] Redirect Tests PASS

[ ] 개별 pytest PASS
[ ] Full pytest PASS
[ ] Import PASS
[ ] Result Document 생성
```

---

# 76. 완료 조건

다음 조건을 모두 만족하면 D08-T02 완료다.

```text
Passive HTTP GET/HEAD Tool 실행 가능
Safety Gate 우회 없음
Assessment Scope 밖 Host 요청 차단
무제한 Redirect 없음
Redirect 재검증
Timeout 있음
Response Body 제한 있음
민감 Header Masking
TLS Verification 활성
환경 Proxy 비사용
Structured ToolExecution 반환
Unit Test PASS
전체 Regression PASS
범위 확대 없음
```

---

# 77. 권장 Commit Message

```text
feat: add passive http request tool
```

사용 금지:

```text
git commit --amend
git push --force
```

---

# 78. 완료 보고 형식

```text
D08-T02 HTTP REQUEST

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- GET
- HEAD
- Safety Gate integration
- Scope validation
- timeout
- response body limit
- header masking
- controlled redirects
- structured errors

Validation:
- GET: PASS / FAIL
- HEAD: PASS / FAIL
- Unsupported Method: PASS / FAIL
- Safety Gate: PASS / FAIL
- Scope Host: PASS / FAIL
- Timeout: PASS / FAIL
- Network Error: PASS / FAIL
- Body Limit: PASS / FAIL
- Binary Response: PASS / FAIL
- Header Masking: PASS / FAIL
- Redirect Disabled: PASS / FAIL
- Redirect In-Scope: PASS / FAIL
- Redirect Out-of-Scope: PASS / FAIL
- Redirect Limit: PASS / FAIL
- TLS Verify: PASS / FAIL
- trust_env=False: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T02_HTTP_REQUEST_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T03 — endpoint_collector
```

---

# 79. 작업 종료 원칙

D08-T02 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T03 — endpoint_collector
```

SecureBoard가 Claude에서 전달되면
Mock 기반 Unit Test와 별도로 실제 Lab Integration Test를 수행한다.
