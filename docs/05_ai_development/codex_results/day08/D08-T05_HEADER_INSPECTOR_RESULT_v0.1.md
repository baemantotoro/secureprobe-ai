# D08-T05 — Header Inspector Result v0.1

## 1. Task ID / Status

Task ID: D08-T05

Status: COMPLETED

## 2. Public API

```python
def inspect_headers(*, url: str, headers: Mapping[str, str]) -> HeaderInspectionResult:
    ...
```

이미 확보한 Response Header의 metadata만 관찰한다.
URL은 기존 public Safety Gate의 Passive Validation으로 확인하며, 잘못된 URL은 ValueError다.
dict 및 Mapping[str, str]를 허용하고 잘못된 입력 형태나 비문자열 key/value는 ValueError다.

## 3. Created Files / Modified Files

Created Files:

- `secureprobe/web/tools/header_inspector.py`
- `tests/unit/test_header_inspector.py`
- `docs/05_ai_development/codex_results/day08/D08-T05_HEADER_INSPECTOR_RESULT_v0.1.md`

Modified Files:

- `secureprobe/models/target.py`: HeaderObservation / HeaderInspectionResult 추가.
- `secureprobe/models/__init__.py`: 두 모델의 export 추가.

기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T05_HEADER_INSPECTOR_v0.1.md`도 내용 변경 없이 Git에 등록한다.
Safety Gate, 기존 HTTP/HTML Tool, 기존 모델 정의, SecureBoard, 기준 문서와 의존성은 변경하지 않았다.

## 4. Observed Headers / Models

Observation 순서는 다음 8개로 고정한다.

1. Content-Security-Policy
2. X-Content-Type-Options
3. X-Frame-Options
4. Referrer-Policy
5. Permissions-Policy
6. Strict-Transport-Security
7. Cache-Control
8. Pragma

HeaderObservation은 name / present / value / note만 반환한다.
name은 빈 값과 공백 문자열을 거부하고 present는 strict bool이다.
HeaderInspectionResult는 url / scheme(http 또는 https) / observations만 반환한다.
두 모델은 extra forbid를 적용하고 Observation 목록 기본값은 instance별로 독립적이다.

## 5. Header Key Normalization / Sensitive Header Policy

비교는 lowercase로 처리하고 출력 name은 위 canonical 형태를 사용한다.
같은 이름의 대소문자 변형이 여러 mapping entry에 있으면 최초 값을 사용한다.
입력 Mapping을 변경하지 않는다.

Authorization / Proxy-Authorization / Set-Cookie / WWW-Authenticate /
X-Api-Key / API-Key / Cookie 및 분석 대상 외 Header는 Observation에서 제외한다.
Server / Date / Content-Length / ETag / X-Powered-By도 무시한다.
Raw Header 전체 dict를 결과에 복사하지 않는다.
민감 Header 테스트 원문이 결과 JSON에 없음을 검증했다.

## 6. HSTS Scheme Policy / Value Length Policy

HTTPS에서는 HSTS의 존재와 값만 관찰한다.
HTTP에서는 `HSTS is only effective over HTTPS` 문맥 설명을 추가한다.
HSTS 존재/누락을 취약점 또는 Finding으로 확정하지 않는다.

Value는 leading/trailing whitespace를 제거한 뒤 최대 4096 characters까지만 저장한다.
초과 시 note에 `value truncated`를 기록한다.
CR/LF, Unicode control/format/surrogate 등 category C 문자가 있는 값은
전체 value를 None으로 생략하고 note에 `value omitted: control characters`를 기록한다.
이 경우 Header의 present=True는 유지한다.
빈 문자열 값은 present=True / value=""이며 누락은 present=False / value=None이다.
빈 입력 Mapping은 분석 대상 8개 모두 누락으로 반환한다.

## 7. Network I/O / Cookie Analysis / Vulnerability Judgment

Network I/O: None

header_inspector는 Response Header metadata만 관찰한다. HTTP 요청이나 DNS lookup을 수행하지 않는다.
Set-Cookie 분석과 Cookie Attribute 판단은 D08-T06 cookie_inspector 책임이다.
Header 누락을 취약점으로 확정하지 않는다.
Severity / OWASP / CWE / CandidateFinding / Finding 생성은 Analyzer 단계 책임이다.
Directive 강도 평가, Ground Truth 비교, ZAP/Semgrep 비교 및 Report 생성을 하지 않는다.
새 dependency를 추가하지 않았다.

## 8. Unit Test Result / Full Regression Result

실행일: 2026-10-05 (Asia/Seoul)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_header_inspector.py -q
```

```text
64 passed in 0.39s
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
496 passed in 2.61s
```

기존 432개와 새 Header Inspector 테스트 64개가 모두 통과했다.
Unit Test는 확보된 Header Mapping만 사용하며 네트워크 fixture를 사용하지 않는다.

## 9. Import Validation / Validation

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.web.tools.header_inspector import inspect_headers; from secureprobe.models import HeaderObservation, HeaderInspectionResult; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

- CSP: PASS
- X-Content-Type-Options: PASS
- X-Frame-Options: PASS
- Referrer-Policy: PASS
- Permissions-Policy: PASS
- HSTS HTTPS: PASS
- HSTS HTTP Context: PASS
- Cache-Control: PASS
- Pragma: PASS
- Case Insensitive: PASS
- Sensitive Header Protection: PASS
- Set-Cookie Not Inspected: PASS
- Unknown Headers Ignored: PASS
- Header Value Limit: PASS
- Control Character Handling: PASS
- Deterministic Order: PASS
- Model Validation / JSON Round-trip / Mutable Default Isolation: PASS
- Network I/O Absent: PASS (코드 검토)
- Unit Test: PASS
- Full pytest: PASS
- Import: PASS
- Scope Check: PASS

## 10. Issues

None

SecureBoard 전달 후 실제 Response Header를 이용한 Integration Test는 별도로 수행한다.

## 11. Next Task

D08-T06 — cookie_inspector

다음 Task는 자동 시작하지 않는다.
