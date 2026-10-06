# D08-T07 — WebTargetContext Implementation v0.1

## 1. 목적

Day 8에서 구현한 Web Passive Tool들을 연결하여
URL 기반 관찰 결과를 하나의 `WebTargetContext`로 구조화한다.

Day 8 목표:

```text
URL
 ↓
Safety Gate
 ↓
http_request
 ↓
endpoint_collector
form_parser
header_inspector
cookie_inspector
 ↓
WebTargetContext
```

이번 Task는 **새로운 Scanner를 구현하는 작업이 아니다.**

기존 Passive Tool의 결과를 조립하여
Day 9 Planner가 사용할 Target Context를 만드는 것이 목적이다.

---

## 2. 작업 ID

```text
D08-T07 — WebTargetContext 생성
```

선행 작업:

```text
D08-T01 Safety Gate             COMPLETED
D08-T02 http_request            COMPLETED
D08-T03 endpoint_collector      COMPLETED
D08-T04 form_parser             COMPLETED
D08-T05 header_inspector        COMPLETED
D08-T06 cookie_inspector        COMPLETED
D08-T06A Cookie Pipeline Bridge COMPLETED
```

다음 작업:

```text
D09-T01 — Tool Registry
```

본 Task 완료 시:

```text
DAY 8 — Web Observer / Passive Tools
```

종료 여부를 판단할 수 있어야 한다.

---

## 3. 기준 문서

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

기존 구현:

```text
secureprobe/core/safety.py

secureprobe/web/tools/http_request.py
secureprobe/web/tools/endpoint_collector.py
secureprobe/web/tools/form_parser.py
secureprobe/web/tools/header_inspector.py
secureprobe/web/tools/cookie_inspector.py

secureprobe/models/assessment.py
secureprobe/models/target.py
secureprobe/models/tool.py
```

---

# 4. DATA_SCHEMA 기준

`DATA_SCHEMA_v0.1.md`의 WebTargetContext:

```json
{
  "context_id": "CTX-WEB-0001",
  "base_url": "http://localhost:8080",
  "endpoints": [],
  "forms": [],
  "headers": {},
  "cookies": [],
  "authentication_detected": true,
  "session_detected": true,
  "content_types": [
    "text/html"
  ]
}
```

이번 Task는 이 구조를 실제 Pydantic Model과 Observer 흐름으로 구현한다.

---

# 5. WebTargetContext Model

`secureprobe/models/target.py`에 추가한다.

권장:

```python
class WebTargetContext(BaseModel):
    context_id: str
    base_url: str

    endpoints: list[Endpoint] = Field(default_factory=list)
    forms: list[Form] = Field(default_factory=list)

    headers: dict[str, str | None] = Field(default_factory=dict)
    cookies: list[CookieInfo] = Field(default_factory=list)

    authentication_detected: bool = False
    session_detected: bool = False

    content_types: list[str] = Field(default_factory=list)
```

정책:

```text
extra="forbid"
str_strip_whitespace=True
mutable default isolation
```

---

# 6. Headers Field 정책

`WebTargetContext.headers`에는
D08-T05 `header_inspector`가 관찰한 8개 Security Header만 저장한다.

예:

```json
{
  "Content-Security-Policy": null,
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": null,
  "Permissions-Policy": null,
  "Strict-Transport-Security": null,
  "Cache-Control": "no-store",
  "Pragma": null
}
```

정책:

```text
present=True  → 안전하게 정리된 value
present=False → null
```

Raw Response Header 전체를 WebTargetContext에 복사하지 않는다.

---

# 7. Cookie 정책

`WebTargetContext.cookies`에는:

```text
CookieInfo
```

만 저장한다.

다음 저장 금지:

```text
Cookie Value
Raw Set-Cookie
Cookie Header
Session Token
```

D08-T06A에서 생성된:

```text
ToolExecution.output["cookies"]
```

를 `CookieInfo`로 Validation하여 사용한다.

