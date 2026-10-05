# D08-T05 — Header Inspector Implementation v0.1

## 1. 목적

SecureProbe AI Web Assessment의 Passive Tool인 `header_inspector`를 구현한다.

이 Tool은 이미 확보된 HTTP Response Header를 입력으로 받아 보안 관련 Header의 존재 여부와 관찰 정보를 Structured Output으로 반환한다.

```text
HTTP Response Headers
        ↓
header_inspector
        ↓
Header Observation
```

이번 Task는 취약점 확정, Severity 결정, OWASP/CWE Mapping, Finding 생성을 하지 않는다.

---

## 2. 작업 ID

```text
D08-T05 — header_inspector
```

선행 작업:

```text
D08-T01 Safety Gate        COMPLETED
D08-T02 http_request       COMPLETED
D08-T03 endpoint_collector COMPLETED
D08-T04 form_parser        선행 완료 전제
```

다음 작업:

```text
D08-T06 — cookie_inspector
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

## 3. 핵심 책임

`header_inspector` 담당:

```text
Response Header 이름 정규화
Security-relevant Header 존재 여부 확인
Header Value의 안전한 metadata 추출
HTTPS 문맥에서 HSTS 관찰
민감 Header 값 미노출
Structured Observation 반환
```

담당하지 않음:

```text
HTTP 요청
Cookie 분석
취약점 확정
Severity 결정
OWASP/CWE Mapping
Finding 생성
Ground Truth 비교
ZAP/Semgrep 비교
Report 생성
```

---

## 4. 구현 위치

생성:

```text
secureprobe/web/tools/header_inspector.py
```

Model 추가 권장:

```text
secureprobe/models/target.py
```

추가 Model 예:

```text
HeaderObservation
HeaderInspectionResult
```

필요 시 수정:

```text
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py
```

Unit Test:

```text
tests/unit/test_header_inspector.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T05_HEADER_INSPECTOR_RESULT_v0.1.md
```

---

## 5. 네트워크 I/O 금지

이번 Tool은 Response Header Parser다.

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
url
headers
```

출력:

```text
HeaderInspectionResult
```

---

## 6. Public API

권장:

```python
def inspect_headers(
    *,
    url: str,
    headers: Mapping[str, str] | dict[str, str],
) -> HeaderInspectionResult:
    ...
```

입력 Header는 D08-T02 `http_request`에서 이미 확보한 Response Header를 전제로 한다.

---

## 7. HeaderObservation Model

권장:

```python
class HeaderObservation(BaseModel):
    name: str
    present: bool
    value: str | None = None
    note: str | None = None
```

`note`는 취약점 판단이 아니라 관찰 설명만 허용한다.

예:

```text
present
not present
HSTS is only effective over HTTPS
value truncated
```

---

## 8. HeaderInspectionResult Model

권장:

```python
class HeaderInspectionResult(BaseModel):
    url: str
    scheme: Literal["http", "https"]
    observations: list[HeaderObservation]
```

필요 시 최소 확장만 허용한다.

---

## 9. Header Key 정규화

Header 비교는 case-insensitive 해야 한다.

```text
content-security-policy
Content-Security-Policy
CONTENT-SECURITY-POLICY
```

을 동일 Header로 처리한다.

비교는 lowercase, 출력 name은 canonical 형태 사용을 권장한다.

---

## 10. 최소 분석 대상

이번 v0.1은 아래 8개만 분석한다.

```text
Content-Security-Policy
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
Strict-Transport-Security
Cache-Control
Pragma
```

추가 Header 분석은 범위 밖이다.

---

## 11. 개별 Header 관찰 정책

각 Header는 기본적으로 다음만 기록한다.

```text
name
present
value
note(optional)
```

### Content-Security-Policy

```text
present/value 관찰
Directive 강도 평가 금지
```

### X-Content-Type-Options

```text
present/value 관찰
nosniff 여부를 값으로 볼 수 있으나 취약 판정 금지
```

