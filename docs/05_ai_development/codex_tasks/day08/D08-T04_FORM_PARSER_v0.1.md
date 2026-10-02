# D08-T04 — Form Parser Implementation v0.1

## 1. 목적

SecureProbe AI Web Assessment의 Passive Tool인 `form_parser`를 구현한다.

이 Tool은 HTML 문서의 `<form>` 구조를 파싱하여 다음 정보를 Structured Model로 반환한다.

```text
Form Action
HTTP Method
Field Name
Field Type
```

이번 Task는 Form을 **분석만** 하며 제출하지 않는다.

금지:

```text
Form Submit
POST 실행
Login 시도
Credential 사용
CSRF 검증
SQLi/XSS Payload 삽입
자동 입력값 생성
취약점 판단
```

---

## 2. 작업 ID

```text
D08-T04 — form_parser
```

선행 작업:

```text
D08-T01 Safety Gate        COMPLETED
D08-T02 http_request       COMPLETED
D08-T03 endpoint_collector COMPLETED
```

다음 작업:

```text
D08-T05 — header_inspector
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

`DATA_SCHEMA_v0.1.md`의 Form 구조:

```json
{
  "action": "/login",
  "method": "POST",
  "fields": [
    {
      "name": "username",
      "type": "text"
    },
    {
      "name": "password",
      "type": "password"
    }
  ]
}
```

이번 Task는 이 구조를 실제 Pydantic Model로 구현한다.

---

## 4. 구현 위치

생성:

```text
secureprobe/web/tools/form_parser.py
```

Form Model은 기존:

```text
secureprobe/models/target.py
```

에 추가하는 것을 권장한다.

추가 Model:

```text
Form
FormField
```

수정 가능:

```text
secureprobe/models/target.py
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py
```

Unit Test:

```text
tests/unit/test_form_parser.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T04_FORM_PARSER_RESULT_v0.1.md
```

---

## 5. 네트워크 I/O 금지

`form_parser`는 HTML parser다.

다음 금지:

```text
httpx
requests
socket
DNS lookup
http_request 호출
Form Submit
```

입력:

```text
base_url
html
```

출력:

```text
list[Form]
```

---

## 6. Public API

권장:

```python
def parse_forms(
    *,
    base_url: str,
    html: str,
    scope: AssessmentScope | None = None,
    max_forms: int = 50,
    max_fields_per_form: int = 100,
) -> list[Form]:
    ...
```

---

## 7. FormField Model

권장:

```python
class FormField(BaseModel):
    name: str
    type: str
```

기본 정책:

```text
name: 빈 문자열 금지
type: normalized lowercase string
extra="forbid"
str_strip_whitespace=True
```

---

## 8. Form Model

권장:

```python
class Form(BaseModel):
    action: str
    method: Literal["GET", "POST"]
    fields: list[FormField] = Field(default_factory=list)
