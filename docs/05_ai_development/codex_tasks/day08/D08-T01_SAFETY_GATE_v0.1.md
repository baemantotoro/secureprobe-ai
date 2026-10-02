# D08-T01 — Safety Gate Basic Implementation v0.1

## 1. 목적

SecureProbe AI의 Web Active Assessment가
허가된 로컬/Allowlist 대상에서만 실행되도록 하는
기본 Safety Gate를 구현한다.

이번 Task의 핵심 목적은 다음이다.

```text
Assessment Request
        ↓
Safety Gate
        ↓
ALLOW / DENY
```

Active Assessment는 기본적으로 다음 대상만 허용한다.

```text
localhost
127.0.0.1
::1
명시적 Allowlist Host
```

그 외 임의 외부 Target은 기본 차단한다.

이번 Task는 실제 HTTP 요청을 보내지 않는다.
URL과 Scope/Authorization 정보를 검증하여
`ValidationResult`를 생성하는 정책 계층만 구현한다.

---

## 2. 프로젝트 진행 변경사항

SecureBoard 구현은 현재 Claude가 병렬로 진행한다.

따라서 기존 WBS의:

```text
Day 3 ~ Day 7
SecureBoard / Ground Truth 준비
```

는 별도 병렬 트랙으로 간주한다.

SecureProbe Codex 트랙은
SecureBoard 완료를 기다리지 않고 독립 구현 가능한:

```text
D08-T01 — Safety Gate 기본 구현
```

부터 진행한다.

단, 실제 SecureBoard 대상 Integration Test는
SecureBoard가 전달된 후 수행한다.

이번 Task에서는 Unit Test만 수행한다.

---

## 3. 작업 ID와 근거

- WBS 기준: Day 8, Task 01
- 작업 ID: `D08-T01`
- 작업명: Safety Gate 기본 구현
- 우선순위: P0
- 선행 작업:
  - Day 1 완료
  - Day 2 완료
- 병렬 의존성:
  - SecureBoard는 Claude에서 별도 진행
- 다음 작업:
  - `D08-T02 — http_request`

기준 문서:

```text
docs/00_context/PROJECT_CONTEXT_v0.1.md
docs/01_architecture/ARCHITECTURE_v0.1.md
docs/01_architecture/AGENT_FLOW_v0.1.md
docs/02_spec/DATA_SCHEMA_v0.1.md
docs/03_wbs/WBS_20DAYS_v0.1.md
```

---

## 4. 핵심 보안 원칙

반드시 다음 원칙을 유지한다.

```text
Test Account 입력은 허가 증명이 아니다.

authorization_confirmed=True 역시
그 자체만으로 외부 Target Active Assessment 허가 근거가 아니다.

Active Assessment는:
localhost / 127.0.0.1 / ::1 / 명시적 Allowlist
대상에서만 허용한다.

그 외 외부 Target은 기본 차단한다.
```

---

## 5. 구현 위치

생성 권장:

```text
secureprobe/core/safety.py
```

필요한 경우 수정:

```text
secureprobe/core/__init__.py
```

Unit Test:

```text
tests/unit/test_safety_gate.py
```

결과 문서:

```text
docs/05_ai_development/codex_results/day08/
D08-T01_SAFETY_GATE_RESULT_v0.1.md
```

---

# 6. 기존 Model 재사용

다음 기존 Model을 재사용한다.

```text
AssessmentRequest
AssessmentScope
ValidationResult
AssessmentType
```

필요한 경우:

```text
RiskLevel
```

을 입력 파라미터 또는 정책 판단에 사용할 수 있다.

새로운 AssessmentRequest/ValidationResult Model을 만들지 않는다.

---

# 7. 권장 Public API

최소 하나의 명확한 Public Function 또는 Class를 제공한다.

권장안:

```python
def validate_web_target(
    request: AssessmentRequest,
    *,
    active: bool,
    allowlist: set[str] | None = None,
) -> ValidationResult:
    ...
```

또는:

