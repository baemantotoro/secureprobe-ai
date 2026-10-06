# D08-T06 — Cookie Inspector Result v0.1

## 1. Task ID / Status

Task ID: D08-T06

Status: COMPLETED

## 2. Public API

```python
def inspect_cookies(
    *,
    set_cookie_headers: str | list[str],
    max_cookies: int = 50,
) -> list[CookieInfo]:
    ...
```

각 문자열은 독립된 Set-Cookie Header 한 개다.
단일 문자열은 한 개 목록으로 처리하고 list[str]는 입력 순서를 보존한다.
다른 타입과 비문자열 목록 항목은 ValueError다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/web/tools/cookie_inspector.py`
- `tests/unit/test_cookie_inspector.py`
- `docs/05_ai_development/codex_results/day08/D08-T06_COOKIE_INSPECTOR_RESULT_v0.1.md`

Modified Files:

- `secureprobe/models/target.py`: CookieInfo 추가.
- `secureprobe/models/__init__.py`: CookieInfo export 추가.

기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T06_COOKIE_INSPECTOR_v0.1.md`도 내용 변경 없이 Git에 등록한다.
기존 모델 정의, Safety Gate, HTTP/HTML/Header Tool, SecureBoard, 기준 문서 및 의존성은 변경하지 않았다.

## 4. CookieInfo Model / Cookie Name Policy / Sensitive Value Policy

CookieInfo 필드:

```text
name, secure, http_only, same_site, domain, path, max_age, expires
```

name은 빈 값과 공백 문자열을 거부한다.
secure / http_only는 strict bool이며 same_site는 Strict / Lax / None 문자열 또는 null이다.
extra forbid와 str_strip_whitespace를 적용한다.
Cookie Value 필드는 없으며 value, Severity, Ground Truth, Benchmark 등 추가 필드를 거부한다.
mutable default가 없으므로 별도 wrapper instance isolation 테스트는 불필요하다.

첫 name=value pair에서 유효한 token 형태의 Cookie name만 추출한다.
Cookie Value는 pair 추출 후 버리고 결과·로그·Cookie Jar에 저장하지 않는다.
비밀번호·Session·Token 테스트 원문이 결과 JSON에 포함되지 않음을 확인했다.
Quoted Cookie Value 내부의 세미콜론은 Attribute 경계로 해석하지 않는다.

## 5. Parser / Secure Policy / HttpOnly Policy / SameSite Policy

Python SimpleCookie 사용을 검토했다. 설치된 Python에서 미지원 `Priority=High`가
별도 Cookie로 파싱되거나 unknown flag가 있는 Header 전체가 누락될 수 있어,
따옴표 및 escape를 구분하는 작은 scanner로 세미콜론 경계를 처리한다.
새 dependency를 추가하지 않았다.

Attribute 이름은 case-insensitive다.
Secure / HttpOnly는 Attribute 존재 여부만 bool로 기록한다.
SameSite는 case-insensitive Strict / Lax / None을 canonical 값으로 정규화하고,
미지원 값은 null로 반환한다.
반복된 Attribute 값은 마지막 값을 사용한다.
Unknown Attribute(Priority / Partitioned / Foo 등)는 무시하며 새 Cookie나 모델 필드로 생성하지 않는다.

## 6. Domain/Path Policy / Max-Age/Expires Policy

Domain / Path는 공백 제거 후 Metadata로 보존하며 과도한 Host 정규화를 하지 않는다.
Quoted Metadata는 바깥 double quote를 제거한다.
Domain / Path / Expires 등 Metadata는 최대 2048 characters로 제한한다.

Max-Age는 정수 변환이 가능하면 기록하며 잘못된 값은 null이다.
음수와 0도 관찰 값으로 보존하고 수명·Session 판단은 하지 않는다.
2048자를 넘는 Max-Age는 잘라서 잘못된 숫자로 해석하지 않고 null로 처리한다.
Expires는 안전한 길이의 문자열로 기록하며 datetime parser를 추가하지 않는다.
Expires의 comma는 Cookie 분리 기준이 아니다.

