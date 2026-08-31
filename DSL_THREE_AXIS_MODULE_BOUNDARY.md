# DSL Three-Axis Module Boundary

Status: **PHYSICAL SEPARATION AUTHORITY / ACTIVE / 2026-08-31 KST**

이 문서는 `DSL_THREE_AXIS_FINAL_TARGET.md`의 3축을 실제 코드베이스에서 서로 간섭 없이 개발·실행하기 위한 물리 분리 규칙을 정의한다.

핵심 원칙은 단순하다.

```text
각 축은 별도 폴더 / 별도 내부 구현
각 축은 독립 실행 가능
축 사이 직접 import / 내부 DB 접근 / 내부 상태 참조 금지
상호 연동은 표준 Request -> Response Bridge만 허용
확장 시 내부 구현은 자유롭게 변경
외부 영향은 표준 입출력 계약 버전에서만 관리
```

즉, **내부는 자유롭게 진화하고 경계는 안정적으로 유지한다.**

---

## 1. 목표 폴더 구조

최종 물리 구조는 다음 형태를 기준으로 한다.

```text
axes/
  axis1_dsl/
    core/
    indicators/
    runtime/
    tests/
    README.md

  axis2_selection/
    engine/
    conditions/
    ranking/
    tests/
    README.md

  axis3_monetization/
    strategies/
    crud/
    evaluation/
    tests/
    README.md

bridges/
  contracts/
    common/
    axis1/
    axis2/
    axis3/
  adapters/
  routing/
  tests/

chart_bridge/
  ... existing generic chart bridge ...
```

현재 기존 코드를 즉시 대규모 이동하지 않는다. 위 구조는 **최종 배치 권한**이며, 실제 이동은 축별로 micro-tranche와 regression을 거쳐 수행한다.

---

## 2. AXIS 1 — DSL Capability Engine

폴더 권한:

```text
axes/axis1_dsl/
```

책임:

```text
DSLParser
DSLSemanticAnalyzer
DSLRuntime
BacktestEngine
BrokerEmulator
MTF
cascading/context binding
built-in indicators
additive user indicators
state/order/execution/risk
chart projection용 계산 결과
```

금지:

```text
고베타 선별 규칙
주도섹터 선별 규칙
특정 Condition CRUD 의미
특정 Strategy CRUD 계보/수익화 정책
특정 종목/venue/timeframe 예외
```

AXIS 1은 **무엇을 표현하고 결정론적으로 실행할 수 있는가**만 책임진다.

---

## 3. AXIS 2 — Semi-Condition Selection

폴더 권한:

```text
axes/axis2_selection/
```

책임:

```text
Universe 입력
cross-sectional feature 계산/수신
filter
rank
top-N
Condition CRUD
selection evidence
Candidate Set 반환
```

예상 condition 재료:

```text
고베타
강세
Close > EMA120
position
sector / leader / follower relation
normalized Histogram strength/rank
relative strength
turnover / capital-flow
```

중요:

```text
Selector는 주문을 만들지 않는다.
Selector는 Strategy를 실행하지 않는다.
Selector의 결과는 Candidate Set + evidence다.
```

---

## 4. AXIS 3 — Strategy Monetization

폴더 권한:

```text
axes/axis3_monetization/
```

책임:

```text
Strategy CRUD
Baseline 보존
strategy lineage/version
candidate별 strategy 선택
AXIS 1 실행 요청 조립
결과 비교
chart/backtest validation 결과 연결
promote / reject / archive
맞춤형 수익전략 연구 workflow
```

금지:

```text
DSL Parser/Runtime를 자체 구현
Selector filter/rank를 자체 구현
Chart 계산 재구현
Feature Catalog baseline 수정
```

AXIS 3은 **어떤 후보에 어떤 전략 버전을 적용하고 성능을 어떻게 비교/채택할 것인가**를 책임진다.

---

## 5. 축 간 직접 참조 금지

다음은 금지한다.

```text
axis2_selection -> axis1_dsl 내부 모듈 import
axis3_monetization -> axis1_dsl 내부 class 직접 import
axis3_monetization -> axis2_selection 내부 repository/DB 직접 접근
axis1_dsl -> Condition CRUD 조회
axis1_dsl -> Strategy CRUD 조회
```

허용되는 공통 의존성은 **표준 계약 정의**뿐이다.

```text
bridges/contracts/*
```

각 축은 계약 객체를 받아 처리하고 계약 객체를 반환한다.

---

## 6. 표준 Request / Response Envelope

모든 축의 Bridge는 공통 envelope를 사용한다.

### Request

```text
schema_version
request_id
request_type
as_of
payload
context_refs
provenance
```

### Response

```text
schema_version
request_id
status
result
evidence
diagnostics
provenance
```

원칙:

```text
필수 field 의미는 version 동안 불변
새 field는 backward-compatible additive가 기본
breaking change는 schema_version 상승
축 내부 private state를 response에 노출하지 않음
모든 결과는 request_id로 추적 가능
```

---