---

# 8. Base URL 정책

`base_url`은 실제 관찰한 최종 Response URL을 사용한다.

우선순위:

```text
http_request.output["final_url"]
```

즉 Redirect가 있었다면:

```text
요청 URL:
http://localhost

최종 URL:
http://localhost/home
```

WebTargetContext:

```text
base_url=http://localhost/home
```

원래 요청 URL은 `AssessmentRequest`에 이미 존재하므로
Context에 중복 필드를 추가하지 않는다.

---

# 9. Content-Type 정책

`http_request.output["content_type"]`에서
MIME Type만 정규화한다.

예:

```text
text/html; charset=utf-8
→ text/html
```

```text
application/json; charset=utf-8
→ application/json
```

정책:

```text
lowercase
공백 제거
중복 제거
```

현재 최초 Response 관찰은 1개이므로:

```text
content_types=[]
```

또는:

```text
content_types=["text/html"]
```

형태가 된다.

---

# 10. HTML Parser 실행 조건

다음일 때만:

```text
Content-Type == text/html
```

Endpoint / Form Parser를 실행한다.

즉:

```text
collect_endpoints(...)
parse_forms(...)
```

호출.

다음에서는 실행하지 않는다.

```text
application/json
application/pdf
image/*
application/octet-stream
text/plain
```

---

# 11. Body 정책

`http_request`의:

```text
body_excerpt
```

만 Parser 입력으로 사용한다.

WebTargetContext 자체에는 HTML Body를 저장하지 않는다.

즉:

```text
body
body_excerpt
raw_html
response_body
```

필드를 WebTargetContext에 추가하지 않는다.

---

# 12. Truncated HTML 정책

`body_truncated=True`인 HTML도
BeautifulSoup 기반 Parser에 best-effort로 전달할 수 있다.

이번 v0.1에서는:

```text
부분 HTML → 가능한 범위에서 Endpoint/Form 추출
```

로 처리한다.

WebTargetContext Schema에 별도 Warning 필드는 추가하지 않는다.

Result Document에 이 제한사항을 기록한다.

---

# 13. Endpoint 생성

HTML Response의 경우:

```python
collect_endpoints(
    base_url=final_url,
    html=body_excerpt,
    scope=assessment_request.scope,
)
```

결과를 그대로:

```text
WebTargetContext.endpoints
```

에 저장한다.

새 Endpoint parsing logic을 Observer에 복사하지 않는다.

---

# 14. Form 생성

HTML Response의 경우:

```python
parse_forms(
    base_url=final_url,
    html=body_excerpt,
    scope=assessment_request.scope,
)
```

결과를:

```text
WebTargetContext.forms
```

에 저장한다.

새 Form Parser를 Observer에 구현하지 않는다.

---

# 15. Header 생성

D08-T05:

```python
inspect_headers(
    url=final_url,
    headers=http_output["headers"],
)
```

를 재사용한다.

반환된 `HeaderInspectionResult.observations`를
Context의 단순 dict로 변환한다.

예:

```python
headers = {
    observation.name: observation.value if observation.present else None
    for observation in result.observations
}
```

---

# 16. Cookie 생성

D08-T06A의:

```text
http_output["cookies"]
```

를 사용한다.

각 item:

```python
CookieInfo.model_validate(item)
```

로 검증한다.

잘못된 Cookie Metadata가 들어오면
조용히 추측하여 수정하지 않는다.

명확히 Context 생성 실패로 처리한다.

---

# 17. authentication_detected 정책

이번 v0.1에서는 deterministic하고 보수적인 기준만 사용한다.

다음 조건이면:

```text
authentication_detected=True
```

```text
Form 중 하나에:
type == "password"
Field가 존재
```

그 외:

```text
False
```

경로 이름:

```text
/login
/auth
/signin
```

만 보고 Authentication이라고 추측하지 않는다.

---

# 18. session_detected 정책

