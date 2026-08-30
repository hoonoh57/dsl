# DSL Human Trading Decision Capability Map

작성일: 2026-08-31
상태: DESIGN BASELINE / 구현 승인 아님

## 1. 목적

현재 DSL의 다음 고도화 기준을 단순 함수 수가 아니라 **사람이 실제 매매 전에 수행하는 판단·참조·분석·행동**으로 재정의한다.

핵심 질문은 다음 하나다.

> 사람이 동일한 데이터와 화면을 보았다면 매매 전에 무엇을 확인하고, 무엇 때문에 거래를 포기하며, 무엇을 비교하고, 무엇을 기다린 뒤 주문하는가?

DSL은 단순 `조건 true -> 주문` 엔진에서 아래와 같은 결정론적 의사결정 파이프라인을 표현·검증할 수 있어야 한다.

```text
UNIVERSE
  -> ELIGIBILITY
  -> HARD GUARDS
  -> MARKET / SECTOR / SYMBOL CONTEXT
  -> REGIME
  -> RELATIVE QUALITY
  -> CAPITAL FLOW / PARTICIPATION
  -> SETUP
  -> TRIGGER
  -> EXECUTION QUALITY
  -> POSITION SIZE
  -> ORDER
  -> POSITION MANAGEMENT
  -> EXIT
  -> COOLDOWN / MEMORY
  -> PORTFOLIO RISK
```

이 문서는 기능 아이디어 수집과 gap map이다. 새 grammar/API를 승인하지 않는다.

---

## 2. 설계 원칙

### 2.1 Signal보다 Permission이 먼저다

사람은 신호가 생겼다는 이유만으로 매수하지 않는다. 먼저 **이 종목/이 시각/이 구간에서 매매해도 되는가**를 판단한다.

따라서 전략 실행 의미는 최소한 다음 세 층을 분리해야 한다.

```text
Permission / Hard Gate
Quality / Score
Trigger / Order
```

- Hard Gate: 하나라도 실패하면 진입 금지.
- Quality: 여러 좋은 조건의 상대적 품질을 계산/비교.
- Trigger: 이미 허가된 후보에서 실제 주문 시점을 결정.

### 2.2 학습보다 결정론적 장비와 계약 우선

횡보구간, VI 근접, 유동성 부족, 최대 익스포저 같은 절대 금지 조건은 학습의 자율판단에 맡기지 않는다.

- 측정값은 Context Feature 또는 Equipment가 제공할 수 있다.
- DSL/Core는 명시된 값과 계약으로 판단한다.
- 같은 입력과 설정이면 같은 허가/차단/주문 결과가 나와야 한다.

### 2.3 Core / Context / Equipment를 구분한다

```text
Core primitive
  언어·상태·주문·포지션·포트폴리오·이벤트 같은 일반 실행 능력

Context feature
  시장/섹터/종목/호가/VI/수급/자금흐름 등 외부 관측값

Equipment / guard
  횡보 금지선, VI 거리 기준, 유동성 절대 기준 등 권위 있는 진입 게이트
```

현재 repo에는 `ctx.*`를 등록된 manifest와 exact-time으로 fail-closed 주입하는 경계가 이미 있으므로, 모든 시장 관측값을 DSL Core 함수로 넣을 필요는 없다.

### 2.4 Chart는 판단 권한이 아니다

Chart는 전략 결과, context, guard 상태와 진입/차단 이유를 시각화할 수 있으나 전략 의미를 재계산하지 않는다.

---

## 3. Human Trading Decision Capability Map

상태 표기:

- `IMPLEMENTED`: 현재 Core/기능 카탈로그에 명확히 존재.
- `PARTIAL`: 기반은 있으나 실전 판단 전체 계약을 충족하지 못함.
- `MISSING`: 현재 확인된 1차 DSL 범위에는 없음.
- `CONTEXT_READY`: Core 기능이 아니라 `ctx.*` 외부 feature로 공급 가능한 기반이 존재.
- `AUDIT_REQUIRED`: 구현 여부/의미를 별도 확인해야 함.

