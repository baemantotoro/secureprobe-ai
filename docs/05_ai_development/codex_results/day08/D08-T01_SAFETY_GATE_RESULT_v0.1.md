# D08-T01 — Safety Gate Result v0.1

## 1. Task ID / Status

Task ID: D08-T01

Status: COMPLETED

## 2. Implemented Policy

Web 전용 `validate_web_target(request, *, active, allowlist=None)`을 구현했다.
기존 `AssessmentRequest`, `AssessmentType`, `ValidationResult`를 재사용하며,
입력 URL과 호출자가 전달한 Host Allowlist 및 Authorization Confirmation으로 판단한다.
SOURCE 요청은 `unsupported assessment type`으로 차단한다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/core/safety.py`
- `tests/unit/test_safety_gate.py`
- `docs/05_ai_development/codex_results/day08/D08-T01_SAFETY_GATE_RESULT_v0.1.md`

Modified Files: None

## 4. Allowed Active Targets / Denied Active Targets

Allowed Active Targets:

- `localhost`
- `127.0.0.1`
- `::1`
- 호출자가 전달한 명시적 Allowlist의 정확한 Host 일치

모든 Active 허용은 `authorization_confirmed=True`를 추가로 요구한다.
대소문자와 마지막 점 하나를 정규화하고 Port는 Host 비교에서 제외한다.
IPv6 표기를 다른 형태로 변환하지 않으며 기본 허용은 정확한 `::1`에 한정한다.

Denied Active Targets:

- Allowlist에 없는 임의 외부 Host
- `127.0.0.1` 외의 `127.0.0.0/8` 주소와 다른 loopback 표기
- `localhost.evil.com`, `evil-localhost.com`, `localhost-example.com`, `127.0.0.1.evil.com`
- Authorization 미확인 요청
- Malformed URL, 미지원 Scheme, Userinfo URL

## 5. Passive Policy

Passive 요청은 유효한 HTTP(S) URL이면 외부 Host도 `allowed=True`로 처리한다.
`active_assessment_allowed`는 요청 모드와 별도로 Host 허가 및 Authorization Confirmation을 모두 충족할 때만 True다.
따라서 Allowlist에 없는 외부 Host는 Authorization 값과 관계없이 Active 권한이 False다.
허용된 로컬 또는 Allowlist Host도 Authorization 미확인 시 Active 권한이 False다.

## 6. Authorization Policy / Credentials Policy

Authorization Confirmation은 Active 허용의 필요조건이며 외부 Host 허가를 대신하지 않는다.
Credentials 존재 여부는 허가 판단에 사용하지 않는다.
`request.scope.allowed_hosts`도 명시적 호출자 Allowlist를 대신하지 않는다.

## 7. URL Validation Policy / Allowlist Policy

- Python 표준 라이브러리 `urllib.parse.urlsplit`으로 URL을 파싱한다.
- `http` / `https`만 허용하고 Host가 있는 절대 URL을 요구한다.
- Userinfo, 잘못된 IPv6 괄호·authority, 비숫자·범위 초과·빈 Port를 차단한다. 명시적 Port는 1~65535다.
- 공백, 제어문자, 역슬래시, 잘못된 Host 라벨, percent-encoded Host 및 scoped IPv6를 차단한다.
- Host는 ASCII Hostname 또는 IP literal을 사용하며 lowercase 및 마지막 점 하나 제거로 정규화한다.
- Query와 Fragment는 Host 허가에 영향을 주지 않는다.
- Allowlist도 같은 Host 정규화를 적용한다. Hostname/IP literal의 정확한 일치만 지원한다.
- URL, Port 포함 Host, Wildcard, CIDR, Regex, Path, 잘못된 Host 형식의 Allowlist 항목은 무시하여 허가를 부여하지 않는다.
- 차단 시 `allowed=False`, `active_assessment_allowed=False`, `validated_scope=None`을 반환한다.
- 성공 시 `request.scope`의 의미와 값을 보존한다. Path Scope 세부 enforcement는 후속 Tool 실행 단계의 범위다.

## 8. Network I/O

None

HTTP 요청, DNS lookup 및 네트워크 클라이언트 호출이 없다.
표준 라이브러리의 로컬 URL 파싱·Host 구문 검사만 사용하며 테스트에 네트워크 fixture가 필요하지 않다.
DNS Resolution / DNS Rebinding Defense는 이번 Task 범위에 포함되지 않는다.

## 9. Unit Test Result / Full Regression Result

실행일: 2026-10-03 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_safety_gate.py -q
```

```text
113 passed in 0.27s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
212 passed in 0.99s
```

기존 Day 1/2 테스트 99개와 새 Safety Gate 테스트 113개가 모두 통과했다.
빈 URL은 기존 Pydantic 입력 검증의 거부와 검증을 우회한 요청에 대한 Gate의 방어적 거부를 각각 확인했다.

## 10. Import Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.core.safety import validate_web_target; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

Import Validation: PASS

## 11. Validation / Scope Check

- Localhost Active: PASS
- 127.0.0.1 Active: PASS
- ::1 Active: PASS
- Explicit Allowlist: PASS
- External Active Deny: PASS
- Spoofing Deny: PASS
- Authorization False Deny: PASS
- Credentials Not Authorization: PASS
- Unsupported Scheme: PASS
- Userinfo Deny: PASS
- Malformed URL: PASS
- Passive External Policy: PASS
- Scope Preservation: PASS
- Network I/O Absent: PASS (코드 검토)
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

Task 지침과 PROJECT_CONTEXT / ARCHITECTURE / AGENT_FLOW / DATA_SCHEMA / WBS의 관련 기준을 대조했다.
변경 범위는 위 생성 파일 3개다. 기존 Model, SecureBoard, Agent, Web/Source Tool,
Report, 기준 문서 및 의존성을 변경하지 않았다. Integration Test는 수행하지 않았다.

## 12. Issues

None

## 13. Next Task

D08-T02 — http_request

다음 Task는 자동 시작하지 않는다. SecureBoard 전달 후 별도 Integration 단계에서 Lab URL을 연결한다.
