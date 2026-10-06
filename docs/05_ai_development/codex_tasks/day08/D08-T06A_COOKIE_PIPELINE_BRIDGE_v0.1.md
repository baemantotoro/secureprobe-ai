# D08-T06A — Cookie Metadata Pipeline Bridge v0.1

## 1. 목적

D08-T02 `http_request`와 D08-T06 `cookie_inspector` 사이의 Cookie Metadata 전달 경로를 연결한다.

현재:

```text
HTTP Response
    ↓
http_request
    ↓
Set-Cookie → ***MASKED***
    ↓
ToolExecution.output
```

보안상 Raw Cookie Value를 저장하지 않는 방향은 맞지만,
`cookie_inspector`가 Secure / HttpOnly / SameSite 등을 분석하려면
원본 `Set-Cookie` 문자열이 잠시 필요하다.

이번 Task의 목표:

```text
HTTP Response
    ↓
raw Set-Cookie
    ↓  [memory only / transient]
cookie_inspector
    ↓
CookieInfo[]
    ↓
ToolExecution.output["cookies"]

동시에:

ToolExecution.output["headers"]["set-cookie"]
=
"***MASKED***"
```

즉:

```text
Raw Cookie Value 영구 저장 금지
Cookie Metadata만 저장
```

를 보장한다.

---

## 2. 작업 ID

```text
D08-T06A — Cookie Metadata Pipeline Bridge
```

성격:

```text
Integration Gap Correction
Scope Expansion 아님
```

선행 작업:

```text
D08-T01 Safety Gate          COMPLETED
D08-T02 http_request         COMPLETED
D08-T03 endpoint_collector   COMPLETED
D08-T04 form_parser          COMPLETED
D08-T05 header_inspector     COMPLETED
D08-T06 cookie_inspector     COMPLETED
```

다음 작업:

```text
D08-T07 — WebTargetContext 생성
```

---

## 3. 기준 문서

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

기존 구현 기준:

```text
secureprobe/web/tools/http_request.py
secureprobe/web/tools/cookie_inspector.py
secureprobe/models/target.py
secureprobe/models/tool.py
```

---

## 4. 핵심 보안 원칙

반드시 유지한다.

```text
Raw Cookie Value를 저장하지 않는다.

Raw Set-Cookie를:
- ToolExecution.output
- ToolExecution.input
- 로그
- Exception message
- Result Document
- Report
- Evidence file
- 테스트 assertion 출력

어디에도 영구 저장하지 않는다.
```

원본 `Set-Cookie`는:

```text
HTTP response object
→ memory only
→ cookie_inspector
→ CookieInfo metadata 생성
→ 즉시 폐기
```

흐름에서만 사용한다.

---

## 5. 변경 방향

가장 단순한 방식으로 `http_request`의 최종 Response 처리 지점에서
`cookie_inspector.inspect_cookies()`를 호출한다.

권장 흐름:

```python
raw_set_cookie_headers = response.headers.get_list("set-cookie")

cookies = inspect_cookies(
    set_cookie_headers=raw_set_cookie_headers
)

output = {
    "status_code": ...,
    "headers": _response_headers(response),
    "cookies": [cookie.model_dump(mode="json") for cookie in cookies],
    ...
}
```

중요:

```text
raw_set_cookie_headers
```

변수는 메모리에서만 사용한다.

---

## 6. Multiple Set-Cookie 처리

복수 Header를 손실 없이 가져온다.

권장:

```python
response.headers.get_list("set-cookie")
```

단순:

```python
response.headers.get("set-cookie")
```

만 사용하면 여러 Header가 합쳐질 수 있으므로
이번 Bridge에서는 복수 Header를 정확히 전달한다.

---

## 7. Comma Split 금지

다음 금지:

```python
response.headers["set-cookie"].split(",")
```

이유:

```text
Expires=Wed, 21 Oct ...
```

의 comma 때문에 Cookie Header가 잘못 분리될 수 있다.

---

## 8. Final Response Cookie 정책

이번 v0.1에서는:

```text
최종 Response의 Set-Cookie만 CookieInfo로 저장
```

한다.

Redirect 중간 Response의 Cookie Metadata는 저장하지 않는다.

이유:

```text
구현 단순성
최종 WebTargetContext 중심
Redirect Cookie Session 유지 방지
```

---

## 9. Redirect Cookie Replay 금지

기존 D08-T02 정책을 그대로 유지한다.

현재:

```python
client.cookies.clear()
```

를 통해 redirect 과정에서 Server-issued Cookie를 재전송하지 않는다.

이번 Task에서 다음을 추가하면 안 된다.