| ID | 사람이 하는 판단/행동 | 필요한 capability | 현재 상태 | 권장 소유 축 | 우선 |
|---|---|---|---|---|---|
| H01 | 거래할 종목 자체를 추림 | universe filter / eligibility | MISSING | Core + Context | S |
| H02 | 거래대금 부족 종목 제외 | turnover / liquidity minimum guard | CONTEXT_READY / 표준 feature MISSING | Context + Equipment | S |
| H03 | 호가가 얇으면 매수 안 함 | spread, depth, depth-at-price, liquidity score | CONTEXT_READY / MISSING | Context + Equipment | S |
| H04 | VI 근처면 좋은 신호도 거부 | VI state, distance-to-VI, exchange event guard | CONTEXT_READY / MISSING | Context + Equipment | S |
| H05 | 횡보구간이면 반복매매 안 함 | range/regime detection + entry suppression | PARTIAL | Core state + Equipment | S |
| H06 | 추세/변동성 상태를 먼저 판단 | trend/range/volatility regime | PARTIAL | Core + Add-on/Equipment | S |
| H07 | 시장 전체가 위험한지 확인 | market risk-on/off context | CONTEXT_READY / 표준 feature MISSING | Context + Equipment | S |
| H08 | 섹터가 강한지 확인 | sector index/context reference | CONTEXT_READY / MISSING | Context | A |
| H09 | 종목이 시장보다 강한지 비교 | cross-symbol relative strength | MISSING | Core Data Context + Context | S |
| H10 | 전일 흐름과 오늘 위치 비교 | prev OHLC, gap, prev range/VWAP/profile | PARTIAL | Core session + Context | A |
| H11 | 최근 N일 대비 현재 신호 강도 비교 | percentile, z-score, normalized strength | PARTIAL/MISSING first-class | Core indicator/statistics | S |
| H12 | 평소 같은 시각 대비 거래대금이 비정상적인지 봄 | time-of-day relative volume/turnover | MISSING | Context/Feature | S |
| H13 | 짧은 시간 큰 자금이 들어오는지 봄 | turnover impulse / acceleration | MISSING | Context/Feature | S |
| H14 | 체결강도/매수우위 확인 | trade intensity, buy/sell pressure, delta | MISSING | Context/Market microstructure | S |
| H15 | 큰 체결이 연속되는지 확인 | large-trade clustering | MISSING | Context/Market microstructure | A |
| H16 | 좋은 후보 중 더 좋은 종목만 선택 | score, rank, top-N | MISSING | Core selection/portfolio | S |
| H17 | 같은 신호라도 품질을 수치화 | deterministic composite score | PARTIAL (수식 조합 가능, first-class 없음) | Core expression | S |
| H18 | 돌파 전에 압축/박스 상태 확인 | compression/range structure | PARTIAL | Indicator/Equipment | A |
| H19 | 돌파가 거래량/대금으로 확인되는지 봄 | breakout quality + confirmation | PARTIAL | Core expression + Context | S |
| H20 | 실패 돌파 후 바로 재진입 안 함 | failed-setup state + cooldown | PARTIAL | Core state | S |
| H21 | 같은 박스에서 반복 신호를 무시 | setup identity + per-zone entry count | PARTIAL/MISSING identity | Core state | S |
| H22 | 하루 손실/진입 횟수 이후 멈춤 | daily entry/loss limit | PARTIAL | Core execution/risk | S |
| H23 | 손절 후 동일 setup 재진입 금지 | trade outcome memory + setup key | PARTIAL/MISSING | Core state/on_fill | S |
| H24 | 장 초반/마감 등 시간대 회피 | session/time window guard | PARTIAL | Core session/execution | A |
| H25 | 현재 가격이 과열 위치인지 판단 | gap/ATR/percentile/distance guards | PARTIAL | Core indicators + Context | A |
| H26 | 주문 전에 스프레드/호가 비용을 확인 | execution-quality preflight | MISSING | Broker/Context | S |
| H27 | 주문이 시장 충격을 만들지 판단 | order size vs depth/ADV | MISSING | Broker/Context | A |
| H28 | 지정가/스탑/취소/OCO 사용 | order lifecycle | IMPLEMENTED major subset | Broker | A |
| H29 | 일부만 체결되면 대응 | partial fill | MISSING | Broker | S |
| H30 | 일부만 청산/추가 진입 | scale in/out / pyramiding | MISSING | Broker/Position | S |
| H31 | 신호 강도와 위험에 맞춰 수량 결정 | position sizing / risk sizing | AUDIT_REQUIRED / insufficient first-class | Portfolio/Risk | S |
| H32 | 여러 종목을 동시에 보유 | multi-position | MISSING | Portfolio | S |
| H33 | 총 노출/섹터 노출 제한 | portfolio exposure caps | MISSING | Portfolio/Risk | S |
| H34 | 현금/평가손익/미실현손익 참조 | portfolio state | MISSING | Portfolio | S |
| H35 | 포트폴리오 전체 DD면 진입 중단 | portfolio drawdown guard | MISSING | Portfolio/Risk | S |
| H36 | 체결 이후 상태에 따라 즉시 판단 | on_fill/on_order events | MISSING | Bar/Event Runtime | A |
| H37 | 열린 봉/틱에서 변화 감시 | on_tick with commit/rollback | MISSING | Bar Runtime | A |
| H38 | 여러 timeframe을 확인 | confirmed MTF | IMPLEMENTED core subset | Data Context | A |
| H39 | 다른 종목/지수를 동시에 참조 | multi-symbol context | MISSING | Data Context | S |
| H40 | 낮은 timeframe 세부 흐름을 상위 전략에서 사용 | lower-TF context/aggregation | PARTIAL/MISSING formal contract | Data Context | A |
| H41 | 거래정지/결측/휴장 등 이상 데이터 회피 | data-quality/session validation | PARTIAL/MISSING | Data Context | A |
| H42 | 반복되는 복합 판단을 함수화 | user-defined functions | MISSING | Language | A |
| H43 | 다중 출력 지표/구조값 사용 | tuple/structured output | MISSING | Language/Type System | A |
| H44 | 후보/구간을 제한 반복 계산 | bounded loops | MISSING | Language | B |
| H45 | 전략 파라미터를 범위로 실험 | parameter declarations/ranges | MISSING | Language/Validation | A |
| H46 | 과최적화를 피하기 위해 IS/OOS 확인 | walk-forward | MISSING | Evaluation | A |
| H47 | 수익 외 품질 지표로 비교 | custom metrics/objective | MISSING | Evaluation | A |
| H48 | 진입했거나 안 한 이유를 되짚음 | decision trace / reason codes | PARTIAL diagnostics, decision trace MISSING | Diagnostics | S |
| H49 | 매매별로 어떤 gate가 막았는지 확인 | gate suppression diagnostics | PARTIAL | Diagnostics | S |
| H50 | 전략 변경 전후를 동일 조건으로 비교 | reproducible experiment identity | PARTIAL | Evaluation/Persistence | A |