```

이번 v0.1에서는 기본적으로:

```text
action
method
fields
```

만 구현한다.

---

## 9. Action 정규화

Form action은 `base_url` 기준 절대 URL로 정규화한다.

예:

```html
<form action="/login">
```

base:

```text
http://localhost:5000/index
```

결과:

```text
http://localhost:5000/login
```

---

## 10. Missing Action

다음:

```html
<form method="post">
```

action이 없거나 빈 문자열이면:

```text
현재 base_url
```

을 사용한다.

---

## 11. Fragment 제거 / Query 보존

```text
/login#section → /login
/search?category=all → query 유지
```

---

## 12. Scheme 정책

허용 Action:

```text
http
https
relative URL
```

제외:

```text
javascript:
data:
mailto:
tel:
ftp:
file:
gopher:
ws:
wss:
```

---

## 13. Userinfo / Malformed Action

다음 Action은 제외한다.

```text
http://user:pass@localhost/
http://localhost@evil.com/
malformed URL
```

잘못된 Action 하나가 전체 Parser를 실패시키면 안 된다.

---

## 14. Method 정책

기본:

```text
GET
```

정규화:

```text
get  → GET
post → POST
```

허용:

```text
GET
POST
```

그 외 Method는 해당 Form을 제외한다.

---

## 15. Field 대상

최소 다음 Element를 분석한다.

```text
input
textarea
select
```

`button`은 이번 Task에서 제외한다.

---

## 16. Field Name

`name` 속성이 존재하는 Field만 수집한다.

제외:

```html
<input>
<input name="">
<input name="   ">
```

---

## 17. Field Type

### input

`type` 속성 사용.

없으면:

```text
text
```

### textarea

```text
textarea
```

### select

```text
select
```

---

## 18. Field Value 저장 금지

절대 저장하지 않는다.

```text
input value
textarea content
selected option value
hidden token value
password value
CSRF token value
Session value
```

예:

```html
<input name="password" value="secret123">
```

결과:

```text
name=password
type=password
```

만 존재해야 한다.

---

## 19. Hidden Field

구조 정보는 수집 가능.

```html
<input type="hidden" name="csrf_token" value="secret">
```

→

```text
name=csrf_token
type=hidden
```

value는 저장하지 않는다.

---

## 20. Duplicate Field

동일 Form 안에서 동일 `(name, type)` 반복 시 deterministic dedupe.

---

## 21. Form 수 제한

기본:

```text
max_forms = 50
```

허용 범위:

```text
1 ~ 200
```

---

## 22. Field 수 제한

기본:

```text
max_fields_per_form = 100
```

허용 범위:

```text
1 ~ 500
```

---

## 23. Limit Validation

다음은 실패:

```text
0
음수
상한 초과
bool
float
string
None
```

ValueError.

---

## 24. Deterministic Order

Form 순서:

```text
DOM 등장 순서
```

Field 순서:

```text
Form 내부 DOM 등장 순서
```

---

## 25. HTML Parser

기존:

```text
beautifulsoup4
```

사용.

```python
BeautifulSoup(html, "html.parser")
```

새 dependency 추가 금지.

---

## 26. base_url Validation

`base_url`은 유효한 HTTP(S) URL이어야 한다.

가능하면 기존 public Safety Gate:

```python
validate_web_target(..., active=False)
```

를 재사용한다.

네트워크 I/O는 발생하지 않는다.

---

## 27. Scope / Authorization

`form_parser`는 Authorization을 판단하지 않는다.

책임:

```text
Form Metadata 추출
```

실제 Action URL 요청 권한은 후속 `http_request` / Safety Gate가 판단한다.

---

## 28. 외부 Host Action

기본적으로 same-host Form만 유지한다.

추가 Host는 `AssessmentScope.allowed_hosts`에 포함된 경우에만 후보로 포함 가능하다.

`allowed_hosts`는 Authorization 증명이 아니다.

---

## 29. Localhost Spoofing

다음 Action은 허용하지 않는다.

```text
http://localhost.evil.com/login
```

정확한 Host 비교.

---

## 30. No Form Submit / Credential Handling

절대 수행하지 않는다.

```text
http_request 호출
GET/POST 요청
credentials 사용
login 시도
```

---

## 31. No CSRF / Authentication / Vulnerability Judgment

금지:

```text
CSRF 보호 있음/없음 판단
로그인 Form 확정
취약 Form 판단
File Upload 취약 판단
```

Form 구조만 반환한다.

---

## 32. No Ground Truth / Benchmark

금지:

```text
ground_truth
known_vulnerability
zap_result
semgrep_result
benchmark_result
```

---

## 33. Unit Test 파일

```text
tests/unit/test_form_parser.py
```

---

## 34. Unit Test — Basic Login Form

```html
<form action="/login" method="post">
  <input name="username" type="text">
  <input name="password" type="password">