```text
Cookie Jar 유지
redirect cookie replay
login session
automatic auth session
```

---

## 10. Redirect 중간 Cookie

예:

```text
/a
→ 302 Set-Cookie: temp=secret
→ /b
→ 200 Set-Cookie: session=secret2
```

권장 최종 결과:

```text
cookies:
session metadata only
```

`temp` Cookie는 보존하지 않는다.

---

## 11. Header Masking 유지

기존 `_response_headers(response)` 정책을 유지한다.

즉:

```text
Set-Cookie → ***MASKED***
Authorization → ***MASKED***
Proxy-Authorization → ***MASKED***
Cookie → ***MASKED***
WWW-Authenticate → ***MASKED***
API Key 계열 → ***MASKED***
```

기존 보안정책을 약화시키지 않는다.

---

## 12. ToolExecution.output 확장

기존 Output:

```text
status_code
headers
content_type
body_excerpt
body_truncated
content_length
elapsed_ms
final_url
redirect_chain
```

이번 Task에서 추가:

```text
cookies
```

예:

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

---

## 13. Raw Cookie Value 금지 확인

다음 Output은 절대 금지:

```json
{
  "raw_set_cookie": "SESSION=secret"
}
```

또는:

```json
{
  "set_cookie_headers": [
    "SESSION=secret"
  ]
}
```

또는:

```json
{
  "cookies": [
    {
      "name": "SESSION",
      "value": "secret"
    }
  ]
}
```

---

## 14. CookieInfo / cookie_inspector 재사용

새 Cookie Model이나 parsing logic을 만들지 않는다.

반드시 기존:

```text
secureprobe.models.CookieInfo
secureprobe.web.tools.cookie_inspector.inspect_cookies
```

를 재사용한다.

---

## 15. 책임 분리

```text
http_request
→ HTTP Response 수집
→ transient raw Set-Cookie 확보
→ cookie_inspector 호출
→ metadata 반환

cookie_inspector
→ Set-Cookie parsing
→ CookieInfo 생성

Analyzer
→ Cookie 설정의 보안 의미 판단
```

---

## 16. 취약점 판단 금지

이번 Bridge에서 다음 판단 금지:

```text
Secure missing
HttpOnly missing
SameSite weak
Cookie misconfiguration
Session weakness
```

단순 Metadata 연결만 수행한다.

---

## 17. Severity / OWASP / CWE / Finding 금지

다음 생성 금지:

```text
LOW
MEDIUM
HIGH
CRITICAL
OWASP mapping
CWE mapping
CandidateFinding
Finding
Evidence
```

---

## 18. Ground Truth / Benchmark 금지

사용 금지:

```text
ground_truth
known_vulnerability
expected_ground_truth
zap_result
semgrep_result
benchmark_result
```

---

## 19. Error 처리

`cookie_inspector`는 malformed Cookie를 개별 무시한다.

따라서 일반적인 잘못된 Cookie 때문에 HTTP 요청 전체를 실패시키지 않는다.

원칙:

```text
HTTP request SUCCESS
+
cookies=[]
```

가능.

예상치 못한 parser 예외가 발생해도 Raw Cookie 값을 Exception message에 포함하지 않는다.

---

## 20. Empty Set-Cookie

Set-Cookie가 없으면:

```json
"cookies": []
```

를 반환한다.

`cookies` 필드는 항상 존재하도록 한다.

---

## 21. Serialization

`CookieInfo`는:

```python
cookie.model_dump(mode="json")
```

으로 JSON-safe dict로 변환한다.

Pydantic object 자체를 `ToolExecution.output`에 직접 넣지 않는다.

---

## 22. Unit Test 위치

기존:

```text
tests/unit/test_http_request.py
```

에 통합 Test를 추가하는 것을 권장한다.

또는 별도:

```text
tests/unit/test_cookie_pipeline.py
```

생성 가능.

둘 다 만들 필요는 없다.

---

## 23. Unit Test — No Cookie

Mock Response:

```text
200 OK
Set-Cookie 없음
```

검증:

```text
status=SUCCESS
output["cookies"] == []
```

---

## 24. Unit Test — Basic Cookie Metadata

Mock:

```text
Set-Cookie:
SESSION=super-secret; Secure; HttpOnly; SameSite=Lax; Path=/
```

검증:

```text
cookies[0].name == SESSION
secure == True
http_only == True
same_site == Lax
path == /
```

그리고:

```text
super-secret
```

이 전체 `ToolExecution.model_dump_json()`에 존재하면 안 된다.

---

## 25. Unit Test — Header Masking 유지

동일 Response에서:

```text
output["headers"]["set-cookie"]
```

