# Quant DSL Current State

Status: **DSL_CORE_PHASE1_TRUSTED / STRATEGY-RESEARCH PHASE ACTIVE / THREE-AXIS FINAL TARGET ACTIVE / PHYSICAL-AXIS-SEPARATION ACTIVE / BASELINE-FROZEN / REMEDIATION_REQUIRED**  
Updated: 2026-08-31 KST

## Recovery authority

세션 전환 시 읽는 순서:

```text
1. SESSION_HANDOFF.md
2. DSL_STRATEGY_RESEARCH_PHILOSOPHY.md
3. DSL_THREE_AXIS_FINAL_TARGET.md
4. DSL_THREE_AXIS_MODULE_BOUNDARY.md
5. CURRENT_STATE.md
6. current dsl-live-studio branch/head
```

Exact user-local PASS evidence and 최신 사용자 결정이 stale 문서보다 우선한다.

사용자가 새 세션에서 `세션이어가!`라고 하면 `SESSION_HANDOFF.md`의 복구 규칙에 따라 **현재 전략 연구 단계부터 즉시 이어간다.** 3축의 최종 제품 구조는 `DSL_THREE_AXIS_FINAL_TARGET.md`, 실제 물리 분리와 표준 Bridge 계약은 `DSL_THREE_AXIS_MODULE_BOUNDARY.md`가 권한 문서다.

## Main product direction — three-axis final target

최종 제품 목표:

```text
AXIS 1. DSL Capability Engine
= 제약이 적은 독립 전략 표현/실행 언어
= MTF + cascading/context + built-in/user indicators + logic + execution/risk

AXIS 2. Semi-Condition Selection
= 여러 종목 중 거래가치가 높은 후보군 선별
= filter/rank/top-N + 고베타/강세/EMA120/position/sector relation/normalized strength

AXIS 3. Strategy Monetization
= Candidate Set에 Strategy CRUD 전략 적용
= chart/backtest/version/compare를 통한 맞춤형 수익화
```

End-to-End 목표:

```text
조건선별
 -> Candidate Set
 -> DSL 전략
 -> 차트 이유 검증
 -> 백테스트/비교
 -> 맞춤형 수익화
```

세 축의 권한은 섞지 않는다.

```text
Selector = 누구를 볼 것인가
DSL      = 무엇을 어떻게 표현/실행할 것인가
Strategy = 어떤 수익전략을 적용할 것인가
Chart    = 계산하지 않고 그 이유를 보여주는 계측기
```

### Physical separation authority

3축은 최종적으로 별도 폴더에 물리 분리한다.

```text
axes/
  axis1_dsl/
  axis2_selection/
  axis3_monetization/

bridges/
  contracts/
  adapters/
  routing/
```

축 사이 직접 import, 내부 DB/상태 접근을 금지한다. 상호연동은 versioned 표준 `Request -> Response` Bridge만 허용한다.

```text
AXIS 2 -> CandidateSetResponse
AXIS 3 -> StrategyExecutionRequest
AXIS 1 -> ExecutionResponse + projections
AXIS 3 -> Monetization/ValidationResponse
```

내부 구현 변경은 각 축 안에서 자유롭게 수행하고, 외부 영향은 표준 입출력 계약의 additive field 또는 version adapter에서 흡수한다. 기존 trusted DSL Core는 폴더 정리를 이유로 먼저 대규모 이동하지 않고 migration은 별도 tranche로 수행한다.

실제 direct Core path는 계속 deterministic하다.

```text
UI / Chart
 -> strategy observation and authoring
 -> local DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime
 -> BacktestEngine
 -> BrokerEmulator
 -> chart / diagnostics / validation
 -> Strategy CRUD iteration
```

LLM은 DSL/전략 작성 보조자다. deterministic Parser/Semantic/Runtime/Backtest/Broker가 실행 권한을 가진다.

Current product branch:

```text
dsl-live-studio
```

## Governing architecture

Core DSL은 generic/deterministic하게 유지한다. 이미 globally validated된 로직에 특정 종목, venue, timeframe, 전략 예외를 삽입하지 않는다.

```text
Chart Core      = generic drawing/pane/geometry
Bridge/Runtime  = lifecycle/routing only
Add-on          = computation meaning/strategy state
JSON            = persistence only
```

