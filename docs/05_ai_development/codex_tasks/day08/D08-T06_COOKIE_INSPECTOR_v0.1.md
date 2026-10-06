# D08-T06 — Cookie Inspector Implementation v0.1

## 1. 목적

SecureProbe AI Web Assessment의 Passive Tool인 `cookie_inspector`를 구현한다.

이 Tool은 이미 확보된 HTTP `Set-Cookie` Header를 입력으로 받아
Cookie의 이름과 보안 관련 Attribute Metadata를 Structured Output으로 반환한다.

기본 흐름:

```text
HTTP Response
    ↓
Set-Cookie Header
    ↓
cookie_inspector
    ↓
CookieInfo[]
```

이번 Task는 Cookie를 **분석만** 하며 저장된 Cookie 값을 재사용하거나 전송하지 않는다.

---

## 2. 작업 ID

```text
D08-T06 — cookie_inspector
```

선행 작업:

```text
D08-T01 Safety Gate          COMPLETED
D08-T02 http_request         COMPLETED
D08-T03 endpoint_collector   COMPLETED
D08-T04 form_parser          COMPLETED
D08-T05 header_inspector     COMPLETED
```

다음 작업:

```text
D08-T07 — WebTargetContext 생성
```

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 3. DATA_SCHEMA 기준

`DATA_SCHEMA_v0.1.md`의 CookieInfo 개념을 따른다.

예:

```json
{
  "name": "SESSION",
  "secure": false,
  "http_only": true,
  "same_site": "Lax",
  "domain": "localhost",
  "path": "/"
}
```

이번 Task에서는 필요 시 다음 Metadata를 최소 확장할 수 있다.

```text
max_age
expires
```

단 Cookie Value는 저장하지 않는다.

---

## 4. 핵심 책임

`cookie_inspector`가 담당:

```text
Set-Cookie Header 파싱
Cookie Name 추출
Secure Attribute 관찰
HttpOnly Attribute 관찰
SameSite Attribute 관찰
Domain Attribute 관찰
Path Attribute 관찰
Max-Age Attribute 관찰
Expires Attribute 관찰
Malformed Cookie 개별 무시
Structured CookieInfo 반환
```

담당하지 않음:

```text
HTTP 요청
Cookie 재전송
Session 유지
Login
Credential 사용
CSRF 판단
Session Fixation 판단
취약점 확정
Severity 결정
OWASP/CWE Mapping
Finding 생성
Ground Truth 비교
ZAP/Semgrep 비교
Report 생성
```

---

## 5. 구현 위치

생성:

```text
secureprobe/web/tools/cookie_inspector.py
```

Model은 기존:

```text
secureprobe/models/target.py
```

에 `CookieInfo`를 추가하는 것을 권장한다.

필요 시 수정:

```text
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py
```

Unit Test:

```text
tests/unit/test_cookie_inspector.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T06_COOKIE_INSPECTOR_RESULT_v0.1.md
```

---

## 6. 네트워크 I/O 금지

이번 Tool은 순수 Parser다.

금지:

```text
httpx
requests
socket
DNS lookup
http_request 호출
```

입력:

```text
Set-Cookie 문자열 또는 문자열 목록
```

출력:

```text
list[CookieInfo]
```

---

## 7. Public API

권장:

```python
def inspect_cookies(
    *,
    set_cookie_headers: str | list[str],
    max_cookies: int = 50,
) -> list[CookieInfo]:
    ...
```

또는:

```python
Sequence[str]
```

를 사용할 수 있다.

한 방식만 선택한다.

---

## 8. CookieInfo Model

권장:

```python
class CookieInfo(BaseModel):
    name: str
    secure: bool
    http_only: bool
    same_site: str | None = None
    domain: str | None = None
    path: str | None = None
    max_age: int | None = None
    expires: str | None = None
```

정책:

```text
extra="forbid"
str_strip_whitespace=True
```

Cookie Value 필드 생성 금지.

---

## 9. Cookie Value 저장 금지

가장 중요한 요구사항이다.

예:

```text
Set-Cookie:
SESSION=super-secret-session-id; Secure; HttpOnly
```

결과:

```json
{
  "name": "SESSION",
  "secure": true,
  "http_only": true
}
```

다음 문자열은 결과에 존재하면 안 된다.

```text
super-secret-session-id
```

---

## 10. Cookie Name

첫 번째 `name=value` pair에서 Cookie name만 추출한다.

예:

```text
SESSION=abc123
```

→

```text
name=SESSION
```

Value는 즉시 버린다.

---

## 11. Attribute Key

Attribute 이름 비교는 case-insensitive 처리한다.

예:

```text
Secure
secure
SECURE
```

동일하게 처리.

---

## 12. Secure

Attribute 존재 여부:

```text
Secure
```

→

```text
secure=True
```

없으면:

```text
False
```

---

## 13. HttpOnly

Attribute 존재 여부:

```text
HttpOnly
```

→

```text
http_only=True
```

없으면:

```text
False
```

---

## 14. SameSite

지원:

```text
Strict
Lax
None
```

case-insensitive 입력을 canonical 형태로 정규화한다.

예:

```text
samesite=strict → Strict
SAMESITE=LAX    → Lax
samesite=none   → None
```

지원하지 않는 값:

```text
same_site=None
```

또는 명확한 unknown 처리.

v0.1 권장:

```text
None
```

---

## 15. Domain

`Domain` Attribute가 있으면 값만 Metadata로 저장할 수 있다.

예:

```text
Domain=localhost
```

→

```text
domain="localhost"
```

Cookie secret이 아니므로 허용한다.

단 과도한 정규화는 하지 않는다.

---

## 16. Path

`Path` Attribute를 저장한다.

예:

```text
Path=/
```

→

```text
path="/"
```

---

## 17. Max-Age

정수로 변환 가능하면 저장한다.

예:

```text
Max-Age=3600
```

→

```text
max_age=3600
```

잘못된 값:

```text
Max-Age=abc
```

이면:

```text
max_age=None
```

권장.

Cookie 전체 parsing 실패로 만들지 않는다.

---

## 18. Expires

`Expires` 문자열은 Metadata로 저장 가능하다.

예:

```text
Expires=Wed, 21 Oct 2026 07:28:00 GMT
```

이번 Task에서는 datetime parsing까지 강제하지 않는다.

원문을 안전한 길이 범위 내에서 저장한다.

---

## 19. Quoted Cookie Value

예:

```text
session="abc;123"; Secure; HttpOnly
```

Cookie Value는 저장하지 않는다.

Parser가 quoted value 때문에 Attribute를 잘못 분리하지 않도록 한다.

가능하면 Python 표준 라이브러리:

```text
http.cookies.SimpleCookie
```

사용을 우선 검토한다.

다만 `Set-Cookie`의 일부 비표준 형태를 처리하기 어렵다면
작고 명확한 Parser를 구현해도 된다.

---

## 20. Multiple Set-Cookie Header

여러 Header를 처리해야 한다.

예:

```python
[
    "SESSION=abc; Secure; HttpOnly",
    "theme=dark; Path=/; SameSite=Lax",
]
```

결과:

```text
CookieInfo 2개
```

---

## 21. Comma Split 금지

다음 때문에 단순 comma split 금지:

```text
Expires=Wed, 21 Oct 2026 ...
```

즉:

```python
header.split(",")
```

로 Cookie를 분리하면 안 된다.

각 Set-Cookie Header 문자열을 개별 입력 항목으로 처리한다.

---

## 22. Single String Input

단일 Header 문자열도 지원 가능.

```text
SESSION=abc; Secure; HttpOnly
```

내부적으로 1개 목록으로 정규화한다.

---

## 23. Malformed Cookie

잘못된 Cookie 하나 때문에 전체 Parser가 실패하면 안 된다.

예:

```text
=broken
no-equals
```

권장:

```text
해당 항목 무시
```

정상 Cookie는 계속 파싱한다.

---

## 24. Empty Header

다음은 무시:

```text
""
"   "
```

---

## 25. Duplicate Cookie Name

동일 Cookie name이 여러 Header에서 나올 수 있다.

이번 v0.1 권장:

```text
각 Set-Cookie Header를 독립 CookieInfo로 유지
```

이유:

```text
Path/Domain이 다를 수 있음
```

name만으로 dedupe하지 않는다.

---

## 26. Deterministic Order

입력 Header 순서를 그대로 유지한다.

동일 입력 → 동일 출력.

---

## 27. Cookie 수 제한

기본:

```text
max_cookies = 50
```

허용 범위:

```text
1 ~ 200
```

초과 시 입력 순서 기준으로 앞에서부터 제한한다.

---

## 28. max_cookies Validation

다음은 오류:

```text
0
음수
201 이상
bool
float
string
None
```

ValueError.

---

## 29. Attribute 수 제한

별도 Attribute 개수 제한은 필수 아님.

단 과도하게 긴 Header 방지를 위해 Header 길이 제한 권장:

```text
max_header_chars = 8192
```

초과 Header는:

```text
무시
```

또는 안전하게 truncate 후 parsing.

권장:

```text
무시
```

---

## 30. Control Character

CR/LF/control 문자가 포함된 Header는 안전상 제외한다.

Header Injection-like 입력을 그대로 처리하지 않는다.

---

## 31. Attribute Value 길이

Domain/Path/Expires 등 Metadata는 무제한 저장하지 않는다.

권장:

```text
각 Attribute Value 최대 2048자
```

초과 시 truncate 또는 None.

---

## 32. Unknown Attribute

예:

```text
Priority=High
Partitioned
Foo=Bar
```

이번 v0.1에서는 무시한다.

범위 확장 금지.

---

## 33. No Cookie Replay

절대 수행하지 않는다.

```text
Cookie header 생성
Cookie jar 저장
Cookie 재전송
Session 유지
```

---

## 34. No Session Judgment

다음 판단 금지:

```text
Session Cookie
Persistent Cookie
Session Fixation
Weak Session
```

Metadata만 반환.

---

## 35. No Vulnerability Judgment

금지:

```text
Secure missing vulnerability
HttpOnly missing vulnerability
SameSite weak
Cookie misconfiguration
```

Analyzer 단계 책임이다.

---

## 36. No Severity / OWASP / CWE / Finding

다음 생성 금지:

```text
Severity
OWASP Mapping
CWE Mapping
CandidateFinding
Finding
```

---

## 37. No Ground Truth / Benchmark

금지:

```text
ground_truth
known_vulnerability
expected_ground_truth
zap_result
semgrep_result
benchmark_result
```

---

## 38. Unit Test 파일

```text
tests/unit/test_cookie_inspector.py
```

---

## 39. Unit Test — Basic Cookie

입력:

```text
SESSION=abc123
```

검증:

```text
name=SESSION
secure=False
http_only=False
same_site=None
```

그리고:

```text
abc123
```

이 결과 JSON에 없어야 한다.

---

## 40. Unit Test — Secure / HttpOnly

```text
SESSION=secret; Secure; HttpOnly
```

검증:

```text
secure=True
http_only=True
```

secret 미저장.

---

## 41. Unit Test — SameSite

각각:

```text
SameSite=Strict
SameSite=Lax
SameSite=None
```

canonical 값 검증.

대소문자 변형도 검증.

---

## 42. Unit Test — Invalid SameSite

```text
SameSite=Invalid
```

→

```text
same_site=None
```

권장.

---

## 43. Unit Test — Domain / Path

```text
Domain=localhost
Path=/app
```

정상 추출.

---

## 44. Unit Test — Max-Age

정상:

```text
Max-Age=3600
```

→ 3600.

비정상:

```text
Max-Age=abc
```

→ None.

---

## 45. Unit Test — Expires With Comma

```text
Expires=Wed, 21 Oct 2026 07:28:00 GMT
```

comma 때문에 Cookie가 잘못 분리되지 않아야 한다.

---

## 46. Unit Test — Multiple Headers

2~3개 `Set-Cookie` 입력.

입력 순서대로 CookieInfo 생성.

---

## 47. Unit Test — Quoted Value

```text
session="abc;123"; Secure; HttpOnly
```

검증:

```text
name=session
secure=True
http_only=True
```

Value 미저장.