### X-Frame-Options

```text
present/value 관찰
DENY/SAMEORIGIN 값 판단은 Analyzer 단계
```

### Referrer-Policy

```text
present/value 관찰
정책 강도 판단 금지
```

### Permissions-Policy

```text
present/value 관찰
Directive parser 구현 금지
```

### Strict-Transport-Security

HTTPS URL에서는 일반 관찰.

HTTP URL에서는 Header 존재 여부는 기록 가능하지만:

```text
note="HSTS is only effective over HTTPS"
```

정도의 문맥 설명만 허용한다.

### Cache-Control / Pragma

```text
present/value 관찰
cache directive 취약 판단 금지
```

---

## 12. Set-Cookie 책임 분리

`Set-Cookie`는 이번 Tool의 분석 대상이 아니다.

담당:

```text
D08-T06 — cookie_inspector
```

금지:

```text
Cookie Attribute 분석
Secure 판단
HttpOnly 판단
SameSite 판단
Session 판단
```

---

## 13. 민감 Header 정책

다음 Header 값은 절대 그대로 출력하지 않는다.

```text
Authorization
Proxy-Authorization
Set-Cookie
WWW-Authenticate
X-Api-Key
API-Key
```

분석 대상이 아니므로 기본적으로 Observation에서 제외한다.
필요한 경우 내부 sanitize 과정에서 `***MASKED***` 처리한다.

결과 serialization에 secret 원문이 존재하면 안 된다.

---

## 14. Raw Header 전체 복사 금지

결과에 Response Header 전체 dict를 그대로 저장하지 않는다.

이유:

```text
민감값 유출 방지
Scope 최소화
Structured Output 유지
```

분석 대상 8개 Header의 관찰 결과만 반환한다.

---

## 15. URL Validation

`url`은 유효한 http/https absolute URL이어야 한다.

가능하면 기존 public Safety Gate의 passive validation을 재사용한다.
네트워크 I/O는 없어야 한다.

차단:

```text
ftp://
relative/path
userinfo URL
malformed URL
```

---

## 16. Header Input Validation

허용:

```text
dict[str, str]
Mapping[str, str]
```

거부:

```text
None
list
string
```

명확한 ValueError 또는 ValidationError로 처리한다.

---

## 17. Empty Header

입력:

```python
{}
```

허용.

결과:

```text
8개 분석 대상 모두 present=False
value=None
```

---

## 18. Header Value 정책

기본:

```text
leading/trailing whitespace 제거
```

과도한 Header Value 저장 방지를 위해 권장 제한:

```text
max_header_value_chars = 4096
```

초과 시 truncate하고 note로 표시한다.

---

## 19. Control Character

Header Value의 CR/LF/control character는 결과에 그대로 남기지 않는다.

권장:

```text
sanitize 또는 해당 값 제외
```

Tool 전체 crash 금지.

---

## 20. Unknown Header

다음과 같은 분석 대상 외 Header는 기본적으로 무시한다.

```text
Server
Date
Content-Length
ETag
X-Powered-By
```

Observation 목록은 8개 대상으로 고정한다.

---

## 21. Deterministic Order

Observation 순서는 반드시 고정한다.

```text
1. Content-Security-Policy
2. X-Content-Type-Options
3. X-Frame-Options
4. Referrer-Policy
5. Permissions-Policy
6. Strict-Transport-Security
7. Cache-Control
8. Pragma
```

동일 입력 → 동일 결과.

---

## 22. No Vulnerability Judgment

금지:

```text
Missing CSP vulnerability
Clickjacking vulnerable
Weak Referrer Policy
HSTS missing finding
Security Misconfiguration
```

이번 Tool은 Observation만 생성한다.

---

## 23. No Severity / OWASP / CWE / Finding

다음 생성 금지:

```text
Severity
OWASP Mapping
CWE Mapping
CandidateFinding
Finding
```