이번 v0.1에서는 Cookie Name을 기준으로
제한된 heuristic을 사용한다.

다음 이름을 case-insensitive exact match로 확인한다.

```text
session
sessionid
jsessionid
phpsessid
connect.sid
```

하나라도 존재:

```text
session_detected=True
```

그 외:

```text
False
```

다음은 하지 않는다.

```text
모든 Cookie를 Session으로 간주
Cookie Value 분석
Token 내용 분석
JWT 분석
```

이 값은 취약점 판단이 아니라
Observer용 Context Hint다.

---

# 19. Context ID

권장:

```text
CTX-WEB-<uuid>
```

예:

```python
f"CTX-WEB-{uuid4().hex}"
```

Stable Prefix만 보장하면 된다.

순번 관리 시스템은 구현하지 않는다.

---

# 20. Observer 위치

생성:

```text
secureprobe/web/observer.py
```

---

# 21. Public API

권장:

```python
async def observe_web_target(
    *,
    assessment_request: AssessmentRequest,
    test_id: str = "OBSERVE-WEB-001",
    allowlist: set[str] | None = None,
) -> WebTargetContext:
    ...
```

---

# 22. Observer 기본 흐름

```text
AssessmentRequest
       ↓
assessment_type == WEB 확인
       ↓
http_request
       ↓
ExecutionStatus.SUCCESS 확인
       ↓
final_url
headers
cookies
content_type
body_excerpt
       ↓
HTML이면:
endpoint_collector
form_parser
       ↓
header_inspector
       ↓
Authentication/Session Hint
       ↓
WebTargetContext
```

---

# 23. http_request 호출 정책

Observer의 최초 관찰 요청:

```text
method=GET
follow_redirects=True
```

권장.

이유:

```text
실제 Landing Page 관찰
Redirect Scope/Safety 정책은 D08-T02가 이미 통제
```

호출 예:

```python
execution = await http_request(
    assessment_request=assessment_request,
    url=assessment_request.target_url,
    test_id=test_id,
    method="GET",
    follow_redirects=True,
    allowlist=allowlist,
)
```

---

# 24. Safety Gate 재구현 금지

Observer에서 Safety Gate logic을 복사하지 않는다.

실제 HTTP 요청 허용 여부는:

```text
http_request
→ validate_web_target
```

기존 흐름을 사용한다.

---

# 25. HTTP 실패 처리

다음 상태에서는 Context를 만들지 않는다.

```text
FAILED
TIMEOUT
BLOCKED
UNSUPPORTED
```

이번 Task에서는 새 Error Model을 만들지 않는다.

권장:

```python
raise RuntimeError(
    f"web observation failed: {execution.error.code}"
)
```

단:

```text
Raw network exception
Cookie secret
Header secret
Response Body
```

를 error message에 넣지 않는다.

---

# 26. Invalid Tool Output 처리

다음 필수 Output이 없거나 type이 잘못된 경우
조용히 기본값으로 추측하지 않는다.

필수 최소:

```text
final_url
headers
cookies
content_type
body_excerpt
```

단:

```text
body_excerpt=None
content_type=None
```

은 정상적으로 처리할 수 있다.

필드 자체 누락과 `None`은 구분한다.

---

# 27. JSON / Non-HTML Response

예:

```text
application/json
```

이면 Context는 생성한다.

```text
endpoints=[]
forms=[]
headers=<8개 observation map>
cookies=<metadata>
content_types=["application/json"]
```

즉 HTML이 아니라고 Context 생성 자체를 실패시키지 않는다.

---

# 28. Empty HTML

HTML body가:

```text
""
```

인 경우:

```text
endpoint_collector
→ current Endpoint 생성 가능

form_parser
→ []
```

기존 Tool 정책을 그대로 따른다.

---

# 29. Raw Sensitive Data 금지

WebTargetContext에 다음이 존재하면 안 된다.

```text
Raw Cookie Value
Raw Set-Cookie
Authorization Header
Proxy-Authorization
API Key
Raw Password
Credential Secret
```

