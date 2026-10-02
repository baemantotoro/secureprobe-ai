# D08-T03 — Endpoint Collector Implementation v0.1

## 1. 목적

SecureProbe AI Web Assessment에서 사용할 Passive Tool인
`endpoint_collector`를 구현한다.

이 Tool의 역할은 HTML 응답에서:

```text
현재 URL
링크(<a href>)
Form Action(<form action>)
```

을 수집하고, 이를 Scope 내 Endpoint 후보로 정규화하는 것이다.

이번 Task는 크롤러 구현이 아니다.

다음은 하지 않는다.

```text
무제한 페이지 탐색
자동 재귀 크롤링
JavaScript 실행
Browser Automation
Form Submit
POST 실행
공격 Payload 생성
취약점 판단
```

---

## 2. 작업 ID와 근거

- WBS 기준: Day 8, Task 03
- 작업 ID: `D08-T03`
- 작업명: endpoint_collector
- 우선순위: P0
- 선행 작업:
  - D08-T01 Safety Gate 완료
  - D08-T02 http_request 완료
- 다음 작업:
  - D08-T04 — form_parser

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. 핵심 역할

`endpoint_collector`는 다음 흐름에서 사용한다.

```text
http_request
    ↓
HTML Response
    ↓
endpoint_collector
    ↓
Endpoint 후보 목록
```

역할:

```text
HTML에서 URL 후보 추출
상대 URL → 절대 URL 정규화
Fragment 제거
Query 보존
Scope 밖 Host 제거
지원하지 않는 Scheme 제거
중복 제거
Endpoint 수 제한
Form Method Metadata 기록
```

---

## 4. 구현 위치

권장 파일:

```text
secureprobe/web/tools/endpoint_collector.py
```

필요 시 수정:

```text
secureprobe/web/tools/__init__.py
```

Unit Test:

```text
tests/unit/test_endpoint_collector.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T03_ENDPOINT_COLLECTOR_RESULT_v0.1.md
```

---

# 5. 네트워크 I/O 금지

이번 Tool은 직접 HTTP 요청을 수행하지 않는다.

금지:

```text
httpx.get
AsyncClient
requests
socket
DNS lookup
```

입력은 이미 확보된 HTML/URL 정보다.

즉:

```text
http_request
→ HTML 확보

endpoint_collector
→ HTML 분석
```

책임을 분리한다.

---

# 6. 권장 Public API

예:

```python
def collect_endpoints(
    *,
    base_url: str,
    html: str,
    allowed_hosts: set[str] | None = None,
    max_endpoints: int = 100,
) -> list[Endpoint]:
    ...
```

또는 기존 AssessmentScope를 받는 형태도 가능하다.

권장:

```python
def collect_endpoints(
    *,
    base_url: str,
    html: str,
    scope: AssessmentScope | None = None,
    max_endpoints: int = 100,
) -> list[Endpoint]:
    ...
```

한 방식만 선택한다.

---

# 7. Endpoint Model

DATA_SCHEMA_v0.1의 Endpoint 개념을 따른다.

최소 구조:

```text
url
method
parameters
source
```

이번 Task에서 필요한 최소 형태:

```python
class Endpoint(BaseModel):
    url: str
    method: str
    source: str
    parameters: list[dict[str, str]] = Field(default_factory=list)
```

또는 더 명확한 Parameter 보조 모델을 둘 수 있다.

예:

```python
class EndpointParameter(BaseModel):
    name: str
    location: str
```

단, 구현 복잡도를 키우지 않는다.

---

# 8. Endpoint Model 위치

권장:

```text
secureprobe/models/target.py
```

단, 현재 `target.py`가 없다면 이번 Task에서
Endpoint만 최소 생성할 수 있다.

생성 가능:

```text
secureprobe/models/target.py
```

수정 가능:

```text
secureprobe/models/__init__.py
```

이번 Task에서 WebTargetContext 전체를 구현하지 않는다.

---

# 9. Source 값

Endpoint `source`는 최소 다음 값을 사용한다.

```text
current
link
form
```

예:

```text
현재 페이지 자체 → current
<a href>        → link
<form action>   → form
```

Literal 또는 문자열 Validation을 사용할 수 있다.

---

# 10. Method 정책

Link:

```text
GET
```

Current URL:

```text
GET
```

Form:

HTML의 `method` 속성 기준.

기본:

```text
GET
```

허용 Metadata:

```text
GET
POST
```

이번 Task에서는 POST Endpoint를 **수집만** 한다.

실행하지 않는다.

---

# 11. Form Method 정규화

다음:

```html
<form method="post">
```

→

```text
POST
```

다음:

