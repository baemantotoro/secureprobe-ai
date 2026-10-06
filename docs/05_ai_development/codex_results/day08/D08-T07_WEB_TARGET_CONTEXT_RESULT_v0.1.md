# D08-T07 WEB TARGET CONTEXT RESULT v0.1

## Task ID / Status

- Task ID: D08-T07 — WebTargetContext
- Status: COMPLETED
- 검증일: 2026-10-06
- 기준: D08-T07_WEB_TARGET_CONTEXT_v0.1.md 및 프로젝트 Context / Architecture / Agent Flow / Data Schema / WBS 문서.

## Public API

```python
async def observe_web_target(
    *,
    assessment_request: AssessmentRequest,
    test_id: str = "OBSERVE-WEB-001",
    allowlist: set[str] | None = None,
) -> WebTargetContext:
    ...
```

위치: `secureprobe/web/observer.py`. `WebTargetContext`는 `secureprobe.models`에서 import할 수 있다.

## Created Files

- `secureprobe/web/observer.py`
- `tests/unit/test_web_observer.py`
- 본 결과 문서.
- 기존 미추적 작업지침 `docs/05_ai_development/codex_tasks/day08/D08-T07_WEB_TARGET_CONTEXT_v0.1.md`를 내용 수정 없이 함께 버전 관리한다.

## Modified Files

- `secureprobe/models/target.py`: WebTargetContext 추가.
- `secureprobe/models/__init__.py`: WebTargetContext export 추가.

## WebTargetContext Schema

| 필드 | 타입 / 기본값 |
| --- | --- |
| context_id | 비어 있지 않은 str, CTX-WEB-UUID 형식으로 Observer 생성 |
| base_url | 비어 있지 않은 str |
| endpoints | list[Endpoint], 독립적인 빈 리스트 |
| forms | list[Form], 독립적인 빈 리스트 |
| headers | dict[str, str 또는 None], 독립적인 빈 dict |
| cookies | list[CookieInfo], 독립적인 빈 리스트 |
| authentication_detected | strict bool, False |
| session_detected | strict bool, False |
| content_types | list[str], 독립적인 빈 리스트 |

`extra="forbid"`, `str_strip_whitespace=True` 적용. 각 인스턴스의 가변 기본값은 공유되지 않는다. JSON round-trip 검증 통과.

## Base URL Policy

HTTP Tool의 `final_url`을 사용한다. 최초 요청 URL은 AssessmentRequest에만 남고 Context에 중복 필드를 만들지 않는다. 실제 URL 허용 및 Redirect Scope 판단은 기존 Tool에 위임한다.

## Endpoint Policy / Form Policy

정규화한 Content-Type이 `text/html`일 때만 기존 `collect_endpoints` / `parse_forms`에 final URL, body excerpt, 요청 scope를 전달한다. 반환 모델을 그대로 조립한다. JSON, PDF, 이미지, 바이너리, 일반 텍스트 응답의 endpoints / forms는 빈 리스트다.

빈 HTML 및 정상적인 `body_excerpt=None`은 빈 문자열로 파싱하여 current Endpoint와 빈 forms를 생성한다. 필드 누락과 명시적인 None은 구분한다. `body_truncated=True`인 excerpt도 best-effort로 파싱한다. 별도 warning/body 필드는 추가하지 않는다.

## Header Policy

기존 `inspect_headers`가 반환한 고정 8개 관찰값만 dict로 변환한다. present=True이면 정리된 value, present=False이면 None이다. Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Strict-Transport-Security, Cache-Control, Pragma만 포함한다. Raw Response Header 전체를 복사하지 않는다.

## Cookie Policy

HTTP Tool의 `output["cookies"]` 각 dict를 `CookieInfo.model_validate`로 검증한다. name, secure, http_only, same_site, domain, path, max_age, expires 메타데이터만 허용한다. 잘못된 bool, 필수값 누락, raw value 등 추가 필드는 실패한다. 마스킹된 Set-Cookie를 다시 파싱하지 않는다. 오류에는 검증 입력값을 포함하지 않는다.

## Content-Type Policy

세미콜론 이전 MIME만 취하고 공백 제거 및 소문자화를 적용한다. 한 응답만 관찰하므로 content_types는 정규화된 MIME 1개 또는 빈 리스트다. None 및 빈 MIME은 빈 리스트다.

## Authentication Detection Policy

수집된 Form에 type이 password인 Field가 있을 때만 True. /login, /auth, /signin 경로 또는 password라는 필드 이름만으로 추측하지 않는다.

## Session Detection Policy

쿠키 이름의 case-insensitive exact match만 사용한다: session, sessionid, jsessionid, phpsessid, connect.sid. 다른 쿠키 및 접두/접미 변형은 False다. 쿠키 값과 JWT를 분석하지 않는다. 두 bool은 관찰 힌트이며 취약점 판단이 아니다.

## HTTP Tool Integration / Safety Responsibility

WEB 요청 여부를 HTTP 호출 전에 검사한다. 기존 http_request를 단 한 번 호출하며 GET, follow_redirects=True, target_url, test_id, allowlist를 전달한다. Redirect 안전성, Scope, 네트워크 I/O는 기존 HTTP Tool이 담당한다. Observer에는 직접 네트워크 클라이언트, Safety Gate 복제, 재귀 Crawl이 없다. AssessmentRequest를 수정하지 않는다.

