# DSL H1 Do-Not-Trade Intelligence Audit

작성일: 2026-08-31
상태: DESIGN/AUDIT BASELINE — 구현 승인 아님

## 1. 목적

Human Trading Decision Capability Map의 H1을 실제 repo 구현과 대조한다.

H1의 목표는 신호를 더 많이 만드는 것이 아니라 **사람이라면 애초에 거래하지 않을 구간/종목/시각에서 주문 생성을 차단하는 능력**을 갖추는 것이다.

대상은 다음 네 묶음이다.

1. 횡보/비추세 구간 회피
2. 유동성/호가 품질
3. VI·가격제한·시장제도 guard
4. 반복진입 억제/cooldown/setup memory

---

## 2. 현재 Core에서 이미 확인된 기반

### 2.1 외부 Hard Gate 입구 — IMPLEMENTED

`BacktestEngine.run(..., entry_gate=...)`가 이미 존재한다.

- bar 수와 같은 길이의 boolean gate를 받는다.
- false이면 `higher_layer_gate_blocked`로 진입을 차단한다.
- gate는 신호 계산 자체를 바꾸지 않고 주문 진입 정책 앞에서 동작한다.

따라서 H1의 핵심 구조는 새 DSL 문법을 먼저 만드는 것보다 다음 경계를 활용하는 것이 적합하다.

```text
Context / Equipment
  -> deterministic measurements
  -> hard-gate decision
  -> BacktestEngine.entry_gate
  -> order suppressed before entry
```

이 구조는 Core에 횡보/VI/호가 의미를 직접 집어넣지 않고도 절대 진입금지를 적용할 수 있다.

### 2.2 시간대/일일 진입횟수 guard — IMPLEMENTED

`StrategySettings`에 다음이 이미 존재한다.

```text
entry_start_time
entry_end_time
max_entries_per_day
```

BacktestEngine은 진입 직전 이를 검사하고 각각 다음 rejection reason을 기록한다.

```text
entry_time_blocked
entry_count_blocked
```

즉 장초/마감 회피와 하루 과매매 제한의 최소 기반은 이미 있다.

### 2.3 상태/반복 억제 primitive — IMPLEMENTED/PARTIAL

Function Registry에 다음 상태 함수가 존재한다.

```text
state.edge
state.falling_edge
state.ready_after
state.hold
state.persist
state.latch
state.count
state.regime
```

또 일반 persistent `state` + `on_bar if/else`가 1차 범위에 구현되어 있다.

따라서 단순한 재진입 지연, 상태 latch, regime 전이는 표현 가능하다.

다만 손절/부분체결/실제 체결결과를 상태로 연결하는 `on_fill/on_order`가 아직 없으므로 **trade-outcome 기반 cooldown/setup memory는 미완성**이다.

### 2.4 횡보 판별에 쓸 수 있는 primitive — PARTIAL

현재 TA 함수 중 다음은 range/trend quality의 재료가 될 수 있다.

```text
ta.vhf
ta.nrange
ta.abs_range
ta.sum_abs_r
ta.adx
ta.atr
ta.stdev
state.regime
```

그러나 `NO_TRADE_RANGE`라는 표준 장비/계약은 없다.

즉 **측정 primitive는 일부 있으나 권위 있는 횡보 진입금지 장비는 미구현**이다.

### 2.5 외부 Context 주입 경계 — CONTEXT_READY

`ctx.*`는 등록된 manifest, exact-time binding, deployment-only 조건으로 외부 feature를 fail-closed 주입할 기반이 있다.

따라서 다음 값들은 Core TA 함수로 만들 필요가 없다.

```text
spread
depth
depth imbalance
VI state
distance to VI
turnover
market risk state
exchange status
```

단, 현재 H1 표준 feature manifest/provider가 준비된 것은 아니다.

---

## 3. H1 상세 Gap Matrix

| ID | Capability | 현재 판정 | 현재 기반 | 부족한 것 | 권장 축 |
|---|---|---|---|---|---|
| H1-01 | 횡보구간 진입금지 | PARTIAL | VHF/nrange/ADX/state.regime + entry_gate | 표준 range detector/equipment, 절대 기준선, provenance | Equipment + Context |
| H1-02 | 횡보 탈출 확인 후 허가 | PARTIAL | edge/ready_after/latch/state | breakout-from-range identity와 re-arm 계약 | Core state + Equipment |
| H1-03 | 동일 횡보구간 반복매매 억제 | PARTIAL | state.count/persistent state | zone/setup identity | Core state |
| H1-04 | 손절 후 cooldown | PARTIAL/MISSING | on_bar state 가능 | fill/outcome event 연결 | Core event runtime |
| H1-05 | 하루 최대 진입횟수 | IMPLEMENTED | max_entries_per_day | DSL/장비에서 표준 정책 노출 방식 | Core settings |
| H1-06 | 특정 시간대 진입금지 | IMPLEMENTED | entry_start_time/end_time | 다중 session window/요일/경매구간 | Core settings/session |
| H1-07 | 최소 거래대금 | CONTEXT_READY/MISSING STANDARD | ctx.* | 표준 turnover feature + threshold equipment | Context + Equipment |
| H1-08 | 최대 spread | CONTEXT_READY/MISSING STANDARD | ctx.* | bid/ask feed, normalized spread feature | Context + Equipment |
| H1-09 | 최소 호가 depth | CONTEXT_READY/MISSING STANDARD | ctx.* | orderbook depth feed/feature | Context + Equipment |
| H1-10 | 주문수량 대비 depth | MISSING | 향후 context 가능 | order size preflight + broker/context contract | Broker + Context |
| H1-11 | VI 근접 진입금지 | CONTEXT_READY/MISSING STANDARD | ctx.* + entry_gate | VI reference/provider, distance feature, threshold | Context + Equipment |
| H1-12 | VI 발동/해제 상태 | CONTEXT_READY/MISSING STANDARD | ctx.* | exchange event state feature | Context + Equipment |
| H1-13 | 상·하한가/가격제한 근접 | CONTEXT_READY/MISSING | ctx.* | price-limit reference + distance feature | Context + Equipment |
| H1-14 | 거래정지/시장상태 차단 | PARTIAL/MISSING | data validation + ctx.* 가능 | exchange status/session state standard | Data Context + Equipment |
| H1-15 | 시장 risk-off 절대금지 | CONTEXT_READY/MISSING STANDARD | ctx.* + entry_gate | market regime provider/manifest | Context + Equipment |
| H1-16 | 차단 이유 기록 | PARTIAL | generic rejection_counts | named gate별 reason/provenance | Diagnostics/Bridge |

