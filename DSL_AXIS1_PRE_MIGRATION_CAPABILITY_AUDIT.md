# DSL AXIS 1 Pre-Migration Capability Audit

Status: **AUTHORITATIVE PRE-MIGRATION CAPABILITY AUDIT / 2026-08-31 KST**

Purpose: frozen legacy `core/`의 현재 DSL 기능을 새 `axes/axis1_dsl/`로 이식하기 전에 실제 코드 기준으로 구현/부분구현/미구현을 확정하고, 이식 검증 직후 계속 개발할 AXIS 1 backlog를 고정한다.

Audit source checkpoint:

```text
branch: dsl-live-studio
commit: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

판정:

```text
IMPLEMENTED_AND_TRUSTED
IMPLEMENTED_NEEDS_VERIFICATION
PARTIAL
NOT_IMPLEMENTED
DEFERRED_BY_POLICY
```

## 1. Current trusted/implemented surface

### Parser / AST fail-closed

**IMPLEMENTED_AND_TRUSTED**

현재 parser는 single-name assignment, input, state, `on(condition)` order block, `on_bar`, nested `if/else`, `set`을 명시적으로 AST로 만들며 미인식 문장을 오류 처리한다.

### Scalar/series type system

**IMPLEMENTED_AND_TRUSTED**

현재 semantic type:

```text
scalar<number>
scalar<bool>
string
series<number>
series<bool>
series<string>
```

산술/비교/AND/OR/NOT, history reference, registered function arity/type 검사가 존재한다.

### Persistent state + on_bar

**IMPLEMENTED_AND_TRUSTED**

persistent `state`, causal one-bar-at-a-time `on_bar`, nested `if/else`가 존재한다.

### MTF confirmed-bar reads

**IMPLEMENTED_AND_TRUSTED**

완료된 higher-timeframe bar만 사용하는 non-repainting MTF path가 존재한다.

### Registered parent-context read binding

**IMPLEMENTED_AND_TRUSTED within narrow v1 contract**

`ctx.<layer>.<feature>` read-only binding이 존재한다. 시장레짐/섹터/peer ranking 계산 자체는 DSL 책임이 아니며 외부에서 사전 계산·동결된 값만 소비한다.

### Current order lifecycle

**IMPLEMENTED_AND_TRUSTED for whole-fill model**

```text
CREATED
ACCEPTED
TRIGGERED
FILLED
CANCELED
REJECTED
EXPIRED
```

MARKET/LIMIT/STOP/STOP_LIMIT, GTC/DAY, OCO, cancel path가 존재한다.

---

## 2. Confirmed AXIS 1 gaps

### G1. Tuple / multi-output typed return + destructuring

**NOT_IMPLEMENTED — TOP PRIORITY AFTER MIGRATION PARITY**

현재 assignment target은 하나의 identifier이고 Semantic `ValueType`/Registry `returns`에도 tuple/product type이 없다.

중요한 현재 상태:

```text
CoreTALib.supertrend() -> Python 내부에서 line + direction 반환 가능
CoreTALib.bbands()     -> Python 내부에서 upper + mid + lower 반환 가능
```

하지만 DSL surface에서는 multi-output contract가 없다.

현재는 다음과 같이 우회한다.

```text
ta.supertrend(...)
ta.supertrend_direction(...)
user.macd_normalized(..., component)
```

목표 일반 계약:

```text
indicator -> typed multi-output value
[a, b, c] = indicator(...)
semantic -> output arity/type validation
runtime -> deterministic materialization
projection -> selected outputs without chart-side recomputation
```

MACD/BBANDS/Supertrend 등에서 공통으로 사용할 수 있는 일반 기능이어야 하며 특정 지표 전용 예외 문법으로 만들지 않는다.

### G2. User-defined functions

**NOT_IMPLEMENTED**

현재 `function/def`, parameter/local scope/return AST와 semantic/runtime contract가 없다. 함수 호출은 registry에 사전 등록된 함수만 허용한다.

### G3. Bounded loops

**NOT_IMPLEMENTED**

DSL에 bounded `for`/iterator/range loop가 없다. Python indicator 구현 내부 loop는 DSL 표현 기능이 아니다.

### G4. on_tick / on_fill + rollback/commit execution model

**NOT_IMPLEMENTED**

현재 다음 계약이 없다.

```text
open-bar tick update
provisional state
last-confirmed snapshot
rollback/recalculate
commit on confirmed bar
fill-triggered recalculation
same-tick/same-bar deterministic event ordering
```

단순 callback 추가가 아니라 Runtime state authority와 Broker event sequencing을 먼저 정의해야 한다.

### G5. Partial fills / partial exits

**NOT_IMPLEMENTED**

현재 `BrokerOrder`에는 `PARTIALLY_FILLED` 상태, cumulative filled quantity, remaining quantity, multi-fill ledger가 없다. accepted/triggered order는 한 번의 `fill()`로 terminal `FILLED`가 된다.

부분 청산용 position-lot/remaining-quantity accounting도 없다.

### G6. Pyramiding / multi-position accounting

**NOT_IMPLEMENTED**

현재 Backtest는 단일 슬롯을 사용한다.

```text
position
quantity
entry_price
entry_fee
open_trade
```

position이 존재하면 `position_occupied` 경로로 추가 entry를 차단한다.

따라서 다음은 없다.

```text
same-direction scale-in
multiple entry lots
independent cost basis
multiple open position ledger
per-lot partial exit
```

### G7. Full TA-Lib/reference differential fixture suite

**NOT_IMPLEMENTED as full suite**

Wilder RMA 기반 ATR/RSI/ADX 등 특정 reference alignment 교정은 존재하지만 전체 registered indicator catalog에 대한 fixed-data differential fixture suite는 없다.

목표:

```text
fixed datasets
reference outputs
declared tolerance
NaN/warmup policy
versioned expected evidence
```

### G8. Capability metadata completeness

**PARTIAL**

현재 registry metadata:

```text
name
minimum/maximum arity
returns
signature
category
```

향후 일반화가 필요한 metadata:

```text
output names / output arity
lookback / minimum period
warmup / NaN policy
batch implementation identity
incremental implementation identity
reference implementation/source
causality / repaint classification
```

### G9. Full-engine batch/streaming parity

**PARTIAL**

일부 state/MTF path에는 parity 검증이 있으나 모든 registered indicator + state + order + future tick/fill lifecycle을 하나의 parity contract로 덮는 수준은 아니다.

### G10. Generic projection / visual output contract

**PARTIAL / NEEDS VERIFICATION**

현재 intermediate series/markers/chart bridge 경로가 존재하지만 향후 tuple output, thresholds, selection/context evidence까지 모두 같은 generic projection contract로 전달되는지 별도 audit가 필요하다.

Chart가 계산을 재구현하는 방식으로 보완하면 안 된다.

---

## 3. Existing strategy-composition audit items

이전 세션에서 정한 다음 항목도 migration 전에 실제 코드/테스트로 다시 판정한다.

```text
1. normalized Histogram direct strategy access
2. JMA up/down/normalized slope direct access
3. session.day_return_pct direct access
4. arithmetic / comparison
5. AND / OR / NOT
6. strategy parameter/input threshold
7. intermediate value + threshold chart projection
8. Strategy CRUD와 Feature Catalog 분리
```

현재 확인:

```text
session.day_return_pct       implemented
arithmetic/comparison        implemented
AND/OR/NOT                   implemented
input scalar threshold       implemented at language level
user.macd_normalized         implemented as single-output component function
JMA base trend series        implemented
JMA normalized slope output  needs exact audit
projection completeness      needs exact audit
Strategy CRUD separation     needs exact audit
```

JMA 관련해서는 `TrendArray.trend_colors` 같은 Python/chart-side metadata 존재 여부와 DSL에서 직접 읽을 수 있는 정식 registered series는 구분해서 판정한다.

---

## 4. AXIS 1 migration/development order

```text
A0 freeze legacy core/ tree
A1 exact current capability audit completion
A2 create new axes/axis1_dsl physical root
A3 migrate one boundary at a time
A4 frozen core vs AXIS 1 parity tests
A5 AXIS 1 trusted migration checkpoint
A6 tuple/multi-output typed return
A7 capability metadata expansion needed by multi-output
A8 user-defined functions
A9 bounded loops
A10 partial-fill/position-ledger design
A11 partial fill / partial exit
A12 pyramiding / multi-position
A13 on_tick/on_fill rollback model
A14 full differential fixture suite
A15 full batch/streaming parity
```

실제 구현은 dependency와 risk에 따라 micro-tranche 순서를 조정할 수 있으나, 3축 이전을 이유로 위 DSL 기능을 장기간 보류하지 않는다.

특히 **tuple/multi-output은 migration parity 직후 최우선 구현 기능**으로 고정한다.

---

## 5. Separation from AXIS 2

다음은 AXIS 1 gap이 아니다.

```text
market regime calculation
high-beta universe construction
sector strength ranking
cross-symbol normalized Histogram ranking
leader/follower universe selection
top-N candidate selection
```

이들은 `DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md`에 따라 Instrument DSL 밖에서 사전 계산·동결된 point-in-time feature snapshot을 사용한다.

AXIS 1은 필요한 값만 read-only context/input으로 소비할 수 있다.

---

## 6. Migration acceptance rule

새 AXIS 1은 기존 trusted behavior parity를 통과해야 한다.

```text
Parser fail-closed parity
Semantic type/error parity
registered feature baseline parity
registered execution invariant parity
Runtime deterministic output parity
Backtest/Broker trade-result parity
MTF/context causal parity
existing additive indicator parity
chart projection parity for unchanged features
```

차이가 나면 먼저 다음으로 분류한다.

```text
migration defect
legacy defect discovered during migration
test defect
authority drift
environment issue
unknown
```

assertion 약화나 compatibility exception으로 녹색을 만들지 않는다.

Broader repository compliance 상태는 별개이며 현재 `REMEDIATION_REQUIRED`를 유지한다.