SUCCESS 이외 FAILED / TIMEOUT / BLOCKED / UNSUPPORTED는 RuntimeError로 종료한다. 메시지는 고정 문구로 Tool error.code / message / 원본 예외 / 응답 데이터를 노출하지 않는다. 필수 output 키 final_url / headers / cookies / content_type / body_excerpt의 누락 또는 잘못된 타입은 ValueError로 명시적으로 실패한다. Cookie 검증과 파서 조립 오류도 입력값 없는 메시지로 변환한다.

## Observation Flow

```text
AssessmentRequest
        → http_request
        → final URL / safe headers / CookieInfo / body excerpt
        → endpoint_collector / form_parser / header_inspector
        → WebTargetContext

Raw Cookie Value:
NOT STORED

Raw Response Body:
NOT STORED IN CONTEXT

Ground Truth:
NOT AVAILABLE TO OBSERVER

Benchmark Result:
NOT AVAILABLE TO OBSERVER
```

## Sensitive Data Policy / Ground Truth Separation / Benchmark Separation

Raw Cookie Value / Raw Set-Cookie / Authorization / Proxy-Authorization / API Key / 입력 필드 value / 본문 전체를 Context에 저장하지 않는다. 테스트의 private-token / raw-password / super-secret-cookie가 결과 JSON에 없음을 검증했다. HTTP output의 임의 추가 정보는 조립 대상에 포함하지 않는다. Context의 ground_truth_id / known_vulnerability / expected_ground_truth / expected_finding / zap_result / semgrep_result / benchmark_result / benchmark_finding 주입을 extra forbid로 거부한다.

Observer는 Ground Truth 또는 Benchmark 파일을 읽지 않는다. LLM, Planner, Registry, Analyzer, Finding, Active Testing 연결은 없다.

## Unit Test Result

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_web_observer.py -q
72 passed in 0.41s
```

HTML / Non-HTML / 최종 URL / MIME / 빈 HTML / truncated HTML / 8개 Header / CookieInfo / auth 및 session hint / 실패 상태 / 누락 및 타입 오류 / 민감값 미보존 / 모델 검증 / 요청 미변경 / HTTP 호출 계약 / 직접 네트워크 import 부재: PASS.

테스트는 실제 ToolExecution을 반환하는 async HTTP mock과 기존 Passive Parser를 사용한다. 실제 인터넷 호출은 없다. async 테스트 실행은 기존 테스트 방식과 동일한 표준 라이브러리 asyncio.run을 사용한다.

## Full Regression Result

```text
.venv\Scripts\python.exe -m pytest -q
649 passed in 2.68s
```

기존 577개 및 신규 72개 통과. Day 1/2 모델, Safety Gate, HTTP Tool, Endpoint / Form / Header / Cookie Tool, Cookie Pipeline Bridge, Observer를 포함한다.

## Import Validation / Scope Check

```text
.venv\Scripts\python.exe -c "from secureprobe.web.observer import observe_web_target; from secureprobe.models import WebTargetContext; print('IMPORT_OK')"
IMPORT_OK
git diff --check
PASS
```

변경 범위는 위 파일 및 기존 작업지침의 버전 관리로 제한한다. 기존 5개 Passive Tool / Safety Gate / Agent / Source / Report / SecureBoard / 기준 문서 / dependency 변경 없음.

## Issues

- 발견된 기존 Passive Tool 결함 및 미해결 테스트 실패 없음.
- 최초 테스트 실행에서 미설치 pytest-asyncio marker를 사용한 부분을 기존 asyncio.run 방식으로 수정했다. 신규 dependency 추가 없음.
- Truncated HTML은 제공된 prefix에서만 추출하므로 뒤쪽 Endpoint / Form은 관찰할 수 없다. JavaScript 실행 및 인증 로그인은 수행하지 않는다.
- 검증은 HTTP mock 기반이다. 실제 SecureBoard Lab 통합 검증은 Lab 전달 이후 별도 수행 대상이다.
- 허용된 URL/메타데이터 자체에 포함된 임의의 비밀 문자열을 탐지하는 범용 redactor는 구현하지 않는다. 원문 대신 기존 Tool의 구조화된 메타데이터를 사용한다.

## Day 8 Completion

READY TO CLOSE

```text
D08-T01 Safety Gate             COMPLETED
D08-T02 http_request            COMPLETED
D08-T03 endpoint_collector      COMPLETED
D08-T04 form_parser             COMPLETED
D08-T05 header_inspector        COMPLETED
D08-T06 cookie_inspector        COMPLETED
D08-T06A Cookie Pipeline Bridge COMPLETED
D08-T07 WebTargetContext        COMPLETED

DAY 8 — COMPLETED
```

## Next Task

D09-T01 — Tool Registry

이번 작업에서 자동 착수하지 않는다.

## Commit / Push

Commit message: `feat: build web target context`. 검증된 변경을 main에 커밋하고 origin/main에 일반 push한다. 실제 SHA 및 push 결과는 작업 완료 보고에 기록한다.