</form>
```

검증:

```text
action absolute URL
method POST
fields 2개
username/text
password/password
```

---

## 35. Unit Test — Default / Missing Action

```html
<form action="/search">
```

→ GET.

```html
<form method="post">
```

→ current base URL.

---

## 36. Unit Test — Relative / Query / Fragment

검증:

```text
../login
/search?type=all
/login#form
```

정규화.

---

## 37. Unit Test — textarea/select/default input type

```html
<textarea name="content"></textarea>
<select name="role"></select>
<input name="username">
```

결과:

```text
content/textarea
role/select
username/text
```

---

## 38. Unit Test — Field Without Name

다음 제외:

```html
<input type="text">
<textarea></textarea>
<select name=""></select>
```

---

## 39. Unit Test — Secret Values Not Stored

HTML:

```html
<input type="password" name="password" value="super-secret">
<input type="hidden" name="csrf_token" value="token-secret">
<textarea name="memo">secret-text</textarea>
<select name="role"><option value="admin-secret">Admin</option></select>
```

결과 JSON 어디에도 다음이 없어야 한다.

```text
super-secret
token-secret
secret-text
admin-secret
```

---

## 40. Unit Test — Duplicate Field

동일 `(name,type)` 반복 시 deterministic dedupe.

---

## 41. Unit Test — Unsupported Method / Scheme

다음 Form 제외:

```text
method=delete
javascript:
data:
mailto:
ftp:
file:
```

---

## 42. Unit Test — Userinfo / External Host / Spoofed Host

제외:

```text
http://user:pass@localhost/login
https://example.com/login
http://localhost.evil.com/login
```

Scope 방식 채택 시 허용된 추가 Host만 후보 포함.

---

## 43. Unit Test — Malformed Action

잘못된 Form 하나가 있어도 정상 Form 파싱은 계속된다.

---

## 44. Unit Test — Empty HTML / No Forms

결과:

```text
[]
```

---

## 45. Unit Test — Form Limit / Field Limit

검증:

```text
max_forms
max_fields_per_form
```

상한 적용.

---

## 46. Unit Test — Invalid Limits

다음 실패:

```text
max_forms=0
max_forms=201
max_forms=True
max_fields_per_form=0
max_fields_per_form=501
```

---

## 47. Unit Test — Deterministic / Malformed HTML

동일 HTML 반복 결과 동일.

잘못 닫힌 HTML에서도 crash 금지.

---

## 48. Model Validation

FormField:

```text
name 빈 값 거부
extra field 거부
```

Form:

```text
action 빈 값 거부
method GET/POST만
extra field 거부
mutable default isolation
```

---

## 49. JSON Round-trip

```python
payload = form.model_dump(mode="json")
restored = Form.model_validate(payload)
```

PASS.

---

## 50. Import Validation

```bash
python -c "from secureprobe.web.tools.form_parser import parse_forms; from secureprobe.models import Form, FormField; print('IMPORT_OK')"
```

PASS.

---

## 51. 개별 Unit Test

```bash
pytest tests/unit/test_form_parser.py -q
```

PASS.

---

## 52. 전체 Regression

```bash
pytest -q
```

D08-T03 완료 시점의 실제 Regression을 기준으로
이번 실행의 실제 결과를 기록한다.

기존 숫자를 복사하지 않는다.

---

## 53. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T04_FORM_PARSER_RESULT_v0.1.md
```

---

## 54. Result Document 필수 내용

```text
Task ID
Status
Public API
Created Files
Modified Files
Form Model
FormField Model
Action Normalization
Method Policy
Field Policy
Sensitive Value Policy
Scope Policy
Limit Policy
Network I/O
Unit Test Result
Full Regression Result
Import Validation
Issues
Next Task
```

---

## 55. 책임 분리 기록

결과 문서에 반드시 다음을 기록한다.

```text
form_parser는 Form Metadata만 분석한다.

Form Submit은 수행하지 않는다.

Credentials를 사용하지 않는다.

CSRF/Authentication/Vulnerability 판단을 하지 않는다.

실제 요청 실행 허가는 Safety Gate/http_request가 담당한다.
```