---

# 30. Ground Truth Leakage 금지

WebTargetContext에 다음 필드 금지:

```text
ground_truth_id
known_vulnerability
expected_ground_truth
expected_finding
```

---

# 31. Benchmark Leakage 금지

금지:

```text
zap_result
semgrep_result
benchmark_result
benchmark_finding
```

---

# 32. Vulnerability Judgment 금지

Observer 단계에서 다음 생성 금지:

```text
SQL Injection
XSS
IDOR
Missing Security Header Finding
Weak Cookie Finding
Severity
OWASP
CWE
CandidateFinding
Finding
```

Context는 관찰 데이터만 담는다.

---

# 33. LLM 사용 금지

이번 Task에서 OpenAI API를 호출하지 않는다.

```text
Planner
```

는 Day 9에서 구현한다.

Observer는 deterministic Tool orchestration만 수행한다.

---

# 34. Network 범위

새 네트워크 코드 작성 금지.

네트워크 I/O는 오직 기존:

```text
http_request
```

를 통해서만 수행한다.

Observer가 직접:

```text
httpx
requests
socket
```

을 사용하면 안 된다.

---

# 35. Recursive Crawl 금지

이번 Observer는 최초 URL 1개를 관찰한다.

금지:

```text
endpoint 수집
→ 자동으로 모든 endpoint HTTP 요청
→ 다시 endpoint 수집
```

즉:

```text
1 URL
→ 1 HTTP observation
→ Context
```

이다.

---

# 36. Tool Registry 연결 금지

Tool Registry는:

```text
D09-T01
```

에서 구현한다.

이번 Observer가 Registry를 만들거나
Planner/Selector를 흉내 내지 않는다.

---

# 37. Unit Test 파일

생성:

```text
tests/unit/test_web_observer.py
```

실제 인터넷은 호출하지 않는다.

`http_request`를 monkeypatch/mock하여
Structured ToolExecution을 반환한다.

---

# 38. Unit Test Helper

Mock ToolExecution은 기존 Model을 사용한다.

예:

```text
ExecutionStatus.SUCCESS
tool_name=http_request
output={
  status_code,
  headers,
  cookies,
  content_type,
  body_excerpt,
  body_truncated,
  final_url,
  redirect_chain
}
```

---

# 39. Unit Test — HTML Context

Mock:

```text
final_url=http://localhost/home
content_type=text/html; charset=utf-8

body:
<a href="/login">Login</a>
<form action="/login" method="post">
  <input name="username">
  <input name="password" type="password">
</form>
```

검증:

```text
base_url=http://localhost/home
content_types=["text/html"]
endpoints 존재
forms 존재
authentication_detected=True
```

---

# 40. Unit Test — Header Context

Mock Header:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

Context:

```text
headers["X-Content-Type-Options"] == "nosniff"
headers["X-Frame-Options"] == "DENY"
headers["Content-Security-Policy"] is None
```

8개 Header key가 deterministic하게 존재하는 것을 권장한다.

---

# 41. Unit Test — Cookie Context

Mock Output:

```json
{
  "cookies": [
    {
      "name": "SESSION",
      "secure": true,
      "http_only": true,
      "same_site": "Lax",
      "domain": null,
      "path": "/",
      "max_age": null,
      "expires": null
    }
  ]
}
```

Context:

```text
CookieInfo로 Validation
Raw Value 없음
```

---

# 42. Unit Test — Session Detection

Cookie:

```text
SESSION
sessionid
JSESSIONID
PHPSESSID
connect.sid
```

각각:

```text
session_detected=True
```

다음:

```text
theme
language
analytics
```

→ False.

---

# 43. Unit Test — Authentication Detection

Password field 존재:

```text
True
```

Password field 없음:

```text
False
```

URL path가 `/login`이어도 password field가 없으면
자동으로 True 처리하지 않는다.

---

# 44. Unit Test — Non-HTML