---

## 48. Unit Test — Sensitive Value Non-Retention

다음 문자열 사용:

```text
super-secret-session
token-secret
private-cookie-value
```

결과 JSON 어디에도 없어야 한다.

---

## 49. Unit Test — Empty / Malformed Header

정상 Cookie와 섞어서:

```text
""
" "
"broken"
"=bad"
```

문제 항목은 무시,
정상 항목은 유지.

---

## 50. Unit Test — Duplicate Name

예:

```text
id=a; Path=/
id=b; Path=/admin
```

두 CookieInfo 모두 유지.

Value a/b는 저장하지 않는다.

---

## 51. Unit Test — Case-insensitive Attributes

```text
secure
HTTPONLY
sAmEsItE=lAx
DOMAIN=LOCALHOST
PATH=/app
```

정상 인식.

---

## 52. Unit Test — Unknown Attribute

```text
Priority=High
Foo=Bar
Partitioned
```

Parser crash 없음.

지원 Metadata에 들어가지 않음.

---

## 53. Unit Test — Control Character

CR/LF 포함 Header는 제외.

secret이 결과에 남지 않아야 한다.

---

## 54. Unit Test — Oversized Header

8192자 초과 Header:

```text
해당 Cookie 제외
```

또는 선택한 안전 정책 검증.

---

## 55. Unit Test — Cookie Limit

100개 Header 입력.

```text
max_cookies=10
```

→ 결과 최대 10개.

---

## 56. Unit Test — Invalid Limit

```text
0
-1
201
True
1.5
"10"
None
```

ValueError.

---

## 57. Unit Test — Deterministic Order

동일 입력 반복 시 동일 순서와 동일 결과.

---

## 58. CookieInfo Model Validation

검증:

```text
name 빈 값 거부
secure strict bool
http_only strict bool
extra field 거부
```

Cookie value 같은 필드 추가 시 거부.

예:

```json
{
  "name": "SESSION",
  "value": "secret"
}
```

→ ValidationError.

---

## 59. Mutable Default

CookieInfo에 mutable default가 없다면 별도 불필요.

list wrapper를 Model로 만든 경우 instance isolation 테스트.

---

## 60. JSON Round-trip

```python
payload = cookie.model_dump(mode="json")
restored = CookieInfo.model_validate(payload)
```

PASS.

---

## 61. Import Validation

```bash
python -c "from secureprobe.web.tools.cookie_inspector import inspect_cookies; from secureprobe.models import CookieInfo; print('IMPORT_OK')"
```

PASS.

---

## 62. 개별 Unit Test

```bash
pytest tests/unit/test_cookie_inspector.py -q
```

PASS.

---

## 63. 전체 Regression

```bash
pytest -q
```

현재 실제 test 수를 기준으로 새 결과를 기록한다.

기존 숫자를 복사하지 않는다.

---

## 64. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T06_COOKIE_INSPECTOR_RESULT_v0.1.md
```

---

## 65. Result Document 필수 내용

```text
Task ID
Status
Public API
Created Files
Modified Files
CookieInfo Model
Cookie Name Policy
Sensitive Value Policy
Secure Policy
HttpOnly Policy
SameSite Policy
Domain/Path Policy
Max-Age/Expires Policy
Multiple Header Policy
Malformed Header Policy
Limit Policy
Network I/O
Session Replay
Vulnerability Judgment
Unit Test Result
Full Regression Result
Import Validation
Issues
Next Task
```

---

## 66. 책임 분리 기록

결과 문서에 다음을 반드시 명시한다.

```text
cookie_inspector는 Set-Cookie Metadata만 분석한다.

Cookie Value는 저장하지 않는다.

Cookie를 재전송하거나 Session을 유지하지 않는다.

Secure / HttpOnly / SameSite 누락을 취약점으로 확정하지 않는다.

Severity / OWASP / CWE / Finding 생성은 Analyzer 단계 책임이다.
```

---

## 67. 변경 가능 파일

```text
secureprobe/web/tools/cookie_inspector.py
secureprobe/models/target.py
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py

tests/unit/test_cookie_inspector.py