---

## 56. 변경 가능 파일

```text
secureprobe/web/tools/form_parser.py
secureprobe/models/target.py
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py

tests/unit/test_form_parser.py

docs/05_ai_development/codex_results/day08/
D08-T04_FORM_PARSER_RESULT_v0.1.md
```

필요한 파일만 수정한다.

---

## 57. 수정 금지 파일

```text
secureprobe/core/safety.py
secureprobe/web/tools/http_request.py
secureprobe/web/tools/endpoint_collector.py

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

## 58. Dependency 정책

기존:

```text
beautifulsoup4
```

사용.

새 dependency 추가 금지.

---

## 59. 완료 체크리스트

```text
[ ] form_parser.py 생성
[ ] Form Model 구현
[ ] FormField Model 구현

[ ] action 절대 URL 정규화
[ ] missing action → base URL
[ ] fragment 제거
[ ] query 보존

[ ] GET/POST method 지원
[ ] unsupported method 제외

[ ] input 분석
[ ] textarea 분석
[ ] select 분석
[ ] field name 필수
[ ] input default type=text

[ ] password/hidden/textarea/select value 미저장
[ ] secret 값 serialization 미포함

[ ] unsupported scheme 제외
[ ] userinfo 제외
[ ] malformed action 개별 제외
[ ] same-host/scope 정책
[ ] spoofing 차단

[ ] max_forms 제한
[ ] max_fields_per_form 제한
[ ] deterministic order

[ ] network I/O 없음
[ ] Form Submit 없음
[ ] Credentials 사용 없음
[ ] CSRF 판단 없음
[ ] Authentication 판단 없음
[ ] 취약점 판단 없음
[ ] Ground Truth/Benchmark 사용 없음

[ ] Unit Test PASS
[ ] Full Regression PASS
[ ] Import PASS
[ ] Result Document 생성
```

---

## 60. 완료 조건

다음 조건을 모두 만족하면 D08-T04 완료다.

```text
HTML Form 구조 파싱 가능
Action 정규화
GET/POST 구분
Field Name/Type 수집
민감 Field Value 저장 없음
Scope 밖 Action 제외
Unsupported Scheme 제외
Malformed Form 개별 무시
Form/Field 수 제한
Network I/O 없음
Form Submit 없음
Unit Test PASS
Full Regression PASS
범위 확대 없음
```

---

## 61. 권장 Commit Message

```text
feat: add passive form parser
```

사용 금지:

```text
git commit --amend
git push --force
```

---

## 62. 완료 보고 형식

```text
D08-T04 FORM PARSER

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- Form model
- FormField model
- action normalization
- GET/POST metadata
- input/textarea/select field parsing
- sensitive value exclusion
- scope filtering
- form/field limits

Validation:
- Basic Form: PASS / FAIL
- Default Method: PASS / FAIL
- Missing Action: PASS / FAIL
- Relative Action: PASS / FAIL
- Query: PASS / FAIL
- Fragment Removal: PASS / FAIL
- textarea/select: PASS / FAIL
- Default Input Type: PASS / FAIL
- No-name Field: PASS / FAIL
- Secret Values Not Stored: PASS / FAIL
- Duplicate Fields: PASS / FAIL
- Unsupported Method: PASS / FAIL
- Unsupported Scheme: PASS / FAIL
- Userinfo: PASS / FAIL
- External Host: PASS / FAIL
- allowed_hosts: PASS / FAIL
- Spoofed Host: PASS / FAIL
- Malformed Action: PASS / FAIL
- Form Limit: PASS / FAIL
- Field Limit: PASS / FAIL
- Deterministic Order: PASS / FAIL
- Network I/O Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T04_FORM_PARSER_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T05 — header_inspector
```

---

## 63. 작업 종료 원칙

D08-T04 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T05 — header_inspector
```

SecureBoard가 Claude에서 전달되면
실제 Login/Register/Search Form을 이용한 Integration Test를 별도로 수행한다.