---

## 4. 가장 먼저 강화할 6개 대영역

### S1. Trade Eligibility / Hard Guard

목표: **좋은 신호를 찾기 전에 나쁜 거래를 제거한다.**

필수 후보:

```text
minimum_turnover
minimum_depth
maximum_spread
VI_distance_guard
market_risk_guard
range/no-trade guard
session guard
max_daily_entries / max_daily_losses
```

권장 구조:

```text
Context/Equipment가 측정
-> DSL/Core가 명시적 gate로 소비
-> false면 entry order 생성 자체를 억제
-> diagnostics에 suppression reason 기록
```

주의: 값 계산 방법과 진입 금지 정책을 섞지 않는다.

### S2. Relative Context / Signal Quality

목표: 절대값보다 **현재 신호가 과거/시장/섹터/동시간대 대비 얼마나 강한가**를 표현한다.

필수 후보:

```text
percentile / zscore / normalized rank
benchmark-relative return/strength
sector-relative strength
previous-day context
same-time-of-day relative volume/turnover
setup quality score
```

단일 종목의 `RSI=70`보다 `최근 20일 동시간대 대비 거래대금 상위 5%` 같은 상대값이 중요하다.

### S3. Capital Flow / Microstructure

목표: 사람이 보는 **실제 참여 강도와 체결 가능성**을 전략 입력으로 만든다.