## 7. 축별 표준 결과

### AXIS 1 Response

예상 `result`:

```text
compiled_strategy_identity
execution_result
metrics
orders / fills / trades
indicator_series
intermediate_series
threshold_series
permission_series
markers
```

Chart가 사용할 값도 AXIS 1/전략 실행 결과에서 projection으로 받으며 Chart가 다시 계산하지 않는다.

### AXIS 2 Response

예상 `result`:

```text
candidate_set_id
as_of
candidates[]
  symbol
  rank
  score/features
  matched_conditions
  evidence
```

이 결과는 주문 의미가 아니다.

### AXIS 3 Response

예상 `result`:

```text
strategy_run_id
strategy_id
strategy_version
candidate_set_id
axis1_execution_ref
comparison
validation_status
promotion_status
```

AXIS 3이 AXIS 1 내부 객체를 소유하지 않고 참조/표준 결과만 가진다.

---

## 8. 표준 Bridge 흐름

최종 E2E는 다음과 같다.

```text
Client / UI
    |
    | SelectionRequest
    v
[AXIS 2]
    |
    | CandidateSetResponse
    v
[AXIS 3]
    |
    | StrategyExecutionRequest
    v
[AXIS 1]
    |
    | ExecutionResponse + projections
    v
[AXIS 3]
    |
    | Monetization/ValidationResponse
    v
Client / Chart / UI
```

각 화살표가 Bridge 계약이다.

Bridge는 routing/serialization/version compatibility를 담당하고, 전략/선별/지표 의미를 새로 계산하지 않는다.

---

## 9. 확장 시 변경 규칙

예를 들어 AXIS 2에 새로운 `capital_flow_score`를 추가하더라도:

```text
AXIS 2 내부 구현 추가
 -> Candidate evidence의 additive field로 노출
 -> AXIS 1 수정 없음
 -> AXIS 3은 필요할 때만 그 field를 사용
```

AXIS 1에 새 사용자지표를 추가하더라도:

```text
AXIS 1 additive indicator
 -> ExecutionResponse projection 추가
 -> AXIS 2 수정 없음
 -> AXIS 3 전략이 필요할 때 호출
```

AXIS 3에 새 Strategy CRUD 정책을 추가하더라도:

```text
AXIS 3 내부 변경
 -> AXIS 1 request contract 유지
 -> AXIS 2 Candidate Set contract 유지
```

따라서 확장 비용은 **표준 입출력부의 additive 변경 또는 version adapter**로 제한한다.

---

## 10. Bridge versioning 원칙

권장 형태:

```text
three_axis.common/v1
axis1.execution/v1
axis2.selection/v1
axis3.monetization/v1
```

새로운 내부 로직은 schema version을 올릴 이유가 아니다.

다음 경우에만 breaking version을 고려한다.

```text
필수 field 의미 변경
기존 field 삭제
기존 소비자가 해석할 수 없는 type 변경
실행 시점/causality contract 변경
```

그 외에는 additive field + adapter를 우선한다.

---

## 11. 테스트 경계

각 축은 자체 test suite를 가진다.

```text
axis1 tests = DSL/Runtime/Backtest/Broker deterministic contract
axis2 tests = filter/rank/top-N/evidence reproducibility
axis3 tests = CRUD/version/strategy selection/comparison workflow
bridge tests = request/response schema + compatibility + routing
E2E tests = Axis2 -> Axis3 -> Axis1 -> Axis3 결과 연결
```

한 축의 내부 test가 다른 축 내부 구현을 직접 import해 검증하지 않는다.

---

## 12. 개발 순서

현재 프로젝트에서는 대규모 폴더 이동부터 하지 않는다.

```text
1. AXIS 1 현재 조합능력 audit 완료
2. 부족한 AXIS 1 일반 기능만 보완
3. bridges/contracts 최소 v1 정의
4. AXIS 2 새 폴더에서 독립 개발 시작
5. AXIS 2 -> Candidate Set 계약 고정
6. AXIS 3 새 폴더에서 Strategy CRUD 독립 개발
7. AXIS 3 -> AXIS 1 표준 실행 Bridge 연결
8. E2E 조건선별 -> 전략 -> 차트/백테스트 검증
9. 안정화 후 기존 코드의 AXIS 1 물리 이동을 별도 migration으로 검토
```

기존 trusted DSL Core를 폴더 정리만을 이유로 먼저 이동하지 않는다.

---

## 13. 완료 기준

3축 분리는 다음이 성립할 때 완료다.

```text
각 축을 독립적으로 개발/테스트/실행 가능
축 간 직접 내부 참조 없음
모든 상호연동은 versioned Request/Response 계약
Chart는 projection 소비만 수행
한 축의 기능 확장이 다른 축 Core 수정을 강제하지 않음
breaking change는 Bridge adapter/version에서 흡수
```

이 구조가 유지되면 프로젝트가 커져도 각 축은 독립적으로 고도화할 수 있고, 통합 비용은 표준 입출력 경계에서 관리할 수 있다.