는 반드시:

```text
***MASKED***
```

여야 한다.

---

## 26. Unit Test — Multiple Set-Cookie

MockTransport에서 복수 Header 제공.

예:

```text
Set-Cookie: SESSION=secret1; Secure; HttpOnly
Set-Cookie: theme=secret2; SameSite=Lax; Path=/
```

결과:

```text
cookies 2개
```

입력 순서 유지.

그리고:

```text
secret1
secret2
```

결과 JSON에 없어야 한다.

---

## 27. Unit Test — Expires Comma

Mock:

```text
Set-Cookie:
id=secret; Expires=Wed, 21 Oct 2026 07:28:00 GMT
```

Cookie 1개로 처리.

---

## 28. Unit Test — Duplicate Cookie Name

```text
id=secret1; Path=/
id=secret2; Path=/admin
```

CookieInfo 2개 유지.

---

## 29. Unit Test — Malformed + Valid

Mock:

```text
Set-Cookie: broken
Set-Cookie: SESSION=secret; Secure
```

결과:

```text
SESSION metadata 1개
```

HTTP request 자체는 SUCCESS.

---

## 30. Unit Test — Redirect Cookie Not Replayed

첫 Response:

```text
302
Set-Cookie: temp=redirect-secret
Location: /final
```

두 번째 요청 Header에:

```text
Cookie
```

가 없어야 한다.

---

## 31. Unit Test — Intermediate Redirect Cookie Not Stored

최종 Response에 Set-Cookie가 없으면:

```text
output["cookies"] == []
```

이어야 한다.

중간 302의 Cookie Metadata를 최종 Output에 포함하지 않는다.

---

## 32. Unit Test — Final Redirect Cookie Stored As Metadata

```text
302 → /final
200 Set-Cookie: SESSION=final-secret; HttpOnly
```

최종 Output:

```text
SESSION metadata 포함
```

`final-secret`은 포함하지 않는다.

---

## 33. Unit Test — Sensitive Value Non-Retention

최종:

```python
serialized = result.model_dump_json()
```

에서 다음 문자열이 모두 없어야 한다.

```text
super-secret
redirect-secret
final-secret
private-cookie-value
```

---

## 34. Unit Test — Tool Input Non-Retention

`ToolExecution.input`에도 Cookie raw value가 없어야 한다.

검증:

```text
result.input
```

에:

```text
raw Set-Cookie
cookie value
```

없음.

---

## 35. Unit Test — Serialization

```python
payload = result.model_dump(mode="json")
```

JSON serialization 성공.

`cookies`는 dict/list 기반.

---

## 36. 기존 회귀 테스트 유지

기존 `http_request`의 다음 테스트가 모두 계속 PASS해야 한다.

```text
GET/HEAD
Safety Gate
Scope
Timeout
Network Error
Body Limit
Binary Response
Header Masking
Redirect Disabled
Redirect In-Scope
Redirect Out-of-Scope
Redirect Limit
Cookie Replay Absent
TLS verify=True
trust_env=False
```

---

## 37. Test 실행

개별:

```bash
pytest tests/unit/test_http_request.py -q
```

또는 별도 Bridge Test 파일을 선택했다면 해당 파일.

전체:

```bash
pytest -q
```

실제 결과를 새로 기록한다.

기존 test 숫자를 복사하지 않는다.

---

## 38. Import Validation

```bash
python -c "from secureprobe.web.tools.http_request import http_request; from secureprobe.web.tools.cookie_inspector import inspect_cookies; print('IMPORT_OK')"
```

PASS.

---

## 39. 코드 검토 기준

최종 `http_request.py`에서 확인:

```text
response.headers.get_list("set-cookie") 사용

inspect_cookies 호출

raw cookie variable이
output/input/log/error에 들어가지 않음

_response_headers(response)의
Set-Cookie masking 유지

redirect 중간 Cookie 저장 없음
```

---

## 40. 변경 가능 파일

주요 수정:

```text
secureprobe/web/tools/http_request.py
tests/unit/test_http_request.py
```

또는 Test 분리 시:

```text
tests/unit/test_cookie_pipeline.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T06A_COOKIE_PIPELINE_BRIDGE_RESULT_v0.1.md
```

필요한 경우에만:

```text
secureprobe/web/tools/__init__.py
```

---

## 41. 수정 금지 파일