필수 후보:

```text
spread
bid/ask depth
depth imbalance
turnover acceleration
trade-count acceleration
buy/sell pressure
large-trade clustering
slippage estimate
```

이 영역은 DSL Core 함수보다 표준 Context Feature manifest와 provenance가 우선이다.

### S4. Stateful Setup Memory

목표: 같은 조건이 반복되어도 사람이 기억을 가지고 행동하는 것처럼 만든다.

현재 `edge`, `ready_after`, `hold`, `persist`, `latch`, `count`, `regime`, persistent state, `on_bar if/else`가 기반이다.

추가로 필요한 의미:

```text
setup identity
failed breakout state
same-zone entry count
post-stop cooldown
per-symbol daily state
trade outcome -> state transition
```

`on_fill`이 없으면 손절/체결 결과와 상태전이를 완전하게 연결하기 어렵다.

### S5. Selection / Ranking / Portfolio

목표: 사람처럼 **고르고 골라 들어가는 능력**을 만든다.

필수 후보:

```text
universe filter
score
rank
top-N
position sizing
multi-position
cash/equity/exposure
sector/portfolio caps
portfolio drawdown gate
```

이 영역이 없으면 DSL은 개별 종목에서 신호가 뜨는 대로 전부 매매하는 구조를 벗어나기 어렵다.

### S6. Execution Reality

목표: 좋은 전략 신호가 실제 주문에서도 돈이 되는지 확인한다.

현재 MARKET/LIMIT/STOP/STOP_LIMIT, OCO, DAY expiry 등은 기반이 있다.

남은 핵심:

```text
partial fills
partial exits
pyramiding
multi-position accounting
liquidity-aware fill
order-size market impact proxy
on_fill/on_order
```

---

## 5. 권장 전략 의사결정 계약 예시

새 문법 제안이 아니라 필요한 표현능력을 설명하기 위한 pseudo-DSL이다.

```text
universe
  -> tradable candidates

hard_gate
  turnover_ok
  spread_ok
  depth_ok
  vi_safe
  market_safe
  not_range

context
  market_strength
  sector_strength
  prev_day_structure
  relative_turnover
  flow_impulse

quality
  breakout_quality
  relative_strength
  flow_quality
  liquidity_quality

setup_state
  armed / triggered / failed / cooldown

trigger
  breakout && quality >= threshold

execution_preflight
  expected_slippage <= cap
  order_size <= depth_budget

position
  risk-sized quantity

portfolio
  symbol/sector/total exposure caps

order
  deterministic broker lifecycle

post_trade
  fill outcome -> state/cooldown/risk update
```

---

## 6. 경쟁 도구에서 가져올 설계 교훈

### TradingView Pine

- 다른 symbol/timeframe data request가 first-class 개념이다.
- confirmed/unconfirmed 및 repainting 위험을 명시적으로 다룬다.
- 우리 DSL은 MTF를 단순 함수 수가 아니라 Data Context 계약으로 확장해야 한다.

### QuantConnect LEAN

- Universe Selection -> Alpha -> Portfolio Construction -> Risk Management -> Execution으로 책임을 분리한다.
- signal은 direction만이 아니라 magnitude/confidence 개념을 가질 수 있다.
- portfolio target과 execution을 분리한다.
- 우리 DSL도 `signal=true`에서 바로 order로 가는 단일 경로를 넘어 selection/quality/risk/execution을 분리해야 한다.

### Backtrader / event-driven engines

- 전략 생명주기와 주문/체결 알림을 분리한다.
- 체결 결과는 상태 변화의 중요한 이벤트다.
- `on_fill/on_order`가 향후 stateful 전략에 중요하다.

### AmiBroker류 portfolio backtesting

- ranking, position sizing, scale in/out, portfolio-level evaluation이 신호 계산만큼 중요하다.
- 전략 수익화 단계에서는 개별 지표 함수보다 selection/allocation/accounting이 병목이 된다.

---

## 7. 현재 DSL의 강점과 실제 gap

