# SecureProbe AI

AI Agent 기반 웹·소스코드 보안진단 PoC.

20일 동안 취업 포트폴리오를 목적으로 개발한다.

## 주요 구성

1. SecureBoard Lab
   - 자체 취약 테스트 웹 애플리케이션

2. SecureProbe AI
   - Web Security Assessment
   - Source Security Assessment

3. Benchmark
   - Web: OWASP ZAP
   - Source: Semgrep

4. Evaluation
   - Ground Truth
   - TP / FP / FN
   - Precision / Recall
   - Manual Verification

## Agent Flow

Observe
→ Plan
→ Select Tool
→ Execute
→ Analyze
→ Verify
→ Report

## Security Notice

본 프로젝트의 Active Security Assessment는
직접 소유한 Lab,
localhost,
Docker 환경,
명시적으로 허가받은 테스트 대상에서만 수행한다.

외부 실서비스에 대한 무단 진단을 목적으로 하지 않는다.
