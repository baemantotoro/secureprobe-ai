# D08-T02 — HTTP Request Result v0.1

## 1. Task ID / Status

Task ID: D08-T02

Status: COMPLETED

## 2. Public API

```python
async def http_request(
    *,
    assessment_request: AssessmentRequest,
    url: str,
    test_id: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    follow_redirects: bool = False,
    timeout_seconds: float = 5.0,
    max_body_bytes: int = 65536,
    allowlist: set[str] | None = None,
) -> ToolExecution:
    ...
```

PASSIVE HTTP Evidence 수집용 async Tool이다. 기존 `ToolExecution`, `ToolError`,
`ExecutionStatus`, `AssessmentRequest`를 재사용하며 별도 중복 모델을 추가하지 않았다.
`test_id`는 호출자가 전달하는 비어 있지 않은 문자열이며, `execution_id`는 UUID로 생성한다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/web/tools/http_request.py`
- `tests/unit/test_http_request.py`
- `docs/05_ai_development/codex_results/day08/D08-T02_HTTP_REQUEST_RESULT_v0.1.md`

Modified Files: None

기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T02_HTTP_REQUEST_v0.1.md`도 내용 변경 없이 Git에 등록한다.
`__init__.py`, 기존 Safety Gate, 모델 및 의존성은 변경하지 않았다.

## 4. Allowed Methods / Safety Gate Integration

- GET / HEAD만 허용한다.
- POST / PUT / PATCH / DELETE / OPTIONS / TRACE / CONNECT 및 그 외 Method는 `BLOCKED / METHOD_NOT_ALLOWED`다.
- 원래 AssessmentRequest와 실제 요청 URL을 기존 `validate_web_target(..., active=False)`로 검증한다.
- Redirect URL도 요청 전에 동일하게 재검증한다.
- Gate 실패는 `BLOCKED / SAFETY_BLOCKED`이며 Transport에 전달하지 않는다.
- 기존 Host canonicalization helper를 재사용한다. URL 보안 정책을 복제하거나 Safety Gate를 수정하지 않았다.

## 5. Scope Host Policy

Assessment Target과 동일 canonical Host는 Passive 요청이 가능하다.
추가 Host는 `scope.allowed_hosts`와 호출자 `allowlist`에 모두 정확히 일치해야 한다.
Scope만으로 Host 허가를 부여하지 않는다. 최초 Scope 위반은 `BLOCKED / OUT_OF_SCOPE`다.
Host 비교는 lowercase 및 마지막 점 하나 제거를 적용하며 Port는 비교에서 제외한다.
Path Scope 세부 enforcement는 이번 Task에 포함하지 않는다.

## 6. Redirect Policy

- 기본 `follow_redirects=False`: 3xx 응답을 반환하고 추가 요청하지 않는다.
- 활성화 시 301 / 302 / 303 / 307 / 308의 Location을 직접 처리한다.
- 최대 Redirect 3회, 단일 호출당 최대 HTTP 요청 4회다.
- 각 Redirect에 Safety Gate 및 Scope Host 검증을 적용한다.
- Scope 이탈은 `BLOCKED / REDIRECT_OUT_OF_SCOPE`이며 해당 Host에 요청하지 않는다.
- 횟수 초과는 `FAILED / TOO_MANY_REDIRECTS`다.
- Query는 요청에 유지되고 Fragment는 HTTP 요청 대상으로 전송되지 않는다.
- Cookie Jar를 각 요청 전에 비워 서버 Cookie를 Redirect에 재전송하지 않는다.
- Userinfo가 있는 Location Header는 결과에서 마스킹한다.
- HTTPX가 비정상 서버 Header를 먼저 거부하는 경우 `FAILED / NETWORK_ERROR`로 구조화하며 추가 요청하지 않는다.

## 7. Timeout Policy / Body Limit

Timeout 기본 5초, 입력 범위 0.1~30초다. HTTPX의 개별 I/O Timeout과
`asyncio.timeout`의 전체 호출 시간 제한을 함께 적용한다.
Timeout은 `TIMEOUT / HTTP_TIMEOUT`, 네트워크 오류는 `FAILED / NETWORK_ERROR`로 반환한다.
두 오류는 `retryable=True`이며 Tool 내부에서 자동 재시도하지 않는다.
오류 메시지에 원시 예외 문자열을 저장하지 않는다.