```html
<form>
```

→

```text
GET
```

지원하지 않는 method가 있으면:

```text
GET/POST 외 Form은 무시
```

권장.

---

# 12. 현재 URL 포함

수집 결과에 base URL 자체를 Endpoint로 포함한다.

예:

```text
base_url = http://localhost:5000/index
```

결과:

```text
Endpoint(
  url="http://localhost:5000/index",
  method="GET",
  source="current",
)
```

---

# 13. Link 수집

대상:

```html
<a href="...">
```

만 우선 수집한다.

이번 Task에서는 다음은 제외:

```text
script src
img src
iframe src
link href
meta refresh
JavaScript route
onclick
```

필요 시 후속 확장한다.

---

# 14. Form Action 수집

대상:

```html
<form action="...">
```

action이 없는 경우:

```text
현재 URL
```

로 간주 가능.

예:

```html
<form method="post">
```

→

```text
base_url + POST
```

---

# 15. URL 정규화

Python 표준 라이브러리:

```python
urllib.parse.urljoin
urllib.parse.urlsplit
urllib.parse.urlunsplit
```

사용 권장.

---

# 16. 상대 URL 처리

예:

```text
base:
http://localhost:5000/app/page

href:
../login
```

결과:

```text
http://localhost:5000/login
```

---

# 17. Root-relative URL

```text
/login
```

→ base host 기준 절대 URL.

---

# 18. Absolute URL

예:

```text
http://localhost:5000/admin
```

Scope 내라면 허용.

외부 Host면 차단.

---

# 19. Fragment 제거

다음:

```text
/page#section
/page#other
```

모두:

```text
/page
```

로 정규화한다.

Fragment는 Endpoint 식별에 사용하지 않는다.

---

# 20. Query 정책

Query String은 보존한다.

예:

```text
/search?q=test
```

→

```text
/search?q=test
```

단, parameter 추출도 수행할 수 있다.

예:

```text
q
```

→

```text
location=query
```

---

# 21. Query Parameter 추출

가능하면 다음 구조로 저장한다.

```python
[
    {
        "name": "q",
        "location": "query"
    }
]
```

중복 parameter name은 하나로 정리해도 된다.

---

# 22. Form Field Parameter

Form Endpoint에는 Form 내부 field name을
parameter metadata로 추가할 수 있다.

대상:

```text
input
textarea
select
```

필드에 `name`이 있을 때만 수집한다.

예:

```html
<input name="username">
<input name="password">
```

→

```text
username location=form
password location=form
```

---

# 23. Password Value 저장 금지

Form field의:

```text
name
type
```

정도만 분석한다.

다음은 저장하지 않는다.

```text
value
password value
token value
hidden secret
```

이번 Endpoint Model에는 field value 자체를 넣지 않는다.

---

# 24. Scheme 허용

Endpoint URL 허용 Scheme:

```text
http
https
```

그 외는 수집하지 않는다.

차단/무시:

```text
javascript:
mailto:
tel:
data:
ftp:
file:
gopher:
ws:
wss:
```

---

# 25. Empty / Hash Link

무시:

```text
href=""
href="#"
href="#section"
```

base URL과 완전히 동일하게 normalize된다면
current Endpoint와 중복 제거되므로 하나만 유지한다.

---

# 26. JavaScript Link 차단

예:

```html
<a href="javascript:alert(1)">
```

수집하지 않는다.

---

# 27. mailto / tel 차단

다음은 Endpoint가 아니다.

```text
mailto:test@example.com
tel:01012345678
```

수집하지 않는다.

---

# 28. Userinfo URL 차단

다음은 수집하지 않는다.

```text
http://user:pass@localhost/
http://localhost@evil.com/
```

Safety Gate와 동일한 보안 방향을 유지한다.

---

# 29. Same Host / Scope 정책

기본적으로 base URL Host와 동일한 Host만 수집한다.

추가 Host는:

```text
AssessmentScope.allowed_hosts
```

에 명시된 경우에만 후보로 포함할 수 있다.

단:

```text
allowed_hosts는 Authorization 증명이 아니다.
```

Endpoint Collector는 네트워크 요청을 하지 않으므로
Authorization 판단은 하지 않는다.

후속 `http_request`가 실제 요청 시 Safety Gate + Allowlist를 다시 적용한다.

---

# 30. Scope와 Authorization 책임 분리

Collector:

```text
어떤 Endpoint를 Assessment 후보로 포함할 것인가
```

Safety Gate:

```text
실제 요청 실행이 허용되는가
```

Collector 결과가 존재한다고 해서
HTTP 요청 권한이 생기는 것은 아니다.

---

