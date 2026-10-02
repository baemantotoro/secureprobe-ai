# D08-T04 — Form Parser Result v0.1

## 1. Task ID / Status

Task ID: D08-T04

Status: COMPLETED

## 2. Public API

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

기존 dependency의 `BeautifulSoup(html, "html.parser")`로 HTML 한 문서의 Form Metadata를 분석한다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/web/tools/form_parser.py`
- `tests/unit/test_form_parser.py`
- `docs/05_ai_development/codex_results/day08/D08-T04_FORM_PARSER_RESULT_v0.1.md`

Modified Files:

- `secureprobe/models/target.py`: Form / FormField 추가.
- `secureprobe/models/__init__.py`: Form / FormField export 추가.

기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T04_FORM_PARSER_v0.1.md`도 내용 변경 없이 Git에 등록한다.
기존 Endpoint 정의, Safety Gate, HTTP Tool, Endpoint Collector, SecureBoard,
기준 문서 및 의존성을 변경하지 않았다.

## 4. Form Model / FormField Model

Form:

- `action`: 빈 문자열 및 공백 문자열 거부.
- `method`: GET / POST만 허용.
- `fields`: FormField 목록, instance별 독립 기본값.

FormField:

- `name`: 빈 문자열 및 공백 문자열 거부.
- `type`: 공백 제거 및 lowercase로 정규화한 비어 있지 않은 문자열.

두 모델 모두 `extra="forbid"`, `str_strip_whitespace=True`를 적용한다.
FormField의 value 및 Form의 Ground Truth / Benchmark 추가 필드를 거부한다.
JSON serialization / round-trip 및 mutable default isolation을 검증했다.

## 5. Action Normalization / Method Policy

Action은 base URL 기준 절대 URL로 정규화한다.
상대 URL, 부모 상대 URL, Root-relative 및 Scheme-relative URL을 지원한다.
action이 없거나 빈 문자열이면 현재 base URL을 사용한다.
Fragment를 제거하고 Query 문자열은 보존한다.
Scheme / Host를 lowercase로 변환하고 Host의 마지막 점 하나를 제거한다.
명시적 Port는 숫자로 정규화하여 유지하고 빈 path는 `/`로 정규화한다.

URL 검증은 기존 public `validate_web_target(..., active=False)`를 재사용한다.
http / https만 허용하며 Userinfo, malformed Action, 미지원 Scheme을 개별 제외한다.
urljoin이 제어문자나 잘못된 절대 URL을 숨기지 않도록 원시 Action도 검사한다.
잘못된 Action 하나 때문에 정상 Form 파싱이 중단되지 않는다.
HTML `<base>` 태그는 해석하지 않고 호출자가 전달한 base URL을 유지한다.
유효하지 않은 base URL 또는 문자열이 아닌 base_url/html 입력은 ValueError다.

Method는 공백 제거 및 uppercase로 정규화한다.
method 속성이 없으면 GET, GET / POST 외의 Method는 해당 Form을 제외한다.
POST Form은 Metadata로만 반환한다.

## 6. Field Policy / Sensitive Value Policy

input / textarea / select만 분석하며 button은 제외한다.
name이 없거나 빈 문자열·공백 문자열인 Field는 제외한다.
input type은 lowercase로 정규화하고 누락·빈 type은 text로 처리한다.
textarea / select는 각각 textarea / select 타입으로 기록한다.
중첩된 malformed Form에서도 Field를 가장 가까운 부모 Form에만 할당한다.
동일 Form의 `(name, type)` 중복은 최초 발견 기준으로 제거한다.

저장하는 Field 정보는 name / type뿐이다.
input value, password value, hidden token / CSRF token value,
textarea 내용, select option value 및 Session 값은 저장하지 않는다.
민감 테스트 문자열이 결과 JSON에 포함되지 않음을 검증했다.
Action Query 문자열 자체는 지침대로 보존한다.

## 7. Scope Policy / Limit Policy

기본적으로 base URL과 같은 canonical Host의 Form만 유지한다.
추가 Host는 `AssessmentScope.allowed_hosts`에 정확히 일치할 때 후보로 포함한다.
대소문자 및 마지막 점 하나를 정규화하며 Port는 Host 비교에서 제외한다.
부분 문자열, Wildcard 및 Scope 밖 Host 확장은 허용하지 않는다.
`localhost.evil.com` 등 위장 Host는 제외한다.
Path Scope 세부 enforcement는 이번 Task 범위에 포함하지 않는다.

Form Metadata 수집은 Authorization 증명이 아니다.
실제 요청 실행 허가는 Safety Gate / http_request가 담당한다.

Form 순서와 Field 순서는 DOM 등장 순서다.
기본 max_forms=50, 허용 integer 범위 1~200.
기본 max_fields_per_form=100, 허용 integer 범위 1~500.
무효 Form / Field를 제외하고 중복 Field를 제거한 후 앞에서부터 제한한다.
0, 음수, 상한 초과, bool, float, string, None 입력은 ValueError다.

## 8. Network I/O / Responsibility

Network I/O: None

form_parser는 Form Metadata만 분석한다.
Form Submit, GET / POST 요청, http_request 호출, Credentials 사용 및 Login 시도를 수행하지 않는다.
CSRF / Authentication / Vulnerability 판단을 하지 않는다.
Ground Truth / Benchmark 정보를 사용하지 않는다.
공격 Payload 생성, 자동 입력값 생성 및 Browser Automation이 없다.
Safety Gate 재사용은 입력 검증만 수행하므로 네트워크 I/O가 발생하지 않는다.

## 9. Unit Test Result / Full Regression Result

실행일: 2026-10-03 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_form_parser.py -q
```

```text
80 passed in 0.50s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
432 passed in 1.78s
```

기존 D08-T03까지의 352개와 새 Form Parser 테스트 80개가 모두 통과했다.
Unit Test는 순수 parser 테스트이며 네트워크 fixture를 사용하지 않는다.

## 10. Import Validation / Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.web.tools.form_parser import parse_forms; from secureprobe.models import Form, FormField; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

- Basic Form: PASS
- Default Method: PASS
- Missing Action: PASS
- Relative Action: PASS
- Query: PASS
- Fragment Removal: PASS
- textarea/select: PASS
- Default Input Type: PASS
- No-name Field: PASS
- Secret Values Not Stored: PASS
- Duplicate Fields: PASS
- Unsupported Method: PASS
- Unsupported Scheme: PASS
- Userinfo: PASS
- External Host: PASS
- allowed_hosts: PASS
- Spoofed Host: PASS
- Malformed Action: PASS
- Form Limit: PASS
- Field Limit: PASS
- Deterministic Order: PASS
- Model Validation / JSON Round-trip: PASS
- Network I/O Absent: PASS (코드 검토)
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

## 11. Issues

None

SecureBoard 전달 후 실제 Login / Register / Search Form을 이용한 Integration Test는 별도로 수행한다.

## 12. Next Task

D08-T05 — header_inspector

다음 Task는 자동 시작하지 않는다.