```python
class SafetyGate:
    def validate(
        self,
        request: AssessmentRequest,
        *,
        active: bool,
    ) -> ValidationResult:
        ...
```

둘 중 하나를 선택한다.

20일 PoC에서는 단순 Function 방식도 충분하다.

---

# 8. 입력 조건

Web Safety Gate 입력은 최소 다음이다.

```text
AssessmentRequest
Active / Passive 여부
Explicit Allowlist
```

이번 Task에서 Source Assessment Safety Gate는 구현하지 않는다.

SOURCE Request가 들어온 경우:

```text
Unsupported 또는 명확한 Validation 실패
```

로 처리한다.

Web 전용 Safety Gate임을 명확히 한다.

---

# 9. ValidationResult 출력

기존 `ValidationResult`를 사용한다.

필드:

```text
allowed
reason
active_assessment_allowed
validated_scope
```

예:

```python
ValidationResult(
    allowed=True,
    reason="localhost target",
    active_assessment_allowed=True,
    validated_scope=request.scope,
)
```

차단 예:

```python
ValidationResult(
    allowed=False,
    reason="external target not in allowlist",
    active_assessment_allowed=False,
    validated_scope=None,
)
```

---

# 10. URL Scheme 정책

허용 Scheme:

```text
http
https
```

그 외 차단:

```text
ftp
file
gopher
ws
wss
data
javascript
```

이번 Task에서는:

```text
http://
https://
```

만 허용한다.

---

# 11. URL Parsing

Python 표준 라이브러리 사용을 우선한다.

권장:

```python
urllib.parse.urlsplit
```

또는:

```python
urllib.parse.urlparse
```

외부 URL parser dependency를 추가하지 않는다.

---

# 12. URL 필수 조건

다음 조건을 확인한다.

```text
scheme 존재
hostname 존재
scheme이 http 또는 https
```

다음은 차단한다.

```text
빈 URL
relative URL
hostname 없는 URL
malformed URL
```

예:

```text
/app
localhost:8080
http:///admin
://localhost
```

---

# 13. Host Canonicalization

Host 비교 전 최소 다음을 정규화한다.

```text
lowercase
trailing dot 제거
```

예:

```text
LOCALHOST
→ localhost

localhost.
→ localhost

Example.COM
→ example.com
```

Port는 Host Allowlist 비교에서 제외한다.

예:

```text
localhost:5000
localhost:8080
```

둘 다 host는:

```text
localhost
```

로 평가한다.

---

# 14. 기본 허용 Host

기본 Active Allow:

```text
localhost
127.0.0.1
::1
```

정확히 이 세 값을 기본 허용한다.

주의:

```text
127.0.0.0/8 전체를 자동 허용하지 않는다.
```

이번 v0.1 기본 허용은:

```text
127.0.0.1
```

한정이다.

---

# 15. Localhost Spoofing 차단

다음은 localhost로 인식하면 안 된다.

```text
localhost.evil.com
evil-localhost.com
localhost-example.com
127.0.0.1.evil.com
```

문자열 포함 검사 금지.

잘못된 예:

```python
if "localhost" in hostname:
```

반드시 canonical host의 정확한 값으로 판단한다.

---

# 16. Explicit Allowlist

호출자가 다음 Allowlist를 전달할 수 있다.

예:

```python
{
    "secureboard.local",
    "lab.example.internal",
}
```

이번 v0.1에서는:

```text
Exact Host Match
```

만 지원한다.

지원하지 않음:

```text
Wildcard
*.example.com
CIDR
Regex
Substring
URL Path 기준 Allowlist
```

---

# 17. Allowlist Canonicalization

Allowlist Host도 Target Host와 동일하게 정규화한다.

```text
lowercase
trailing dot 제거
```

예:

```text
SECUREBOARD.LOCAL.
→ secureboard.local
```

---

# 18. Allowlist 입력 형식

Allowlist는 Hostname/IP literal만 받는다.

예:

정상:

```text
secureboard.local
192.0.2.10
```