Mock:

```text
content_type=application/json
body_excerpt={"status":"ok"}
```

검증:

```text
WebTargetContext 생성 성공
endpoints=[]
forms=[]
content_types=["application/json"]
```

---

# 45. Unit Test — Content-Type Normalization

검증:

```text
Text/HTML; Charset=UTF-8
→ text/html
```

중복 없음.

---

# 46. Unit Test — Redirect Final URL

Assessment Request:

```text
http://localhost
```

Mock final_url:

```text
http://localhost/home
```

Context:

```text
base_url=http://localhost/home
```

---

# 47. Unit Test — Truncated HTML

```text
body_truncated=True
```

이어도 Parser가 crash하지 않고
가능한 Context를 생성해야 한다.

---

# 48. Unit Test — Failed HTTP

각각:

```text
FAILED
TIMEOUT
BLOCKED
UNSUPPORTED
```

Context를 생성하지 않는다.

Secret 없는 명확한 RuntimeError 또는
선택한 오류 정책으로 종료한다.

---

# 49. Unit Test — Invalid Cookie Metadata

예:

```json
{
  "name": "SESSION",
  "secure": "yes"
}
```

Pydantic Validation 실패.

Observer가 임의로:

```text
"yes" → True
```

같이 수정하면 안 된다.

---

# 50. Unit Test — Invalid Output Contract

예:

```text
headers field missing
cookies field missing
final_url missing
```

명확하게 실패.

---

# 51. Unit Test — Sensitive Data Non-Retention

Mock HTTP Tool 내부 데이터에 다음과 같은 Secret 문자열을 사용하더라도
Context 결과에는 없어야 한다.

```text
super-secret-cookie
private-token
raw-password
```

단 Mock output에는 애초에 raw Cookie를 넣지 않는 것이 원칙이다.

WebTargetContext JSON에 민감 필드 이름도 없어야 한다.

---

# 52. Unit Test — No Ground Truth / Benchmark Fields

다음 주입 시 Model에서 거부:

```text
ground_truth_id
known_vulnerability
zap_result
semgrep_result
benchmark_result
```

---

# 53. Unit Test — Mutable Default Isolation

두 WebTargetContext instance 사이:

```text
endpoints
forms
headers
cookies
content_types
```

가 공유되지 않아야 한다.

---

# 54. Unit Test — JSON Round-trip

```python
payload = context.model_dump(mode="json")
restored = WebTargetContext.model_validate(payload)
```

PASS.

---

# 55. Unit Test — Context ID

검증:

```text
context_id.startswith("CTX-WEB-")
```

빈 값 금지.

정확한 UUID 값 자체를 고정 비교하지 않는다.

---

# 56. Unit Test — Request Mutation 금지

`observe_web_target()` 실행 전/후:

```text
assessment_request.model_dump()
```

가 동일해야 한다.

---

# 57. Unit Test — http_request 호출 계약

Mock을 이용하여 확인:

```text
method == GET
follow_redirects == True
url == assessment_request.target_url
allowlist 그대로 전달
```

---

# 58. Unit Test — No Direct Network Client

`secureprobe/web/observer.py`에서 다음 import 금지:

```text
httpx
requests
socket
```

네트워크는 `http_request`만 담당한다.

---

# 59. Model Validation

`WebTargetContext` 최소 검증:

```text
context_id non-empty
base_url non-empty
authentication_detected strict bool
session_detected strict bool
extra forbid
```

필요 시 base_url 자체의 URL validation은
Observer 생성 과정에서 기존 Safety Gate가 보장하므로
Model validator를 과도하게 추가하지 않는다.

---

# 60. Import Validation

```bash
python -c "from secureprobe.web.observer import observe_web_target; from secureprobe.models import WebTargetContext; print('IMPORT_OK')"
```

PASS.

---

# 61. 개별 Unit Test

```bash
pytest tests/unit/test_web_observer.py -q
```

PASS.

---