### 이미 강한 부분

- fail-closed AST parser / semantic typing
- 함수 arity 및 boolean event 검증
- deterministic state primitives
- persistent state + nested `on_bar if/else`
- confirmed-only MTF 기반
- MARKET/LIMIT/STOP/STOP_LIMIT lifecycle
- OCO / DAY expiry / cancel semantics
- OHLC risk exits / next-open contract
- exact-time `ctx.*` parent-context binding
- Live Studio feature/invariant executable catalog

### 핵심 gap

현재 가장 큰 gap은 **지표 부족**이 아니라 다음이다.

```text
1. 매매대상 선택
2. 진입 허가/금지 계층
3. 시장/섹터/미시구조 표준 context
4. 상대강도/상대품질
5. 후보 ranking/top-N
6. 포지션/포트폴리오 자본배분
7. 부분체결/부분청산/피라미딩
8. 체결 이벤트와 setup memory 연결
9. decision trace
10. robust evaluation / walk-forward
```

---

## 8. 개발 우선순위 제안

### Wave H1 — Do-Not-Trade Intelligence

먼저 매매 횟수를 줄이고 질 낮은 진입을 막는다.

1. 표준 Eligibility/Guard contract 설계
2. range/no-trade equipment binding
3. turnover/liquidity/spread/VI context manifests
4. gate suppression reason diagnostics
5. daily entry/loss/cooldown state 강화

### Wave H2 — Relative Quality

1. percentile/zscore/normalized strength primitives
2. previous-day richer context
3. benchmark/sector multi-symbol context
4. same-time-of-day relative turnover
5. deterministic composite quality score

### Wave H3 — Selection / Capital

1. universe/filter
2. rank/top-N
3. position sizing
4. multi-position
5. exposure/portfolio risk caps

### Wave H4 — Execution / Stateful Reality

1. partial fills
2. partial exits / pyramiding
3. on_fill/on_order
4. liquidity-aware execution contract
5. setup outcome memory

### Wave H5 — Robust Strategy Research

1. parameter ranges
2. walk-forward
3. custom metrics
4. experiment identity / comparison
5. decision trace and attribution

---

## 9. 다음 audit에서 답해야 할 질문

각 capability에 대해 구현 전에 다음을 답한다.

1. 이 능력은 Core primitive인가, Context feature인가, Equipment guard인가?
2. 외부 데이터가 필요한가? 필요하면 provenance는 무엇인가?
3. hard gate인가 soft score인가?
4. batch/streaming에서 동일한가?
5. lookahead/repainting 위험이 있는가?
6. 실패 시 fail-closed인가?
7. 어떤 diagnostics/reason code를 남길 것인가?
8. Live Studio에서 어떻게 executable example로 검증할 것인가?
9. Chart에서 어떤 시각 증거로 확인할 것인가?
10. 기존 Core 축을 전략 특화 로직으로 오염시키지 않는가?

---

## 10. 결론

향후 DSL 고도화의 중심은 `더 많은 지표`가 아니다.

```text
좋은 신호 탐지
보다
나쁜 거래 제거
+ 상대적 품질 비교
+ 고르고 골라 선택
+ 실제 체결 가능성 확인
+ 자본/포트폴리오 위험 통제
+ 경험을 state로 기억
```

가 우선이다.

DSL은 사람이 순간적으로 수행하는 복합 판단을 불투명한 자율판단으로 흉내 내는 대신, **관측값·하드게이트·상대평가·상태·주문·위험을 명시적인 결정론적 계약으로 바꾸는 언어**가 되어야 한다.

이 capability map을 다음 DSL 확장 backlog의 상위 authority로 사용하되, 각 Wave는 별도 승인 후 micro-tranche로 구현한다.

## 참고

- DSL_ENGINE_AUDIT.md
- core/dsl_context.py
- TradingView Pine Script: other timeframes and data / execution model / strategies
- QuantConnect LEAN Algorithm Framework: Universe, Alpha, Portfolio Construction, Risk Management, Execution
- Backtrader strategy lifecycle
- AmiBroker portfolio / ranking / walk-forward concepts