본문 한도 기본 65536 bytes, 입력 범위 1~1048576 bytes다.
한도 밖 또는 유한하지 않은 Timeout 값은 네트워크 호출 전 `FAILED / INVALID_INPUT`이다.

Text 본문은 스트리밍으로 제한된 byte prefix만 보관한다.
한도를 넘는 데이터가 확인되면 즉시 읽기를 중단하고 `body_truncated=True`로 기록하며 Response를 닫는다.
정확히 한도 크기로 종료된 본문은 truncated로 표시하지 않는다.
Decode 오류는 replacement 처리 또는 UTF-8 fallback으로 처리한다.

HEAD / Binary / Content-Type이 없는 응답은 본문을 읽거나 decode하지 않고 `body_excerpt=None`으로 반환한다.
`Accept-Encoding: identity`를 요청하며, 서버가 압축 Content-Encoding을 보내도
압축을 해제하지 않고 metadata만 반환하여 무제한 압축 해제를 피한다.
본문을 의도적으로 수집하지 않은 경우 `body_truncated=False`이며 수집 중 한도 초과와 구분한다.
`content_length`는 유효한 서버 Header 값이며 전체 본문을 읽어 계산한 크기가 아니다.

Output:

```text
status_code, headers, content_type, body_excerpt, elapsed_ms,
final_url, redirect_chain, body_truncated, content_length
```

## 8. Header Masking / TLS Policy / Proxy Policy

Request Header는 Accept / Accept-Language / User-Agent / Referer /
If-None-Match / If-Modified-Since만 호출자가 설정할 수 있다.
기본 User-Agent는 `SecureProbeAI/0.1`이다.
Authorization / Proxy-Authorization / Cookie / Set-Cookie / X-Api-Key / API-Key 등
미허용 Header는 `BLOCKED / HEADER_NOT_ALLOWED`로 차단한다.
제어문자 또는 잘못된 encoding 값도 실제 요청 전에 차단한다.
차단된 Header의 원시 값과 Userinfo URL은 ToolExecution input에 저장하지 않는다.

Response의 Authorization / Proxy-Authorization / Cookie / Set-Cookie /
WWW-Authenticate / X-Api-Key / API-Key 값은 `***MASKED***`로 반환한다.

HTTPX 설정: `verify=True`, `trust_env=False`, `follow_redirects=False`.
TLS 비활성화 옵션, 환경 Proxy, persistent Cookie Session 및 Logging Framework를 추가하지 않았다.

## 9. Network I/O

Production Tool: HTTPX를 통한 실제 HTTP 요청 수행 가능.

Unit Test: 모든 HTTP 요청은 `httpx.MockTransport`로 처리하며 실제 인터넷 접속 없음.
Safety Gate 자체의 네트워크 I/O 없음 정책은 유지한다.
Shell / Browser / Crawler / 병렬 Scanner / 공격 Payload / 입력 변조를 사용하지 않는다.
Ground Truth / Benchmark 전용 필드를 추가하지 않으며 취약점 판단을 수행하지 않는다.
별도 Evidence 저장 파일은 생성하지 않는다.

## 10. Unit Test Result / Full Regression Result

실행일: 2026-10-03 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_http_request.py -q
```

```text
69 passed in 0.50s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
281 passed in 1.29s
```

기존 212개와 HTTP Tool 테스트 69개 모두 통과했다.
전체 작업 Timeout 검증은 완료되지 않는 Mock Stream을 사용하여 종료 및 Stream Close를 확인한다.

## 11. Import Validation / Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.web.tools.http_request import http_request; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

- GET: PASS
- HEAD: PASS
- Unsupported Method: PASS
- Safety Gate: PASS
- Scope Host: PASS
- Timeout: PASS
- Network Error: PASS
- Body Limit: PASS
- Binary Response: PASS
- Header Masking: PASS
- Redirect Disabled: PASS
- Redirect In-Scope: PASS
- Redirect Out-of-Scope: PASS
- Redirect Limit: PASS
- TLS Verify: PASS
- trust_env=False: PASS
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

## 12. Issues

None

SecureBoard 대상 실제 Lab Integration Test는 전달 후 별도로 수행한다.

## 13. Next Task

D08-T03 — endpoint_collector

다음 Task는 자동 시작하지 않는다.