이번 Task에서 URL 형태:

```text
https://secureboard.local
```

를 Allowlist 항목으로 지원할 필요는 없다.

단순 Host 목록으로 유지한다.

---

# 19. Userinfo 정책

다음과 같은 URL은 차단한다.

```text
http://user:pass@localhost/
http://localhost@evil.com/
```

이유:

```text
Host confusion 방지
Credential URL 유입 방지
```

`username` 또는 `password`가 URL parser 결과에 존재하면
Safety Gate에서 차단한다.

Test Account는 별도 `Credentials` Model로만 관리한다.

---

# 20. Fragment 정책

URL fragment는 HTTP 요청 대상 Host 판단에는 사용하지 않는다.

예:

```text
http://localhost/#admin
```

Host는:

```text
localhost
```

로 검증할 수 있다.

단, fragment를 Allowlist 판단에 사용하지 않는다.

---

# 21. Query 정책

Query String도 Host 허가 판단에 사용하지 않는다.

예:

```text
http://localhost/search?q=test
```

Host:

```text
localhost
```

로 검증한다.

---

# 22. Active Assessment 정책

`active=True`인 경우 다음 조건을 모두 만족해야 한다.

```text
assessment_type == WEB
target_url valid
scheme == http/https
userinfo 없음

authorization_confirmed == True

AND

host가 다음 중 하나:
- localhost
- 127.0.0.1
- ::1
- explicit allowlist exact match
```

---

# 23. authorization_confirmed 정책

중요:

```text
authorization_confirmed=True
```

는 Active Assessment의 필요조건 중 하나일 수 있지만,
외부 Target 허용의 충분조건이 아니다.

예:

```text
target = https://example.com
authorization_confirmed = True
allowlist = empty
```

결과:

```text
DENY
```

---

# 24. Test Account 정책

`request.credentials` 값의 존재 여부는
Safety Gate 허용 판단 근거로 사용하지 않는다.

예:

```text
credentials 존재
authorization_confirmed=True
external target
allowlist 없음
```

결과:

```text
DENY
```

---

# 25. Passive Assessment 정책

`active=False`의 경우에도 URL 형식과 scheme 검증은 수행한다.

그러나 Passive Assessment의 외부 Target 허용 여부는
이번 Task에서 광범위하게 확장하지 않는다.

v0.1 권장 정책:

```text
Passive:
- valid http/https URL이면 Validation 자체는 허용 가능
- active_assessment_allowed는 host 정책에 따라 별도로 계산
```

예:

```text
https://example.com
active=False
```

가능한 결과:

```text
allowed=True
active_assessment_allowed=False
```

즉:

```text
Passive Validation 가능
Active Tool 실행은 불가
```

이 구조를 권장한다.

---

# 26. ValidationResult 의미

`allowed`:

```text
현재 요청 자체가 Safety Validation을 통과했는가
```

`active_assessment_allowed`:

```text
Active Tool까지 실행할 수 있는가
```

두 값을 혼동하지 않는다.

---

# 27. localhost Active 예

입력:

```text
target_url=http://localhost:8080
authorization_confirmed=True
active=True
```

결과:

```text
allowed=True
active_assessment_allowed=True
```

---

# 28. External Passive 예

입력:

```text
target_url=https://example.com
authorization_confirmed=False
active=False
allowlist={}
```

권장 결과:

```text
allowed=True
active_assessment_allowed=False
```

---

# 29. External Active 차단 예

입력:

```text
target_url=https://example.com
authorization_confirmed=True
active=True
allowlist={}
```

결과:

```text
allowed=False
active_assessment_allowed=False
```

---

# 30. Explicit Allowlist Active 예

입력:

```text
target_url=https://secureboard.local
authorization_confirmed=True
active=True
allowlist={"secureboard.local"}
```

결과:

```text
allowed=True
active_assessment_allowed=True
```

---

# 31. Authorization False 예

입력:

```text
target_url=http://localhost
authorization_confirmed=False
active=True
```