Chart는 DSL 계산을 재계산하지 않고 projection을 표시한다.

3축 추가 권한 분리:

```text
Feature Catalog = DSL 기능 검증 SSOT / 불변
Condition CRUD  = Semi-Condition 선별 규칙 / 버전
Strategy CRUD   = 수익전략 / 복제 / 버전 / 비교 / 폐기
```

Selector는 주문 의미를 소유하지 않고 Candidate Set과 evidence를 반환한다.

## DSL Core Phase 1 trusted checkpoint

기존 사용자 화면 checkpoint:

```text
registered DSL feature catalog      75 / 75 PASS
registered execution invariants     23 / 23 PASS
Live Studio direct-Core path        TRUSTED
v2 + v3 + v4 invariant UI           TRUSTED
DSL Core Phase 1                    TRUSTED
```

이 수치는 당시 정의된 Phase 1 surface의 checkpoint다. 이후 additive 기능은 focused 검증을 별도로 가진다.

## Recently verified additive capabilities

### `user.macd_normalized`

기존 `ta.macd`는 수정하지 않았다.

```text
components:
macd
signal
hist
hist_abs_pct

hist_abs_pct = abs(MACD - Signal) / abs(price) * 100
```

User-local focused evidence:

```text
4 / 4 PASS
```

### `session.day_return_pct()`

범용 정의:

```text
(close / session.day_open() - 1) * 100
```

NXT / `_AL` / live 특수 분기 없음.

User-local focused evidence:

```text
4 / 4 PASS
```

## Timeframe and chart execution

등록 Feature Catalog의 `timeframe = "1d"`는 example fixture 기본값이다. 차트 삽입 실행의 authority는 현재 차트 timeframe이다.

```text
1m chart -> DSL 1m
5m chart -> DSL 5m
15m chart -> DSL 15m
1d chart -> DSL 1d
```

User-local evidence:

```text
chart_bridge/dsl_chart_timeframe_policy.test.mjs
5 / 5 PASS
```

사용자 차트 화면에서 `ta.macd`의 1m 삽입 성공을 확인했다.

## Execution UX

사용자가 서버 실행명령을 외우지 않도록 루트에 다음 entrypoint를 둔다.

```text
start.bat
restart.bat
stop.bat
```

의도:

```text
start   = managed stack reset + Live Studio + Chart Bridge + health + chart browser
restart = servers unchanged + chart browser restart only
stop    = managed chart/server shutdown
```

정적 launcher test의 올바른 명령:

```powershell
python -m unittest discover -s tests -p "test_dsl_stack_entrypoints.py" -v
```

최종 user-local static test PASS는 아직 보고되지 않았다.

## Strategy research phase — active

현재 `ta.macd` 기본 교차전략은 **MACD_BASELINE_V1**로 동결한다.

```text
Feature Catalog = DSL 기능 검증 / baseline / 불변
Strategy CRUD   = 수익전략 실험 / 버전 / 비교 / 삭제
```

현재 개선 철학:

```text
1. 기존 DSL 조합으로 가능한 전략은 Strategy CRUD에서만 작성
2. 새로운 측정값 자체가 부족할 때만 additive User Indicator
3. Universe / Permission / Context / Execution / Risk는 일반 기능으로 확장
4. 최종적으로 AXIS 2 Selector와 AXIS 3 Strategy를 분리 연결
```

MACD 파라미터를 특정 차트에 맞춰 무한 조정하기보다 다음 측정값을 **전략 Permission 후보**로 연구한다.

```text
Normalized MACD Histogram strength
JMA normalized slope strength
session.day_return_pct position
```

가능한 조합 예:

```text
MACD crossover AND hist_strength >= H
MACD crossover AND jma_strength >= J
MACD crossover AND (hist_strength >= H OR jma_strength >= J)
MACD crossover AND hist_strength >= H AND jma_strength >= J
```

`H=0.5` 등은 현재 후보 수평선이지 검증된 최적값이 아니다.

## Chart-led research contract

차트는 전략 개발 계측기다.

```text
관찰
 -> 정규화된 series + threshold horizontal line
 -> 손실/수익 구간 비교
 -> 가설
 -> 새 Strategy CRUD
 -> 다른 종목/기간/timeframe 검증
 -> 이후 통계/백테스트 확대
```

