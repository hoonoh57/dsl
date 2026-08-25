# Stage 1 연속 구현·검증 운영정책

Status: **AUTHORITATIVE EXECUTION POLICY / SUPERSEDES PER-WORKSTREAM USER GATES / 2026-08-25 KST**

## 1. 목적

이 문서는 `PRODUCT_IMPLEMENTATION_PLAN.md`의 Stage 1 구현축 `S1.0 ~ S1.13` 총 14개를 실제로 수행하는 운영 방식을 고정한다.

제품 방향과 각 Workstream의 기능 범위·Victory 정의는 `PRODUCT_IMPLEMENTATION_PLAN.md`를 따른다. 이 문서는 **개발 중간 검증과 사용자 개입 시점**만을 더 강한 규칙으로 정의한다.

## 2. 최우선 원칙

Stage 1의 14개 구현축은 사용자에게 중간 UI 검증을 요구하지 않고 **연속 구현한다.**

```text
S1.0 Authority / State Hygiene
  -> S1.1 Engine Trust Boundary
  -> S1.2 DSL Capability Completion
  -> S1.3 Data Contract / Provenance
  -> S1.4 Backtest Evidence Engine
  -> S1.5 Immutable Experiment Store
  -> S1.6 Parameter Seeker
  -> S1.7 Result Analyzer
  -> S1.8 Human-Mediated LLM Improvement Loop
  -> S1.9 Improvement Episode Memory
  -> S1.10 Target-Return Improvement Loop
  -> S1.11 Single-Symbol Chart Audit
  -> S1.12 Semi-Automation Product UX
  -> S1.13 Methodology Validation
```

각 축을 구현할 때 개발자는 원격에서 가능한 자동검증을 스스로 수행하고, 발견되는 단순 오류·회귀·배선 누락은 즉시 수정한다. **사용자에게 각 축의 검증을 요청하거나 pull/test를 반복 요청하지 않는다.**

## 3. 개발 우선순위

현재 목표는 완벽한 국지 최적화가 아니라 **Stage 1 전체 제품이 실제로 가동되는 완성형 vertical slice**다.

따라서 구현 중에는 다음 순서를 따른다.

1. 전체 기능 계약을 끝까지 연결한다.
2. 기존에 가동 가능한 코드는 적극 재사용한다.
3. 빈 UI, placeholder, 죽은 경로가 Stage 1 핵심 workflow를 막지 않게 한다.
4. 각 Workstream 내부의 사소한 품질 개선 때문에 다음 Workstream으로 진행이 멈추지 않게 한다.
5. 단, fail-closed, 미래참조 금지, 회계/체결 의미, Experiment 불변성처럼 결과 신뢰를 파괴하는 결함은 발견 즉시 수정한다.
6. 테스트를 녹색으로 만들기 위한 compatibility bypass, assertion 약화, dummy/synthetic product fallback은 금지한다.

## 4. 검증 시점

검증은 세 층으로 나눈다.

### A. 개발 중 자동검증

각 구현축에서 원격으로 확인 가능한 범위는 개발자가 직접 확인한다.

- import / syntax / unit test
- parser/semantic fail-closed
- API contract
- DB migration/schema
- deterministic fixture
- backtest reconciliation
- seeker deterministic run
- experiment lineage
- HTTP/UI smoke route

실패는 `test defect / product defect / authority drift / environment issue / unknown`으로 분류하고 수정한다.

### B. Stage 1 통합 운영테스트·가혹테스트

`S1.0 ~ S1.13` 기능 구현이 모두 연결된 후 별도의 테스트 계획을 코드로 구현하고 한 번에 수행한다.

가혹테스트에는 최소 다음을 포함한다.

- 다양한 유효/무효 DSL 대량 compile
- 고정 데이터에서 반복 실행 determinism
- batch/streaming parity
- bar_close/next_open/order lifecycle/accounting matrix
- Seeker 수백~수천 candidate 반복 및 duplicate cache/resume
- Experiment/Improvement lineage 장기 누적
- invalid LLM response / malformed DSL / rejected candidate 보존
- 목표수익 loop iteration/budget/plateau 종료
- 장시간 반복 run에서 memory/resource 누수 탐지 가능한 범위
- UI/API end-to-end smoke
- 대표 전략군 regression

### C. 사용자 UI 검증

Stage 1 전체가 자동 운영테스트·가혹테스트를 통과하거나, 남은 환경 의존 이슈가 명확히 격리된 뒤에만 사용자에게 UI 검증을 요청한다.

그 시점의 사용자 검증은 개별 파일이나 함수가 아니라 다음 전체 workflow를 본다.

```text
전략 입력
 -> DSL
 -> 실행/차트
 -> Baseline 박제
 -> Parameter Seeker
 -> 결과 분석
 -> LLM feedback prompt 생성
 -> LLM 응답 paste
 -> revised DSL 검증/실행
 -> 재-Seeker
 -> Experiment 비교/승격/거절
 -> 반복/stop
```

## 5. 중간 보고 정책

사용자에게 중간 검증을 요구하지 않는다. 대화상 보고가 필요할 때도 다음만 간결히 알린다.

- 현재까지 구현된 Stage 1 범위
- 자동검증 결과
- 현재 막힌 환경 의존사항이 있는지
- 다음 구현축

정상 성공 로그를 길게 나열하지 않는다.

## 6. Stage 1 완료 판정

Stage 1은 `S1.0 ~ S1.13` 소스가 존재한다고 완료가 아니다.

다음 순서가 모두 충족되어야 한다.

```text
14개 Workstream 기능 연결 완료
 -> 자동 단위/통합 검증
 -> 운영테스트
 -> 가혹테스트
 -> 결함 수정 및 재시험
 -> 사용자 UI 검증
 -> 보완 tranche
```

사용자 UI 검증 전 상태는 `IMPLEMENTED_AWAITING_SYSTEM_VALIDATION` 또는 실제 결과에 맞는 상태로 표현한다. 가혹테스트와 사용자 검증 전에는 `완료`, `전체 PASS`, `수익성 검증`을 선언하지 않는다.

## 7. 이후 Stage

Stage 1의 전체 UI 검증과 보완이 끝난 뒤에 Stage 2 Multi-Symbol Application으로 이동한다. Stage 2 이후도 같은 방식으로 **단계 전체 구현 -> 자동 운영/가혹테스트 -> 사용자 UI 검증 -> 보완** 순서를 사용한다.
