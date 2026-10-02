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
- Scope Expansion: No
- Contract Enforcement Fix: Yes
- Root Cause: `evidence_ids`가 `default_factory=list`로 채워지면서 필드 누락이 빈 Evidence로 통과하던 문제를 발견했다.
- Fix: `CandidateFinding.evidence_ids` / `Finding.evidence_ids`를 required contract로 정정했다.
- Validation Goal: 실제로 거부되는 입력 사례를 점검하고, 보안 traceability를 보장하는지 확인했다.
