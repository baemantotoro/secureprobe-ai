# D02-T04 — Validation Unit Test Result v0.1

## 1. 작업 ID

D02-T04

## 2. 작업명

Validation Unit Test

## 3. 상태

Status: COMPLETED

## 4. 목적

SecureProbe AI의 Model Layer가 잘못된 Structured Output과 잘못된 입력을 실제로 거부하는지 검증한다.

## 5. 검증 범위

다음 네 가지 축을 중심으로 테스트를 작성했다.

- Enum 값 검증
- Required field / boundary condition 검증
- Extra field / sensitive field / ground truth leakage 방지
- JSON serialization / round-trip / whitespace / datetime 처리

## 6. 테스트 파일

```text
tests/unit/test_schema_validation.py
```

## 7. 구현 원칙

- 초기 단계에서는 Schema 계약이 대부분 만족되었지만, `evidence_ids`가 누락되었을 때 빈 리스트로 대체되는 동작이 보안 계약을 약하게 만들고 있음을 확인했다.
- 해당 문제는 필드가 기본값을 가지고 있었기 때문에 발생한 모델 계층의 누락이며, 이를 `required` contract로 고정하는 최소 수정으로 해결했다.
- 보안 계약상 필요한 traceability를 엄격하게 유지하기 위해 Production Model을 정정했다.

## 8. 검증 결과

```text
72 passed in 0.24s
```

## 9. 실행 명령

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\unit\test_schema_validation.py -q
```

## 10. 전체 회귀 검증

```text
99 passed in 0.94s
```

## 11. 결정

- 다음 Task로 진행 가능: Yes
- 이유: Validation Contract가 실제로 동작하고 있으며, Day 2의 모델 범위는 모두 통과했다.

## 12. 비고

이번 Task는 기능 추가가 아니라 Schema Defect Correction과 Contract 증명에 집중했다.

- Production Code Changed: Yes
- Changed File: `secureprobe/models/finding.py`
- Change Type: Schema Defect Correction
- Scope Expansion: No
- Contract Enforcement Fix: Yes
- Root Cause: `evidence_ids`가 `default_factory=list`로 채워지면서 필드 누락이 빈 Evidence로 통과하던 문제를 발견했다.
- Fix: `CandidateFinding.evidence_ids` / `Finding.evidence_ids`를 required contract로 정정했다.
- Required Contract: 두 필드에 `Field(min_length=1)`을 적용하여 필드 누락과 빈 Evidence 목록을 모두 거부한다.
- Validation Goal: 실제로 거부되는 입력 사례를 점검하고, 보안 traceability를 보장하는지 확인했다.

## 13. Security Contract

- Raw Password Injection: PASS
- Evidence-less Candidate: PASS
- Evidence-less Finding: PASS
- Missing Candidate evidence_ids: PASS
- Missing Finding evidence_ids: PASS
- Invalid Finding validation_status: PASS
- Ground Truth Leakage: PASS
- Benchmark Leakage: PASS
- Internal Reasoning Injection: PASS
- Extra Field Rejection: PASS

## 14. Validation Coverage

- Invalid Enum / Literal: PASS
- Required Field Validation: PASS
- Boundary Validation: PASS
- Malformed Payload: PASS
- Extra Field Rejection: PASS
- Sensitive Field Injection: PASS
- Evidence Traceability: PASS
- Ground Truth Leakage: PASS
- Benchmark Leakage: PASS
- Internal Reasoning Injection: PASS
- JSON Serialization: PASS
- JSON Round-trip: PASS
- Mutable Default Isolation: PASS
- Datetime Validation: PASS
- Whitespace Validation: PASS

## 15. Import Validation

Import Validation: PASS

```powershell
.\.venv\Scripts\python.exe -c "from secureprobe.models import AssessmentRequest, AssessmentResult, TestPlan, ToolSelection, ToolExecution, ToolError, Evidence, CandidateFinding, Finding, AgentEvent; print('IMPORT_OK')"
```

```text
IMPORT_OK
```

## 16. Schema Consistency

Schema Consistency: PASS

`docs/02_spec/DATA_SCHEMA_v0.1.md`와 `docs/01_architecture/AGENT_FLOW_v0.1.md`의 D02-T04 확인 항목을 모델 및 기존 검증 테스트와 대조했다.

- `CandidateFinding.evidence_ids` / `Finding.evidence_ids`: 필수이며 빈 목록을 거부한다.
- ValidationStatus 허용값: `UNVERIFIED`, `TOOL_VERIFIED`, `MANUAL_REQUIRED`, `MANUAL_VERIFIED`, `REJECTED`.
- Ground Truth: Assessment 입력과 분리하며 추가 필드 주입을 거부한다.
- Benchmark: Agent 입력과 분리하며 ZAP / Semgrep 결과 필드 주입을 거부한다.
- Internal reasoning: 내부 추론 필드 주입을 거부하며 짧은 reasoning summary만 허용한다.

## 17. Issues

None

## 18. Day 2 Completion

READY TO CLOSE

```text
D02-T01 Common Enum        COMPLETED
D02-T02 Assessment Model   COMPLETED
D02-T03 Agent Model        COMPLETED
D02-T04 Validation Test    COMPLETED
```

이번 결과 문서 최종화에서는 Production Code와 Test Code를 수정하지 않았다.

## 19. Next Task

D03-T01 — SecureBoard Project 생성