전략 판단에 사용된 중간값은 DSL/Runtime 계산값을 그대로 차트에 표시해야 한다.

```text
MACD
Signal
Histogram
normalized Histogram
JMA strength
position pct
required threshold
permission bool
trigger / result
```

AXIS 2가 구현되면 Selector evidence도 같은 원칙으로 projection한다.

Chart가 재계산하지 않는다.

## AXIS 2 — Semi-Condition Selection target

이제 Universe 방향은 장기 아이디어가 아니라 최종 제품의 독립 축으로 승격되었다.

목표 형태:

```text
Universe
 -> generic filter
 -> rank
 -> top-N
 -> evidence/reasons
 -> Candidate Set
```

실제 전략에서 활용할 수 있는 feature 후보:

```text
지수 고베타
주도섹터/대장/추종 관계
Close > EMA120
normalized Histogram strength/rank
position
relative strength
거래대금/자금유입
```

하지만 이 조건 묶음을 Core에 하나의 특수 함수로 하드코딩하지 않는다. 일반 filter/rank/top-N/relative-selection contract 위에서 **Condition CRUD**가 조합한다.

장기 구분:

```text
DSL SYMBOL   = single-symbol indicator/trigger/permission/execution
DSL UNIVERSE = cross-sectional filter/rank/top-N/relative selection
```

## AXIS 3 — Strategy Monetization target

선별된 Candidate Set에 Strategy CRUD 전략을 적용한다.

```text
Candidate Set
 -> Strategy version
 -> DSL execute
 -> chart observability
 -> backtest / compare
 -> promote / reject
 -> tailored monetization
```

모든 종목에 동일 전략 하나를 강제하지 않는다. 후보군 특성/timeframe/normalized strength/context에 맞는 전략 버전을 비교 가능하게 운용하는 것이 최종 목표다.

Baseline은 계속 불변이다.

```text
MACD_BASELINE_V1
 -> MACD_HIST_V1
 -> MACD_JMA_V1
 -> MACD_HIST_JMA_V1
 -> MACD_HIST_JMA_POSITION_V1
 -> selected-universe strategy variants
```

## Immediate next work

최종 목표가 3축으로 상향되고 물리 분리 원칙이 추가되었어도 **현재 micro-tranche는 바꾸지 않는다.**

먼저 AXIS 1의 **DSL 조합능력 audit**을 수행한다.

```text
1. normalized Histogram direct strategy access
2. JMA up/down/normalized slope direct access
3. session.day_return_pct direct access
4. arithmetic/comparison composition
5. AND/OR/NOT composition
6. strategy parameter/input thresholds
7. intermediate values + thresholds -> chart projection
8. Strategy CRUD vs Feature Catalog separation
```

판정:

```text
가능 -> Core 수정 없음
일반 문법 부족 -> 최소 범용 문법 tranche
측정값 부족 -> additive User Indicator
observability 부족 -> generic projection tranche
persistence 부족 -> separate Strategy CRUD tranche
```

이 audit가 끝난 뒤 **Bridge v1 계약을 먼저 정의한 다음**, AXIS 2를 새 폴더에서 독립 개발한다.

```text
bridges/contracts v1
 -> AXIS 2: Universe -> filter -> rank -> top-N -> evidence -> Candidate Set
 -> AXIS 3: Candidate Set -> Strategy CRUD -> AXIS 1 execution request
 -> AXIS 1: deterministic execution response/projections
```

그 이후에 실제 고베타/강세/EMA120/sector relation/normalized strength 조건을 Condition CRUD에서 조합한다.

상세 권한 문서:

```text
DSL_STRATEGY_RESEARCH_PHILOSOPHY.md
DSL_THREE_AXIS_FINAL_TARGET.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
```

## Deferred / nonclaims

Phase 2/deferred language items:

```text
partial fills
pyramiding
multi-position accounting
on_tick / on_fill rollback semantics
tuple / multi-output indicators
bounded loops
user-defined functions
full TA-Lib differential fixture coverage
```

No synthetic fixture proves profitability. No candidate threshold is optimal without broader evidence. No live trading readiness or repository-wide compliance PASS is claimed.

Broader repository status remains:

```text
REMEDIATION_REQUIRED
```