# 31. Host Canonicalization

가능하면 기존 Safety Gate의 Host canonicalization 정책과
일관되게 처리한다.

단, private helper를 무리하게 import하지 않는다.

필요하면 최소 동일 정책:

```text
lowercase
trailing dot 제거
exact host match
```

사용.

---

# 32. Localhost Spoofing

base:

```text
http://localhost
```

HTML:

```html
<a href="http://localhost.evil.com/admin">
```

결과:

```text
수집하지 않음
```

substring 비교 금지.

---

# 33. Scheme-relative URL

예:

```text
//localhost:5000/path
```

base scheme을 사용해 normalize 가능.

Scope 내라면 수집.

---

# 34. Malformed URL

잘못된 href/action은
Tool 전체를 실패시키지 않고 해당 항목만 무시한다.

예:

```text
http://[::1
http://local host
```

Collector 전체 crash 금지.

---

# 35. Deduplication

동일 Endpoint는 한 번만 반환한다.

Deduplication Key 권장:

```text
(method, normalized_url)
```

즉:

```text
GET /login
POST /login
```

은 서로 다른 Endpoint로 유지한다.

---

# 36. Source 우선순위

같은 `(method, url)`이 여러 Source에서 발견된 경우
하나만 유지한다.

Source 우선순위는 단순하게:

```text
form > link > current
```

또는 최초 발견 기준으로 해도 된다.

중요한 것은 deterministic 해야 한다.

---

# 37. Parameter Merge

동일 Endpoint가 여러 번 발견되면
parameter metadata는 합칠 수 있다.

중복 name/location은 제거한다.

복잡한 merge 알고리즘은 불필요하다.

---

# 38. Endpoint 수 제한

무제한 HTML 링크 수집 방지.

기본:

```text
max_endpoints = 100
```

권장 허용 범위:

```text
1 ~ 500
```

최대 초과 시:

```text
앞에서부터 deterministic하게 제한
```

한다.

---

# 39. max_endpoints 입력 검증

다음은 오류:

```text
0
-1
501 이상
bool
```

명확하게 ValueError 또는 ValidationError.

---

# 40. Order

결과 순서는 deterministic 해야 한다.

권장:

```text
현재 URL
→ DOM 등장 순서
```

또는:

```text
정렬된 URL
```

한 방식을 유지한다.

Portfolio 재현성을 위해 deterministic이 중요하다.

---

# 41. HTML Parser

기존 dependency:

```text
beautifulsoup4
```

사용.

권장:

```python
BeautifulSoup(html, "html.parser")
```

외부 parser dependency 추가 금지.

---

# 42. HTML 입력 제한

이번 Task에서 max HTML size를 별도로 강제할 수 있다.

하지만 D08-T02에서 이미 body excerpt가 최대 64 KiB로 제한되므로
추가 복잡한 size limit은 필수 아님.

---

# 43. Empty HTML

```text
html=""
```

결과:

```text
current Endpoint만 반환
```

가능.

---

# 44. Non-HTML 입력

Collector 호출자는 HTML Response만 전달하는 것이 원칙이다.

이번 Task에서 content-type 판정은 하지 않아도 된다.

잘못된 문자열이 들어와도 crash하지 않도록 한다.

---

# 45. No HTTP Request

Unit Test에서 MockTransport도 필요 없다.

이 Tool은 순수 parser로 테스트한다.

---

# 46. No Vulnerability Judgment

다음 판단 금지:

```text
취약 endpoint
admin exposed
SQLi 가능
XSS 가능
```

Collector는 Endpoint 후보만 생성한다.

---

# 47. No Ground Truth / Benchmark

다음 정보 사용 금지:

```text
ground_truth
known_vulnerability
zap_result
semgrep_result
benchmark_result
```

---

# 48. No Recursive Crawl

다음 구조를 구현하지 않는다.

```text
Endpoint 발견
→ 자동 http_request
→ 새 HTML
→ 또 Endpoint 발견
→ 반복
```

이번 Task는 한 HTML 문서만 분석한다.

---

# 49. No JavaScript Execution

다음은 하지 않는다.

```text
SPA routing
onclick execution
fetch/XHR intercept
script parsing
Playwright/Selenium
```

---

# 50. Unit Test 파일

생성:

```text
tests/unit/test_endpoint_collector.py
```

---

# 51. Unit Test — Current Endpoint

base URL만 있는 경우:

```text
GET current
```

1개 생성.

---

# 52. Unit Test — Relative Link

HTML:

```html
<a href="/login">Login</a>
```

결과:

```text
GET http://localhost/login
```

---

# 53. Unit Test — Parent Relative Link