docs/05_ai_development/codex_results/day08/
D08-T06_COOKIE_INSPECTOR_RESULT_v0.1.md
```

필요한 파일만 수정한다.

---

## 68. 수정 금지 파일

```text
secureprobe/core/safety.py
secureprobe/web/tools/http_request.py
secureprobe/web/tools/endpoint_collector.py
secureprobe/web/tools/form_parser.py
secureprobe/web/tools/header_inspector.py

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

## 69. Dependency 정책

새 dependency 추가 금지.

Python 표준 라이브러리 + 기존 Pydantic만 사용한다.

---

## 70. 완료 체크리스트

```text
[ ] cookie_inspector.py 생성
[ ] CookieInfo Model 구현

[ ] Cookie name 추출
[ ] Cookie value 미저장

[ ] Secure 관찰
[ ] HttpOnly 관찰
[ ] SameSite 정규화
[ ] Domain 관찰
[ ] Path 관찰
[ ] Max-Age 관찰
[ ] Expires 관찰

[ ] multiple Set-Cookie 지원
[ ] comma split 금지
[ ] quoted value 처리
[ ] malformed cookie 개별 무시
[ ] duplicate name 유지
[ ] case-insensitive attributes

[ ] max_cookies 제한
[ ] oversized header 방어
[ ] control character 방어
[ ] deterministic order

[ ] network I/O 없음
[ ] Cookie replay 없음
[ ] Session 유지 없음
[ ] Credential 사용 없음
[ ] 취약점 판단 없음
[ ] Severity 없음
[ ] OWASP/CWE 없음
[ ] Finding 생성 없음
[ ] Ground Truth/Benchmark 없음

[ ] Unit Test PASS
[ ] Full Regression PASS
[ ] Import PASS
[ ] Result Document 생성
```

---

## 71. 완료 조건

다음 조건을 모두 만족하면 D08-T06 완료다.

```text
Set-Cookie 구조 파싱 가능
Cookie name만 보존
Cookie value 미저장
Secure/HttpOnly/SameSite/Domain/Path/Max-Age/Expires 관찰
Multiple Header 처리
Quoted Value 처리
Malformed Header 개별 무시
Cookie 수 제한
Network I/O 없음
Cookie Replay 없음
취약점 확정 없음
Unit Test PASS
Full Regression PASS
범위 확대 없음
```

---

## 72. 권장 Commit Message

```text
feat: add passive cookie inspector
```

사용 금지:

```text
git commit --amend
git push --force
```

---

## 73. 완료 보고 형식

```text
D08-T06 COOKIE INSPECTOR

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- CookieInfo model
- Set-Cookie parsing
- Secure / HttpOnly
- SameSite normalization
- Domain / Path
- Max-Age / Expires
- sensitive value non-retention
- cookie/header limits

Validation:
- Basic Cookie: PASS / FAIL
- Secure: PASS / FAIL
- HttpOnly: PASS / FAIL
- SameSite Strict: PASS / FAIL
- SameSite Lax: PASS / FAIL
- SameSite None: PASS / FAIL
- Invalid SameSite: PASS / FAIL
- Domain: PASS / FAIL
- Path: PASS / FAIL
- Max-Age: PASS / FAIL
- Expires: PASS / FAIL
- Multiple Headers: PASS / FAIL
- Quoted Value: PASS / FAIL
- Sensitive Value Not Stored: PASS / FAIL
- Malformed Header: PASS / FAIL
- Duplicate Name: PASS / FAIL
- Case Insensitive Attribute: PASS / FAIL
- Unknown Attribute: PASS / FAIL
- Control Character: PASS / FAIL
- Oversized Header: PASS / FAIL
- Cookie Limit: PASS / FAIL
- Deterministic Order: PASS / FAIL
- Network I/O Absent: PASS / FAIL
- Cookie Replay Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T06_COOKIE_INSPECTOR_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T07 — WebTargetContext 생성
```

---

## 74. 작업 종료 원칙

D08-T06 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T07 — WebTargetContext 생성
```

SecureBoard가 Claude에서 전달되면 실제 Set-Cookie Header를 이용한 Integration Test를 별도로 수행한다.