결과:

```text
allowed=False
active_assessment_allowed=False
```

Active Assessment에서는 authorization confirmation을 요구한다.

---

# 32. DNS Resolution 제외

이번 Task에서는 DNS Resolution을 구현하지 않는다.

즉 다음은 하지 않는다.

```text
socket.getaddrinfo
DNS lookup
CNAME resolution
DNS rebinding detection
Resolved IP allowlist comparison
```

이유:

```text
현재 Task는 기본 Safety Gate 정책 구현
20일 PoC 범위 보호
네트워크 I/O 없는 deterministic Unit Test 유지
```

필요하면 추후 별도 보강한다.

---

# 33. Network Request 금지

Safety Gate는 네트워크 요청을 보내지 않는다.

금지:

```text
httpx.get
requests.get
socket connect
ping
DNS lookup
```

입력값만 검증한다.

---

# 34. Scope 처리

Validation 성공 시:

```text
validated_scope=request.scope
```

를 기본으로 사용할 수 있다.

차단 시:

```text
validated_scope=None
```

권장.

이번 Task에서 path scope 세부 검증은 하지 않는다.

예:

```text
allowed_paths
deny_paths
```

는 그대로 보존한다.

Path Scope enforcement는 실제 Tool 실행 단계에서 추가 검토한다.

---

# 35. Reason 메시지

Reason은 사람이 확인하기 쉬운 간결한 값으로 작성한다.

예:

```text
localhost target
loopback target
explicit allowlist target
authorization not confirmed
external target not in allowlist
unsupported URL scheme
target URL missing hostname
URL userinfo is not allowed
unsupported assessment type
```

긴 설명이나 Chain-of-Thought를 저장하지 않는다.

---

# 36. Unit Test 파일

생성:

```text
tests/unit/test_safety_gate.py
```

---

# 37. 기본 허용 Test

다음 Active Target을 각각 검증한다.

```text
http://localhost
http://localhost:8080
https://LOCALHOST
http://localhost.

http://127.0.0.1
http://127.0.0.1:5000

http://[::1]
http://[::1]:8080
```

전제:

```text
authorization_confirmed=True
active=True
```

결과:

```text
allowed=True
active_assessment_allowed=True
```

---

# 38. External Active 차단 Test

다음은 차단:

```text
https://example.com
https://www.google.com
```

allowlist 없음.

결과:

```text
allowed=False
active_assessment_allowed=False
```

Test에서는 실제 네트워크 접속하지 않는다.

---

# 39. Localhost Spoofing Test

반드시 차단:

```text
http://localhost.evil.com
http://evil-localhost.com
http://localhost-example.com
http://127.0.0.1.evil.com
```

---

# 40. Explicit Allowlist Test

예:

```text
allowlist={"secureboard.local"}
target=https://secureboard.local
```

authorization confirmed + active:

```text
ALLOW
```

다음은 차단:

```text
secureboard.local.evil.com
evilsecureboard.local
```

---

# 41. Allowlist Case/Trailing Dot Test

Allowlist:

```text
SECUREBOARD.LOCAL.
```

Target:

```text
https://secureboard.local
```

또는 반대.

Canonicalization 후 정확히 일치하면 허용한다.

---

# 42. Authorization False Test

다음:

```text
localhost
authorization_confirmed=False
active=True
```

차단.

```text
allowed=False
active_assessment_allowed=False
```

---

# 43. Credentials Not Authorization Test

Request:

```text
credentials 존재
external target
authorization_confirmed=True
allowlist 없음
active=True
```

결과:

```text
DENY
```

---

# 44. Passive External Test

```text
https://example.com
active=False
```

권장:

```text
allowed=True
active_assessment_allowed=False
```

authorization_confirmed 값과 무관하게
Active Tool은 허용하지 않는다.

---

# 45. Scheme Validation Test

허용:

```text
http
https
```

차단:

```text
ftp://localhost
file:///etc/passwd
gopher://localhost
data:text/plain,test
```