```html
<a href="../admin">Admin</a>
```

올바르게 urljoin.

---

# 54. Unit Test — Query

```html
<a href="/search?q=test&page=1">
```

Query 유지.

parameters:

```text
q
page
```

---

# 55. Unit Test — Fragment

```html
<a href="/page#one">
<a href="/page#two">
```

둘 다 normalize:

```text
/page
```

→ 1 Endpoint.

---

# 56. Unit Test — Form GET

```html
<form action="/search" method="get">
  <input name="q">
</form>
```

결과:

```text
GET /search
parameter q location=form
```

---

# 57. Unit Test — Form POST

```html
<form action="/login" method="post">
```

결과:

```text
POST /login
```

하지만 실제 POST 실행은 하지 않는다.

---

# 58. Unit Test — Form Default Method

```html
<form action="/search">
```

→ GET.

---

# 59. Unit Test — Form Missing Action

```html
<form method="post">
```

→ current URL + POST.

---

# 60. Unit Test — Field Value Not Stored

```html
<input name="password" value="secret">
<input type="hidden" name="csrf" value="token-secret">
```

Endpoint parameter metadata에는:

```text
password
csrf
```

가 있을 수 있으나:

```text
secret
token-secret
```

문자열이 결과에 존재하면 안 된다.

---

# 61. Unit Test — Unsupported Scheme

HTML:

```html
<a href="javascript:alert(1)">
<a href="mailto:test@example.com">
<a href="tel:01012345678">
<a href="ftp://localhost/file">
```

모두 제외.

---

# 62. Unit Test — External Host

base:

```text
http://localhost
```

HTML:

```html
<a href="https://example.com">
```

Scope에 없으면 제외.

---

# 63. Unit Test — allowed_hosts 추가 Host

base:

```text
http://localhost
```

scope:

```text
allowed_hosts=["secureboard.local"]
```

HTML:

```text
https://secureboard.local/path
```

Collector 후보에는 포함 가능.

단 실제 HTTP 실행 권한은 별도 Safety Gate/Allowlist가 필요함을
코드 주석/결과 문서에 기록한다.

---

# 64. Unit Test — Spoofed Host

```text
http://localhost.evil.com
```

제외.

---

# 65. Unit Test — Userinfo

```text
http://user:pass@localhost/
```

제외.

---

# 66. Unit Test — Duplicate

같은 URL이 여러 번 등장:

```html
<a href="/login">
<a href="/login#top">
<form action="/login" method="get">
```

method가 모두 GET이라면 하나로 dedupe 가능.

parameter merge 정책이 있으면 확인한다.

---

# 67. Unit Test — GET/POST Same URL

```html
<a href="/login">
<form action="/login" method="post">
```

결과:

```text
GET /login
POST /login
```

둘 다 유지.

---

# 68. Unit Test — max_endpoints

100개 이상 생성하는 HTML.

```text
max_endpoints=10
```

이면 결과 정확히 10개.

current Endpoint 포함 여부를 정책에 맞게 일관되게 처리한다.

---

# 69. Unit Test — Invalid max_endpoints

다음:

```text
0
-1
501
True
```

실패.

---

# 70. Unit Test — Malformed Link

잘못된 href 하나 때문에
나머지 정상 Endpoint 수집이 실패하면 안 된다.

---

# 71. Unit Test — Empty HTML

결과:

```text
current Endpoint만
```

---

# 72. Unit Test — Deterministic Order

동일 HTML을 여러 번 실행해
동일 순서/결과가 나오는지 확인.

---

# 73. Model Validation

Endpoint Model 사용 시:

```text
url 빈 문자열 금지
method GET/POST 제한
source current/link/form 제한
parameters list
extra forbid
```

를 권장한다.

---

# 74. Import Test

예:

```bash
python -c "from secureprobe.web.tools.endpoint_collector import collect_endpoints; print('IMPORT_OK')"
```

Endpoint export 시:

```bash
python -c "from secureprobe.models import Endpoint; print('IMPORT_OK')"
```

둘 다 확인 가능.

---

# 75. 개별 Unit Test

```bash
pytest tests/unit/test_endpoint_collector.py -q
```

PASS.

---

# 76. 전체 Regression

```bash
pytest -q
```

현재 기준:

```text
212 passed
```

새 Test 추가 후 실제 결과를 새로 기록한다.

기존 수치를 복사하지 않는다.

---