## 7. Multiple Header Policy / Malformed Header Policy / Limit Policy

각 Header를 독립 CookieInfo로 반환한다.
Cookie name이 같아도 Domain / Path가 다를 수 있으므로 dedupe하지 않는다.
입력 Header 순서를 유지하며 동일 입력은 동일 결과를 반환한다.
단순 comma split은 사용하지 않는다. 합쳐진 여러 Cookie 문자열을 복원하는 기능은 제공하지 않는다.

빈 Header, name=value가 없는 Header, 빈/잘못된 name,
닫히지 않은 quote 등 malformed Header는 개별 무시한다.
CR/LF 및 Unicode control/format/surrogate 등 category C 문자가 있는 Header는 전체 제외한다.
8192 characters를 넘는 Header는 잘라서 파싱하지 않고 전체 제외한다.
잘못된 항목이 있어도 정상 Header 처리는 계속된다.

max_cookies 기본 50, 허용 integer 범위 1~200이다.
0 / 음수 / 상한 초과 / bool / float / string / None은 ValueError다.
정상 파싱된 Cookie를 입력 순서대로 제한하며 무효 Header는 개수에 포함하지 않는다.

## 8. Network I/O / Session Replay / Vulnerability Judgment

Network I/O: None

cookie_inspector는 Set-Cookie Metadata만 분석한다.
Cookie Value를 저장하지 않는다.
Cookie Header 생성·Cookie Jar 저장·Cookie 재전송·Session 유지·Credentials 사용이 없다.
HTTP 요청과 DNS lookup을 수행하지 않는다.
Secure / HttpOnly / SameSite 누락을 취약점으로 확정하지 않는다.
Session / CSRF / Session Fixation 판단을 하지 않는다.
Severity / OWASP / CWE / Finding 생성은 Analyzer 단계 책임이다.
Ground Truth / ZAP / Semgrep 비교 및 Report 생성을 하지 않는다.

입력은 획득 시점의 원래 Set-Cookie Header를 전제로 한다.
D08-T02의 저장용 `***MASKED***` 값으로는 Attribute를 복원할 수 없으므로,
후속 통합은 원문을 일시적으로 Parser에 전달하고 Metadata만 보존해야 한다.
이번 Task에서는 HTTP Tool을 변경하지 않았다.

## 9. Unit Test Result / Full Regression Result

실행일: 2026-10-06 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_cookie_inspector.py -q
```

```text
71 passed in 0.42s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
567 passed in 3.01s
```

기존 496개와 Cookie Inspector 테스트 71개가 모두 통과했다.
Unit Test는 문자열 입력을 사용하며 네트워크 fixture가 필요하지 않다.

## 10. Import Validation / Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.web.tools.cookie_inspector import inspect_cookies; from secureprobe.models import CookieInfo; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

- Basic Cookie: PASS
- Secure: PASS
- HttpOnly: PASS
- SameSite Strict / Lax / None / Invalid: PASS
- Domain / Path: PASS
- Max-Age / Expires: PASS
- Multiple Headers: PASS
- Quoted Value: PASS
- Sensitive Value Not Stored: PASS
- Malformed Header: PASS
- Duplicate Name: PASS
- Case Insensitive Attribute: PASS
- Unknown Attribute: PASS
- Control Character: PASS
- Oversized Header / Attribute Limit: PASS
- Cookie Limit: PASS
- Deterministic Order: PASS
- Model Validation / JSON Round-trip: PASS
- Network I/O Absent: PASS (코드 검토)
- Cookie Replay Absent: PASS (코드 검토)
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

## 11. Issues

None

SecureBoard 전달 후 실제 Set-Cookie Header 기반 Integration Test는 별도로 수행한다.

## 12. Next Task

D08-T07 — WebTargetContext 생성

다음 Task는 자동 시작하지 않는다.