---

# 46. Userinfo 차단 Test

차단:

```text
http://user:pass@localhost
http://localhost@evil.com
```

---

# 47. Malformed URL Test

최소:

```text
""
"/admin"
"http:///admin"
"://localhost"
```

Validation 결과:

```text
allowed=False
active_assessment_allowed=False
```

예외를 외부로 던지지 않고
가능하면 `ValidationResult`로 정리한다.

---

# 48. SOURCE Assessment Test

`AssessmentType.SOURCE` Request를
Web Safety Gate에 전달하면:

```text
allowed=False
active_assessment_allowed=False
reason="unsupported assessment type"
```

등 명확히 처리한다.

---

# 49. Scope Preservation Test

허용된 Request에서:

```text
request.scope
```

와:

```text
result.validated_scope
```

가 동일 의미의 값을 유지하는지 검증한다.

---

# 50. No Network I/O Test

Safety Gate Test는 mock network를 만들 필요가 없어야 한다.

코드에서:

```text
httpx
requests
socket
```

를 import하지 않는 것이 권장된다.

---

# 51. Public Import

필요하면 다음 import를 지원한다.

```python
from secureprobe.core.safety import validate_web_target
```

또는 선택한 Public Class.

`secureprobe/core/__init__.py` export는 필수가 아니다.

---

# 52. 전체 Regression Test

개별:

```bash
pytest tests/unit/test_safety_gate.py -q
```

전체:

```bash
pytest -q
```

기존 Day 1/2 Test 포함 전체 PASS해야 한다.

현재 기존 Full Regression 기준:

```text
99 passed
```

이지만 새 Safety Test 추가 후 실제 test 수를 새로 기록한다.

이전 숫자를 복사하지 않는다.

---

# 53. Import Test

예:

```bash
python -c "from secureprobe.core.safety import validate_web_target; print('IMPORT_OK')"
```

실제 Public API 이름에 맞게 실행한다.

결과:

```text
IMPORT_OK
```

---

# 54. 수정 가능 파일

생성:

```text
secureprobe/core/safety.py
tests/unit/test_safety_gate.py

docs/05_ai_development/codex_results/day08/
D08-T01_SAFETY_GATE_RESULT_v0.1.md
```

필요 시 최소 수정:

```text
secureprobe/core/__init__.py
```

---

# 55. 수정 금지 파일

다음은 수정하지 않는다.

```text
secureprobe/models/*
secureprobe/web/*
secureprobe/source/*
secureprobe/agent/*
secureprobe/report/*

secureboard/*

PROJECT_CONTEXT_v0.1.md
ARCHITECTURE_v0.1.md
AGENT_FLOW_v0.1.md
DATA_SCHEMA_v0.1.md
WBS_20DAYS_v0.1.md
```

---

# 56. 범위 확장 금지

이번 Task에서 구현하지 않는다.

```text
HTTP 요청
Web Observer
http_request Tool
endpoint_collector
form_parser
header_inspector
cookie_inspector
Authentication Login
Session Handling
DNS Resolution
DNS Rebinding Defense
CIDR Allowlist
Wildcard Allowlist
Browser Automation
Ground Truth
ZAP
Semgrep
```

---

# 57. 결과 문서

반드시 생성:

```text
docs/05_ai_development/codex_results/day08/
D08-T01_SAFETY_GATE_RESULT_v0.1.md
```

---

# 58. 결과 문서 필수 항목

```text
Task ID
Status
Implemented Policy
Created Files
Modified Files
Allowed Active Targets
Denied Active Targets
Passive Policy
Authorization Policy
Credentials Policy
URL Validation Policy
Allowlist Policy
Network I/O
Unit Test Result
Full Regression Result
Import Validation
Scope Check
Issues
Next Task
```

---

# 59. 결과 문서 예시