# 77. 결과 문서

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T03_ENDPOINT_COLLECTOR_RESULT_v0.1.md
```

---

# 78. 결과 문서 필수 항목

```text
Task ID
Status
Public API
Created Files
Modified Files
Endpoint Model
Collected Sources
URL Normalization
Scope Policy
Scheme Policy
Form Method Policy
Parameter Policy
Deduplication
Endpoint Limit
Network I/O
Unit Test Result
Full Regression Result
Import Validation
Issues
Next Task
```

---

# 79. 결과 문서 책임 분리

다음 내용을 명확히 기록한다.

```text
endpoint_collector는 네트워크 요청을 하지 않는다.

Endpoint 후보 수집은 HTTP 요청 허가를 의미하지 않는다.

실제 요청은 http_request가 수행하며
Safety Gate / Allowlist 정책을 다시 적용한다.

POST Form은 Metadata로 수집만 하며 실행하지 않는다.
```

---

# 80. 변경 가능 파일

생성 가능:

```text
secureprobe/web/tools/endpoint_collector.py
secureprobe/models/target.py
tests/unit/test_endpoint_collector.py

docs/05_ai_development/codex_results/day08/
D08-T03_ENDPOINT_COLLECTOR_RESULT_v0.1.md
```

필요한 경우 수정:

```text
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py
```

---

# 81. 수정 금지 파일

```text
secureprobe/core/safety.py
secureprobe/web/tools/http_request.py

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

---

# 82. Dependency 정책

기존:

```text
beautifulsoup4
```

사용.

새 dependency 추가 금지.

---

# 83. 완료 체크리스트

```text
[ ] endpoint_collector.py 생성
[ ] Endpoint Model 구현 또는 기존 구조 재사용

[ ] current URL 수집
[ ] link href 수집
[ ] form action 수집

[ ] relative URL normalization
[ ] fragment 제거
[ ] query 보존
[ ] query parameter 추출
[ ] form field name 추출

[ ] GET/POST metadata
[ ] POST 실행 없음

[ ] http/https만 허용
[ ] javascript/mailto/tel/data/ftp 제외
[ ] userinfo URL 제외
[ ] malformed URL 개별 무시

[ ] same-host 기본
[ ] allowed_hosts 범위 적용
[ ] localhost spoofing 차단
[ ] authorization 판단 없음

[ ] deduplication
[ ] GET/POST 동일 URL 구분
[ ] parameter merge
[ ] max_endpoints 제한
[ ] deterministic order

[ ] network I/O 없음
[ ] recursive crawl 없음
[ ] JavaScript 실행 없음
[ ] Ground Truth/Benchmark 사용 없음
[ ] 취약점 판단 없음

[ ] Unit Test PASS
[ ] Full pytest PASS
[ ] Import PASS
[ ] Result Document 생성
```

---

# 84. 완료 조건

다음 조건을 모두 만족하면 D08-T03 완료다.

```text
HTML 한 문서에서 Endpoint 후보 수집 가능
Current/Link/Form 구분
상대 URL 정규화
Scope 밖 Host 제거
지원하지 않는 Scheme 제거
Fragment 제거
Query 보존
Parameter Metadata 수집
GET/POST 구분
중복 제거
Endpoint 수 제한
Network I/O 없음
POST 실행 없음
Recursive Crawl 없음
Unit Test PASS
Full Regression PASS
범위 확대 없음
```

---

# 85. 권장 Commit Message

```text
feat: add passive endpoint collector
```

사용 금지:

```text
git commit --amend
git push --force
```

---

# 86. 완료 보고 형식

```text
D08-T03 ENDPOINT COLLECTOR

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- current endpoint
- link collection
- form action collection
- URL normalization
- query/form parameter metadata
- scope filtering
- deduplication
- endpoint cap

Validation:
- Current URL: PASS / FAIL
- Relative Link: PASS / FAIL
- Query: PASS / FAIL
- Fragment Removal: PASS / FAIL
- GET Form: PASS / FAIL
- POST Form Metadata: PASS / FAIL
- Field Values Not Stored: PASS / FAIL
- Unsupported Scheme: PASS / FAIL
- External Host: PASS / FAIL
- allowed_hosts: PASS / FAIL
- Spoofed Host: PASS / FAIL
- Userinfo: PASS / FAIL
- Deduplication: PASS / FAIL
- GET/POST Same URL: PASS / FAIL
- Endpoint Limit: PASS / FAIL
- Malformed Link: PASS / FAIL
- Empty HTML: PASS / FAIL
- Deterministic Order: PASS / FAIL
- Network I/O Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T03_ENDPOINT_COLLECTOR_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T04 — form_parser
```

---

# 87. 작업 종료 원칙

D08-T03 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T04 — form_parser
```

SecureBoard가 Claude에서 전달되면
실제 Lab HTML을 이용한 Integration Test를 별도로 수행한다.