Analyzer 단계 책임이다.

---

## 24. No Ground Truth / Benchmark

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

## 25. Unit Test 파일

```text
tests/unit/test_header_inspector.py
```

---

## 26. Unit Test — All Headers Present

8개 Header 모두 입력.

검증:

```text
모두 present=True
고정 순서 유지
value 안전 저장
```

---

## 27. Unit Test — Empty Headers

```python
{}
```

검증:

```text
8개 모두 present=False
value=None
```

---

## 28. Unit Test — Case Insensitive

입력:

```text
content-security-policy
X-CONTENT-TYPE-OPTIONS
x-frame-options
```

정상 인식.

---

## 29. Unit Test — HSTS HTTPS / HTTP

HTTPS:

```text
https://localhost
```

정상 관찰.

HTTP:

```text
http://localhost
```

HSTS가 있어도 취약 판단 없이 HTTPS에서만 의미 있다는 note만 허용.

---

## 30. Unit Test — Sensitive Header Exclusion

입력:

```text
Authorization: Bearer super-secret
Proxy-Authorization: Basic super-secret
Set-Cookie: session=super-secret
WWW-Authenticate: Basic realm="secret"
X-Api-Key: super-secret
```

결과 JSON에:

```text
super-secret
```

이 존재하면 안 된다.

---

## 31. Unit Test — Set-Cookie Not Inspected

`Set-Cookie`가 있어도 Cookie 분석 Observation을 생성하지 않는다.

---

## 32. Unit Test — Unknown Headers Ignored

입력:

```text
Server
Date
ETag
X-Powered-By
```

결과 대상은 기존 8개만 유지.

---

## 33. Unit Test — Large Header Value

4096자 초과 값 입력.

검증:

```text
무제한 저장 없음
truncate 정책 동작
```

---

## 34. Unit Test — Control Character

CR/LF 포함 값이 원형 그대로 결과에 남지 않아야 한다.

---

## 35. Unit Test — Invalid URL

```text
ftp://localhost
relative/path
http://user:pass@localhost
```

명확히 실패.

---

## 36. Unit Test — Invalid Header Input

```text
None
[]
"headers"
```

실패.

---

## 37. Unit Test — Deterministic Order

동일 입력 반복 시 Observation 순서와 값 동일.

---

## 38. Model Validation

HeaderObservation:

```text
name 빈 값 금지
present bool
extra forbid
```

HeaderInspectionResult:

```text
url 필수
scheme http/https
observations list
extra forbid
```

Mutable default isolation도 검증한다.

---

## 39. JSON Round-trip

```python
payload = result.model_dump(mode="json")
restored = HeaderInspectionResult.model_validate(payload)
```

PASS.

---

## 40. Import Validation

```bash
python -c "from secureprobe.web.tools.header_inspector import inspect_headers; from secureprobe.models import HeaderObservation, HeaderInspectionResult; print('IMPORT_OK')"
```

PASS.

---

## 41. 개별 Unit Test

```bash
pytest tests/unit/test_header_inspector.py -q
```

PASS.

---

## 42. 전체 Regression

```bash
pytest -q
```

실제 실행 결과를 기록한다.
기존 test 수치를 복사하지 않는다.

---

## 43. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T05_HEADER_INSPECTOR_RESULT_v0.1.md
```

---

## 44. Result Document 필수 내용

```text
Task ID
Status
Public API
Created Files
Modified Files
Observed Headers
Header Key Normalization
Sensitive Header Policy
HSTS Scheme Policy
Value Length Policy
Network I/O
Cookie Analysis
Vulnerability Judgment
Unit Test Result
Full Regression Result
Import Validation
Issues
Next Task
```

---

## 45. 책임 분리 기록

결과 문서에 다음을 반드시 명시한다.

```text
header_inspector는 Response Header metadata만 관찰한다.

HTTP 요청은 수행하지 않는다.