```text
# D08-T01 — Safety Gate Result v0.1

## Status

COMPLETED

## Active Policy

Allowed:
- localhost
- 127.0.0.1
- ::1
- explicit exact-match allowlist

Required:
- authorization_confirmed=True

Denied:
- arbitrary external target
- malformed URL
- unsupported scheme
- userinfo URL
- localhost spoofing

## Passive Policy

Valid external http/https URL may pass request validation,
but active_assessment_allowed remains False unless host policy passes.

## Credentials Policy

Credentials are not treated as authorization proof.

## Network I/O

None

## Validation

Unit Test:
PASS

Full pytest:
PASS

Import:
PASS

## Issues

None

## Next Task

D08-T02 — http_request
```

---

# 60. 완료 체크리스트

```text
[ ] safety.py 생성
[ ] Web 전용 Safety Gate 구현

[ ] http/https scheme 허용
[ ] malformed URL 차단
[ ] userinfo 차단

[ ] localhost 허용
[ ] 127.0.0.1 허용
[ ] ::1 허용
[ ] explicit allowlist exact match 허용

[ ] localhost spoofing 차단
[ ] external active 기본 차단

[ ] authorization_confirmed=False active 차단
[ ] credentials를 authorization으로 사용하지 않음

[ ] passive / active 결과 분리
[ ] active_assessment_allowed 별도 계산

[ ] network I/O 없음
[ ] DNS resolution 없음

[ ] test_safety_gate.py 생성
[ ] Unit Test PASS
[ ] Full pytest PASS
[ ] Import PASS

[ ] 결과 문서 생성
[ ] 범위 확대 없음
```

---

# 61. 완료 조건

다음 조건을 모두 만족하면 D08-T01 완료다.

```text
기본 Safety Gate 구현
Active localhost/loopback 허용
Explicit Allowlist exact match 허용
External Active 기본 차단
Authorization Confirmation 정책 적용
Credentials 비허가증명 원칙 적용
Localhost spoofing 방지
URL parsing / scheme validation
Passive와 Active 권한 분리
Network I/O 없음
Unit Test PASS
전체 Regression PASS
결과 문서 작성
```

---

# 62. Git 검증

작업 전:

```bash
git status
```

작업 후:

```bash
git status
git diff --stat
git diff
```

변경 범위가 이번 Task와 일치하는지 확인한다.

---

# 63. 권장 Commit Message

```text
feat: add web assessment safety gate
```

다음 사용 금지:

```text
git commit --amend
git push --force
```

---

# 64. 완료 보고 형식

```text
D08-T01 SAFETY GATE

Status:
COMPLETED / BLOCKED / FAILED

Implemented:
- URL validation
- localhost/loopback policy
- explicit allowlist
- authorization confirmation policy
- passive/active separation
- localhost spoofing protection

Validation:
- Localhost Active: PASS / FAIL
- 127.0.0.1 Active: PASS / FAIL
- ::1 Active: PASS / FAIL
- Explicit Allowlist: PASS / FAIL
- External Active Deny: PASS / FAIL
- Spoofing Deny: PASS / FAIL
- Authorization False Deny: PASS / FAIL
- Credentials Not Authorization: PASS / FAIL
- Unsupported Scheme: PASS / FAIL
- Userinfo Deny: PASS / FAIL
- Malformed URL: PASS / FAIL
- Passive External Policy: PASS / FAIL
- Network I/O Absent: PASS / FAIL
- Unit Test: PASS / FAIL
- Full pytest: PASS / FAIL
- Import: PASS / FAIL
- Scope Check: PASS / FAIL

Result Document:
docs/05_ai_development/codex_results/day08/
D08-T01_SAFETY_GATE_RESULT_v0.1.md

Commit:
<commit SHA>

Push:
SUCCESS / FAILED

Issues:
-

Next Task:
D08-T02 — http_request
```

---

# 65. 작업 종료 원칙

D08-T01 완료 후 다음 Task를 자동 시작하지 않는다.

다음 작업:

```text
D08-T02 — http_request
```

SecureBoard가 Claude에서 완료되면
별도의 Integration 단계에서 실제 Lab URL을 연결한다.
