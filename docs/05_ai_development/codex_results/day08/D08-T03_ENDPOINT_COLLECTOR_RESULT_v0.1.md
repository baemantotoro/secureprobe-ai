# D08-T03 — Endpoint Collector Result v0.1

## 1. Task ID / Status

Task ID: D08-T03

Status: COMPLETED

## 2. Public API

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

HTML 한 문서에서 Endpoint 후보를 반환하는 순수 parser다.
`BeautifulSoup(html, "html.parser")`와 기존 dependency만 사용한다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/models/target.py`
- `secureprobe/web/tools/endpoint_collector.py`
- `tests/unit/test_endpoint_collector.py`
- `docs/05_ai_development/codex_results/day08/D08-T03_ENDPOINT_COLLECTOR_RESULT_v0.1.md`

Modified Files:

- `secureprobe/models/__init__.py`: Endpoint / EndpointParameter export 추가.

기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T03_ENDPOINT_COLLECTOR_v0.1.md`도 내용 변경 없이 Git에 등록한다.
Safety Gate, HTTP Tool, 기존 모델 정의, SecureBoard, 기준 문서 및 requirements는 변경하지 않았다.

## 4. Endpoint Model / Collected Sources

Endpoint:

- `url`: 빈 문자열 및 공백 문자열 금지.
- `method`: GET / POST.
- `source`: current / link / form.
- `parameters`: EndpointParameter 목록, instance별 독립 기본값.

EndpointParameter는 `name`과 `location`(query / form)만 저장한다.
두 모델은 `extra="forbid"`이며 field value 및 Ground Truth 등 추가 필드를 거부한다.
WebTargetContext 전체 모델은 구현하지 않았다.

Collected Sources:

- base URL: current / GET.
- `<a href>`: link / GET.
- `<form action>`: form / GET 또는 POST Metadata.

script src, img src, iframe src, link href, meta refresh, onclick 및 JavaScript route는 수집하지 않는다.
HTML `<base>` 태그도 해석하지 않고 호출자가 전달한 base URL을 유지한다.

## 5. URL Normalization / Scheme Policy

상대 URL, 부모 상대 URL, Root-relative 및 Scheme-relative URL을 절대 URL로 해석한다.
Fragment는 제거하며 Query 문자열은 보존한다.
Scheme / Host는 lowercase, Host의 마지막 점 하나는 제거한다.
명시적 Port는 숫자로 정규화하고 유지하며 비어 있는 path는 `/`로 정규화한다.

URL 구문 검증은 기존 public `validate_web_target(..., active=False)`를 재사용한다.
private helper를 import하지 않는다.
http / https만 허용하며 Userinfo, malformed Host / Port / IPv6,
역슬래시·내부 공백·제어문자가 있는 후보를 제외한다.
urljoin이 비정상 절대 URL 또는 제어문자를 정규화하여 숨기지 않도록 원시 reference도 검사한다.
잘못된 href/action은 해당 항목만 무시하고 정상 항목 수집을 계속한다.
빈 링크와 Fragment-only 링크는 무시한다.

base URL이 유효하지 않거나 base_url/html이 문자열이 아니면 ValueError다.
빈 HTML 또는 일반 문자열 입력은 current Endpoint만 반환할 수 있다.

## 6. Scope Policy

기본적으로 base URL과 정확히 같은 canonical Host만 후보로 포함한다.
추가 Host는 `scope.allowed_hosts`에 명시된 경우 후보로 포함한다.
Host 부분 문자열 비교, Wildcard, URL 또는 Port 포함 Scope 항목을 지원하지 않는다.
`localhost.evil.com` 등 위장 Host는 같은 Host로 처리하지 않는다.
Path Scope 세부 enforcement는 이번 Task에 포함하지 않는다.

Endpoint 후보 수집은 HTTP 요청 허가를 의미하지 않는다.
Collector는 Authorization을 판단하지 않는다.
실제 요청은 `http_request`가 Safety Gate / Scope / 호출자 Allowlist 정책을 다시 적용하여 수행한다.

## 7. Form Method Policy / Parameter Policy

Form method는 공백 제거 및 uppercase로 정규화한다.
method 속성이 없으면 GET이며, GET / POST 외의 Form은 무시한다.
action이 없거나 비어 있으면 현재 URL을 사용한다.
POST Form은 Metadata로 수집만 하며 실행하지 않는다.

Query parameter는 이름만 추출하고 중복 이름을 제거한다.
Form의 input / textarea / select는 name이 있을 때만 수집하며 해당 Form 소속 field만 포함한다.
Form value, textarea 내용, select option value, 비밀번호 및 hidden token 값은 저장하지 않는다.
Query 문자열 자체는 지침대로 URL에 보존한다.

## 8. Deduplication / Endpoint Limit

Deduplication key: `(method, normalized_url)`.

같은 URL의 GET / POST는 서로 다른 Endpoint다.
중복 Endpoint는 최초 발견 source를 유지하고 `(name, location)` 기준으로 parameter metadata를 병합한다.
결과 순서는 current URL → DOM 등장 순서다.

Endpoint Limit 기본 100개, 허용 범위는 integer 1~500이다.
0 / 음수 / 501 이상 / bool / 비정수 입력은 ValueError다.
current Endpoint가 제한 수에 포함된다. 제한 이후 새 Endpoint는 추가하지 않으며,
이미 유지된 Endpoint의 parameter metadata 병합은 계속 수행한다.

## 9. Network I/O

None

HTTP 요청, DNS lookup, Form Submit, POST 실행, 재귀 크롤링,
JavaScript 실행 및 Browser Automation이 없다.
Safety Gate 재사용도 입력 검증만 수행한다.
Ground Truth / Benchmark 정보를 사용하거나 취약점 판단을 생성하지 않는다.
Unit Test는 순수 parser 테스트이며 MockTransport가 필요하지 않다.

## 10. Unit Test Result / Full Regression Result

실행일: 2026-10-03 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_endpoint_collector.py -q
```

```text
71 passed in 0.31s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
352 passed in 1.39s
```

Task 문서의 예시 회귀 수치는 212개지만 실제 작업 전 기준은 D08-T02를 포함한 281개다.
기존 281개와 새 Endpoint Collector 테스트 71개가 모두 통과했다.

## 11. Import Validation / Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.web.tools.endpoint_collector import collect_endpoints; from secureprobe.models import Endpoint, EndpointParameter; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

- Current URL: PASS
- Relative Link: PASS
- Query: PASS
- Fragment Removal: PASS
- GET Form: PASS
- POST Form Metadata: PASS
- Field Values Not Stored: PASS
- Unsupported Scheme: PASS
- External Host: PASS
- allowed_hosts: PASS
- Spoofed Host: PASS
- Userinfo: PASS
- Deduplication: PASS
- GET/POST Same URL: PASS
- Endpoint Limit: PASS
- Malformed Link: PASS
- Empty HTML: PASS
- Deterministic Order: PASS
- Model Validation / JSON Round-trip: PASS
- Network I/O Absent: PASS (코드 검토)
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

## 12. Issues

None

SecureBoard 전달 후 실제 Lab HTML을 이용한 Integration Test는 별도로 수행한다.

## 13. Next Task

D08-T04 — form_parser

다음 Task는 자동 시작하지 않는다.