---

## 4. 핵심 설계 결론

### 4.1 H1은 DSL 함수팩이 아니라 “Permission Layer”다

다음 구조를 기준으로 한다.

```text
Signal layer
  entry_cond = ...

Permission layer
  range_ok
  liquidity_ok
  vi_ok
  session_ok
  market_ok

Final entry permission
  signal AND all hard gates
```

단, 각 장비의 측정/판별 의미를 DSL expression에 중복 구현하지 않는다.

### 4.2 첫 구현 대상은 횡보 장비가 적합하다

이유:

- 현재 OHLCV만으로 구현·검증 가능하다.
- 외부 호가/VI feed가 없어도 개발 가능하다.
- 사용자가 문제로 지적한 “횡보장에서 수없이 사고파는 현상”을 직접 줄인다.
- `entry_gate` 경계가 이미 있어 Core 오염 없이 붙일 수 있다.

첫 장비의 목표 형태:

```text
Range Detector Equipment
  input: trusted chart/market bars
  output per bar:
    range_score
    trade_permitted: bool
    reason_code
    detector_version
    threshold/version provenance
```

초기 detector는 하나의 학습모델이 아니라 합의된 결정론적 지표 조합으로 시작한다.

후보 재료:

```text
VHF
ADX
normalized range
slope/JMS2 absolute threshold
volatility compression
```

어떤 조합을 표준으로 채택할지는 별도 fixture/differential 검증 후 결정한다.

### 4.3 호가/VI는 두 번째 구현군이다

호가/VI는 값 자체보다 **데이터 source와 시간 정합성**이 먼저다.

필요 순서:

```text
trusted provider
-> normalized context feature
-> manifest/provenance
-> exact-time ctx binding
-> hard guard equipment
-> entry_gate
```

가짜/추정 호가나 VI 값을 Core에서 계산하지 않는다.

### 4.4 단일 bool gate만으로는 장기적으로 진단이 부족하다

현재 `entry_gate`는 실행 차단에는 충분하지만 여러 장비 중 무엇이 막았는지 알 수 없다.

향후에는 실행 의미를 바꾸지 않는 진단 sidecar가 필요하다.

예:

```text
gate result:
  permitted: false
  reasons:
    - RANGE_BLOCKED
    - SPREAD_TOO_WIDE
  evidence:
    range_score: ...
    spread_pct: ...
```

Core의 주문 차단 입력은 여전히 최종 boolean으로 유지할 수 있다. 세부 evidence는 Diagnostics/Context 쪽에 둔다.

---

## 5. 개발 순서 제안

### H1-A — Range/No-Trade Equipment

1. range detector contract 정의
2. 기존 VHF/nrange/ADX/JMS2 후보의 고정 fixture 비교
3. 절대 기준선 기반 trade_permitted 출력
4. `entry_gate` 연결
5. 횡보 fixture에서 crossover 반복매매 감소 invariant
6. 추세 fixture에서 정상 진입을 과도하게 막지 않는 invariant
7. chart에 range-score/blocked zone은 시각화만 함

### H1-B — Named Gate Diagnostics

1. gate reason schema
2. blocked-bar count/reasons
3. chart에서 “왜 진입하지 않았는지” 표시
4. 전략 결과와 gate 결과의 reproducibility hash

### H1-C — Liquidity Context

1. turnover 표준 feature
2. spread 표준 feature
3. depth 표준 feature
4. exact-time binding
5. threshold equipment

### H1-D — VI/Exchange Guard

1. VI state/distance provider contract
2. price-limit/exchange-state context
3. hard gate
4. historical replay fixture

### H1-E — Outcome-aware Re-entry Control

1. on_fill/on_order 기반 마련
2. stop outcome -> cooldown state
3. setup/zone identity
4. same-zone max-entry invariant

---

## 6. 현재 판단

H1 전체를 새로 만들어야 하는 상태는 아니다.

이미 있는 강한 기반:

```text
entry_gate
state primitives
persistent on_bar state
entry time guard
max entries/day
exact-time ctx.* binding
confirmed MTF
```

실제 부족한 핵심은 다음이다.

```text
1. 권위 있는 range/no-trade detector
2. 표준 liquidity/VI context feature
3. named gate diagnostics
4. setup identity
5. fill/outcome 기반 memory
```

따라서 첫 개발 tranche는 **H1-A Range/No-Trade Equipment**가 가장 작은 변경으로 가장 큰 실전 차이를 검증할 수 있다.