```text
secureprobe/core/safety.py

secureprobe/web/tools/endpoint_collector.py
secureprobe/web/tools/form_parser.py
secureprobe/web/tools/header_inspector.py
secureprobe/web/tools/cookie_inspector.py

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

`cookie_inspector.py`는 이미 완료된 Parser이므로 이번 Bridge에서 수정하지 않는다.

---

## 42. Dependency 정책

새 dependency 추가 금지.

기존:

```text
httpx
pydantic
```

만 사용한다.

---

## 43. Result Document

생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T06A_COOKIE_PIPELINE_BRIDGE_RESULT_v0.1.md
```

---

## 44. Result Document 필수 내용

```text
Task ID
Status
Reason for Bridge
Modified Files
Transient Cookie Flow
Raw Cookie Retention Policy
Final Response Policy
Redirect Cookie Policy
Multiple Set-Cookie Policy
Header Masking Policy
ToolExecution Output Change
Unit Test Result
Full Regression Result
Import Validation
Security Review
Issues
Next Task
```

---

## 45. 결과 문서에 반드시 기록

```text
HTTP Response Raw Set-Cookie
        ↓
Transient Memory Only
        ↓
cookie_inspector
        ↓
CookieInfo Metadata
        ↓
ToolExecution.output["cookies"]

Raw Set-Cookie:
NOT STORED
```

---

## 46. Security Review 항목

```text
Raw Cookie in ToolExecution.output: PASS / FAIL
Raw Cookie in ToolExecution.input: PASS / FAIL
Raw Cookie in Logs: PASS / FAIL
Raw Cookie in Errors: PASS / FAIL
Header Set-Cookie Masking: PASS / FAIL
Multiple Set-Cookie Metadata: PASS / FAIL
Redirect Cookie Replay Absent: PASS / FAIL
Intermediate Redirect Cookie Not Stored: PASS / FAIL
Final Cookie Metadata Only: PASS / FAIL
```

---

## 47. 완료 체크리스트

```text
[ ] http_request → cookie_inspector 연결

[ ] response.headers.get_list("set-cookie") 사용
[ ] 복수 Set-Cookie 보존
[ ] comma split 없음

[ ] raw Set-Cookie memory only
[ ] raw cookie value output에 없음
[ ] raw cookie value input에 없음
[ ] raw cookie value log에 없음
[ ] raw cookie value exception에 없음

[ ] headers output Set-Cookie 계속 MASKED

[ ] output["cookies"] 추가
[ ] CookieInfo JSON-safe metadata만 저장

[ ] Set-Cookie 없음 → cookies=[]
[ ] malformed cookie → HTTP request 실패시키지 않음

[ ] redirect cookie replay 없음
[ ] intermediate redirect cookie 저장 없음
[ ] final response cookie metadata만 저장

[ ] 기존 http_request 기능 회귀 없음
[ ] Unit Test PASS
[ ] Full Regression PASS
[ ] Import PASS
[ ] Result Document 생성
```

---

## 48. 완료 조건

다음 조건을 모두 만족하면 D08-T06A 완료다.

```text
http_request와 cookie_inspector 실제 연결

Raw Set-Cookie는 transient memory only

ToolExecution에는 CookieInfo metadata만 저장

Set-Cookie Header는 계속 MASKED

복수 Set-Cookie 처리

Cookie Value 미저장

Redirect Cookie 재전송 없음

Intermediate Redirect Cookie 미보존

Final Response Cookie Metadata 저장

Unit Test PASS

Full Regression PASS

범위 확대 없음
```

---

## 49. 권장 Commit Message

```text
fix: bridge cookie metadata into http output
```

사용 금지:

```text
git commit --amend
git push --force
```

---

## 50. 완료 보고 형식

```text
D08-T06A COOKIE METADATA PIPELINE BRIDGE

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- transient raw Set-Cookie path
- cookie_inspector integration
- CookieInfo metadata output
- final-response-only cookie policy
- masked Set-Cookie storage

Security Validation:
- Raw Cookie Output Retention: PASS / FAIL
- Raw Cookie Input Retention: PASS / FAIL
- Raw Cookie Log Retention: PASS / FAIL
- Raw Cookie Error Retention: PASS / FAIL
- Set-Cookie Header Masking: PASS / FAIL
- Multiple Set-Cookie: PASS / FAIL
- Expires Comma: PASS / FAIL
- Cookie Replay Absent: PASS / FAIL
- Intermediate Redirect Cookie Not Stored: PASS / FAIL
- Final Cookie Metadata: PASS / FAIL

Validation:
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T06A_COOKIE_PIPELINE_BRIDGE_RESULT_v0.1.md

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

## 51. 작업 종료 원칙

D08-T06A 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T07 — WebTargetContext 생성
```

이 Bridge가 완료되면 Day 8의 Passive Tool 결과를
하나의 WebTargetContext로 조립할 준비가 완료된다.