# 62. 전체 Regression

```bash
pytest -q
```

현재 실제 test 수를 기준으로 결과를 새로 기록한다.

기존 숫자를 복사하지 않는다.

---

# 63. Day 8 Regression 범위

전체 pytest에서 최소 다음이 모두 유지되어야 한다.

```text
Safety Gate
http_request
endpoint_collector
form_parser
header_inspector
cookie_inspector
cookie pipeline bridge
Web Observer
Day 1/2 Model Regression
```

---

# 64. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T07_WEB_TARGET_CONTEXT_RESULT_v0.1.md
```

---

# 65. Result Document 필수 내용

```text
Task ID
Status
Public API
Created Files
Modified Files

WebTargetContext Schema
Base URL Policy
Endpoint Policy
Form Policy
Header Policy
Cookie Policy
Content-Type Policy
Authentication Detection Policy
Session Detection Policy

HTTP Tool Integration
Safety Responsibility
Sensitive Data Policy
Ground Truth Separation
Benchmark Separation

Unit Test Result
Full Regression Result
Import Validation
Issues

Day 8 Completion
Next Task
```

---

# 66. 결과 문서에 반드시 기록할 흐름

```text
AssessmentRequest
        ↓
http_request
        ↓
final URL / safe headers / CookieInfo / body excerpt
        ↓
endpoint_collector
form_parser
header_inspector
        ↓
WebTargetContext
```

그리고:

```text
Raw Cookie Value:
NOT STORED

Raw Response Body:
NOT STORED IN CONTEXT

Ground Truth:
NOT AVAILABLE TO OBSERVER

Benchmark Result:
NOT AVAILABLE TO OBSERVER
```

---

# 67. Day 8 Completion Section

모든 테스트가 통과하면 결과 문서에:

```text
## Day 8 Completion

READY TO CLOSE
```

를 기록한다.

근거:

```text
D08-T01 Safety Gate             COMPLETED
D08-T02 http_request            COMPLETED
D08-T03 endpoint_collector      COMPLETED
D08-T04 form_parser             COMPLETED
D08-T05 header_inspector        COMPLETED
D08-T06 cookie_inspector        COMPLETED
D08-T06A Cookie Pipeline Bridge COMPLETED
D08-T07 WebTargetContext        COMPLETED
```

---

# 68. Next Task

결과 문서:

```text
## Next Task

D09-T01 — Tool Registry
```

---

# 69. 변경 가능 파일

생성:

```text
secureprobe/web/observer.py
tests/unit/test_web_observer.py

docs/05_ai_development/codex_results/day08/
D08-T07_WEB_TARGET_CONTEXT_RESULT_v0.1.md
```

수정:

```text
secureprobe/models/target.py
secureprobe/models/__init__.py
secureprobe/web/__init__.py
```

필요한 파일만 수정한다.

---

# 70. 수정 금지 파일

```text
secureprobe/core/safety.py

secureprobe/web/tools/http_request.py
secureprobe/web/tools/endpoint_collector.py
secureprobe/web/tools/form_parser.py
secureprobe/web/tools/header_inspector.py
secureprobe/web/tools/cookie_inspector.py

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

기존 Passive Tool 결함을 발견하면
이번 Task에서 임의 수정하지 말고 Result Document의 Issues에 기록한다.

---

# 71. Dependency 정책

새 dependency 추가 금지.

현재 dependency만 사용한다.

---

# 72. 범위 확장 금지

이번 Task에서 구현하지 않는다.

```text
Recursive Crawling
Browser Automation
JavaScript Execution
Authentication Login
Credential Submission
Active Testing
SQLi/XSS Payload
Access Control Test
Tool Registry
LLM Planner
Tool Selector
Analyzer
Verifier
Finding
Report
Ground Truth
ZAP
Semgrep
```

---

# 73. 완료 체크리스트