Set-Cookie 분석은 D08-T06 cookie_inspector 책임이다.

Header 누락을 취약점으로 확정하지 않는다.

Severity / OWASP / CWE / Finding 생성은 Analyzer 단계 책임이다.
```

---

## 46. 변경 가능 파일

```text
secureprobe/web/tools/header_inspector.py
secureprobe/models/target.py
secureprobe/models/__init__.py
secureprobe/web/tools/__init__.py

tests/unit/test_header_inspector.py

docs/05_ai_development/codex_results/day08/
D08-T05_HEADER_INSPECTOR_RESULT_v0.1.md
```

필요한 파일만 수정한다.

---

## 47. 수정 금지 파일

```text
secureprobe/core/safety.py
secureprobe/web/tools/http_request.py
secureprobe/web/tools/endpoint_collector.py
secureprobe/web/tools/form_parser.py

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

## 48. Dependency 정책

새 dependency 추가 금지.

Python 표준 라이브러리 + 기존 Pydantic만 사용한다.

---

## 49. 완료 체크리스트

```text
[ ] header_inspector.py 생성
[ ] HeaderObservation Model
[ ] HeaderInspectionResult Model

[ ] CSP 관찰
[ ] X-Content-Type-Options 관찰
[ ] X-Frame-Options 관찰
[ ] Referrer-Policy 관찰
[ ] Permissions-Policy 관찰
[ ] HSTS 관찰
[ ] Cache-Control 관찰
[ ] Pragma 관찰

[ ] case-insensitive Header 처리
[ ] deterministic order
[ ] http/https URL validation

[ ] Authorization 값 미노출
[ ] Proxy-Authorization 값 미노출
[ ] Set-Cookie 값 미노출
[ ] WWW-Authenticate 값 미노출
[ ] API Key 값 미노출

[ ] Set-Cookie 분석 없음
[ ] Cookie Attribute 판단 없음

[ ] Header value 길이 제한
[ ] control character 안전 처리

[ ] network I/O 없음
[ ] HTTP request 없음
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

## 50. 완료 조건

다음 조건을 모두 만족하면 D08-T05 완료다.

```text
8개 Security-relevant Header 구조적 관찰 가능
Case-insensitive Header 처리
Sensitive Header Value 미노출
HSTS HTTP/HTTPS 문맥 구분
Header Value 크기 제한
Cookie 분석 책임 분리
Network I/O 없음
취약점 확정 없음
Unit Test PASS
Full Regression PASS
범위 확대 없음
```

---

## 51. 권장 Commit Message

```text
feat: add passive header inspector
```

사용 금지:

```text
git commit --amend
git push --force
```

---

## 52. 완료 보고 형식

```text
D08-T05 HEADER INSPECTOR

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- security header observations
- case-insensitive normalization
- sensitive header protection
- HSTS scheme context
- deterministic output

Validation:
- CSP: PASS / FAIL
- X-Content-Type-Options: PASS / FAIL
- X-Frame-Options: PASS / FAIL
- Referrer-Policy: PASS / FAIL
- Permissions-Policy: PASS / FAIL
- HSTS HTTPS: PASS / FAIL
- HSTS HTTP Context: PASS / FAIL
- Cache-Control: PASS / FAIL
- Pragma: PASS / FAIL
- Case Insensitive: PASS / FAIL
- Sensitive Header Protection: PASS / FAIL
- Set-Cookie Not Inspected: PASS / FAIL
- Unknown Headers Ignored: PASS / FAIL
- Header Value Limit: PASS / FAIL
- Control Character Handling: PASS / FAIL
- Deterministic Order: PASS / FAIL
- Network I/O Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T05_HEADER_INSPECTOR_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T06 — cookie_inspector
```

---

## 53. 작업 종료 원칙

D08-T05 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T06 — cookie_inspector
```

SecureBoard가 Claude에서 전달되면 실제 Response Header 기반 Integration Test를 별도로 수행한다.
