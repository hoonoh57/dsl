# Quant DSL Current State

Status: **DSL_CORE_PHASE1_TRUSTED / STRATEGY-RESEARCH PHASE ACTIVE / BASELINE-FROZEN / REMEDIATION_REQUIRED**  
Updated: 2026-08-31 KST

## Recovery authority

세션 전환 시 읽는 순서:

```text
1. SESSION_HANDOFF.md
2. DSL_STRATEGY_RESEARCH_PHILOSOPHY.md
3. CURRENT_STATE.md
4. current dsl-live-studio branch/head
```

Exact user-local PASS evidence and 최신 사용자 결정이 stale 문서보다 우선한다.

사용자가 새 세션에서 `세션이어가!`라고 하면 `SESSION_HANDOFF.md`의 복구 규칙에 따라 **현재 전략 연구 단계부터 즉시 이어간다.**

## Main product direction

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
3. Universe / Permission / Context / Execution / Risk는 실제 필요가 확인될 때 일반 기능으로 확장
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

Chart가 재계산하지 않는다.

## Long-term selection direction

궁극적인 연구 방향의 한 형태:

```text
지수 고베타
+ 주도섹터/대장/추종 관계
+ Close > EMA120
+ normalized Histogram strength/rank
 -> 강세 후보 선별
 -> MACD + JMA timing
 -> 종목당 소수의 고품질 진입
```

장기적으로:

```text
DSL SYMBOL   = single-symbol indicator/trigger/permission/execution
DSL UNIVERSE = cross-sectional filter/rank/top-N/relative selection
```

하지만 Universe 언어는 지금 성급히 확장하지 않는다.

## Immediate next work

새 전략을 바로 코딩하기 전에 **DSL 조합능력 audit**을 수행한다.

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

상세 철학은 `DSL_STRATEGY_RESEARCH_PHILOSOPHY.md`가 권한 문서다.

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