```text
[ ] WebTargetContext Model 구현
[ ] models/__init__.py export

[ ] observer.py 생성
[ ] observe_web_target 구현

[ ] http_request 재사용
[ ] GET 사용
[ ] follow_redirects=True
[ ] direct httpx 사용 없음

[ ] final_url → base_url
[ ] content_type 정규화
[ ] HTML 여부 판단

[ ] endpoint_collector 재사용
[ ] form_parser 재사용
[ ] header_inspector 재사용
[ ] CookieInfo Validation

[ ] raw Body Context 저장 없음
[ ] raw Cookie Context 저장 없음
[ ] raw Set-Cookie 저장 없음

[ ] Header 8개 dict 생성
[ ] missing Header → null

[ ] authentication_detected 구현
[ ] password field 기준

[ ] session_detected 구현
[ ] 제한된 exact cookie-name heuristic

[ ] HTML Context PASS
[ ] Non-HTML Context PASS
[ ] Redirect Final URL PASS
[ ] Header Context PASS
[ ] Cookie Context PASS
[ ] Authentication Hint PASS
[ ] Session Hint PASS

[ ] HTTP failure handling
[ ] Invalid Tool Output reject
[ ] Invalid Cookie metadata reject

[ ] Ground Truth leakage 없음
[ ] Benchmark leakage 없음
[ ] Vulnerability 판단 없음
[ ] LLM 호출 없음
[ ] Recursive Crawl 없음

[ ] Unit Test PASS
[ ] Full Regression PASS
[ ] Import PASS

[ ] Result Document 생성
[ ] Day 8 READY TO CLOSE 기록
[ ] Next Task D09-T01 기록
```

---

# 74. 완료 조건

다음 조건을 모두 만족하면 D08-T07 완료다.

```text
AssessmentRequest URL
→ http_request
→ Passive Parser
→ WebTargetContext

전체 흐름이 Structured Model로 연결됨

Endpoint / Form / Header / Cookie Context 생성 가능

Authentication / Session Hint 생성 가능

Sensitive Raw Data 미보존

Ground Truth / Benchmark 분리 유지

No Active Test

No LLM

No Recursive Crawl

Unit Test PASS

Full Regression PASS

Day 8 READY TO CLOSE
```

---

# 75. 권장 Commit Message

```text
feat: build web target context
```

사용 금지:

```text
git commit --amend
git push --force
```

---

# 76. 완료 보고 형식

```text
D08-T07 WEB TARGET CONTEXT

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- WebTargetContext model
- passive observer orchestration
- endpoint context
- form context
- header context
- cookie context
- authentication hint
- session hint
- content type normalization

Validation:
- HTML Context: PASS / FAIL
- Non-HTML Context: PASS / FAIL
- Final URL: PASS / FAIL
- Endpoint Collection: PASS / FAIL
- Form Parsing: PASS / FAIL
- Header Mapping: PASS / FAIL
- Cookie Metadata: PASS / FAIL
- Authentication Detection: PASS / FAIL
- Session Detection: PASS / FAIL
- Sensitive Data Non-Retention: PASS / FAIL
- HTTP Failure Handling: PASS / FAIL
- Invalid Output Rejection: PASS / FAIL
- Ground Truth Separation: PASS / FAIL
- Benchmark Separation: PASS / FAIL
- Direct Network Client Absent: PASS / FAIL
- Recursive Crawl Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T07_WEB_TARGET_CONTEXT_RESULT_v0.1.md

Day 8:
READY TO CLOSE / NOT READY

Next Task:
D09-T01 — Tool Registry

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-
```

---

# 77. 작업 종료 원칙

D08-T07 완료 후 Day 8 검증을 수행한다.

검증 통과 시:

```text
DAY 8 — COMPLETED
```

로 공식 종료한다.

그 다음:

```text
D09-T01 — Tool Registry
```

로 이동한다.

SecureBoard가 Claude에서 전달되면
현재 Mock 기반 검증과 별도로 실제 Lab을 대상으로
Web Observer Integration Test를 수행한다.
