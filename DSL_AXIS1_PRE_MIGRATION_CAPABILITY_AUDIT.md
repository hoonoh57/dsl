# DSL AXIS 1 Pre-Migration Capability Audit

Status: **STEP 1 COMPLETE / AUTHORITATIVE PRE-MIGRATION CAPABILITY AUDIT / 2026-08-31 KST**

Purpose: frozen legacy `core/`의 현재 DSL 기능을 새 `axes/axis1_dsl/`로 이식하기 전에 실제 코드/테스트 기준으로 구현, 부분구현, 미구현을 확정한다.

Audit source:

```text
branch: dsl-live-studio
frozen core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

판정:

```text
IMPLEMENTED_AND_TRUSTED
IMPLEMENTED_NEEDS_VERIFICATION
PARTIAL
NOT_IMPLEMENTED
DEFERRED_BY_POLICY
```

---

## 1. 현재 신뢰된 기본 능력

다음은 기존 코드/테스트에서 확인된 기능이다.

```text
Parser / AST fail-closed                     IMPLEMENTED_AND_TRUSTED
scalar / series / bool / string type         IMPLEMENTED_AND_TRUSTED
arithmetic / comparison / AND OR NOT         IMPLEMENTED_AND_TRUSTED
history reference                            IMPLEMENTED_AND_TRUSTED
input scalar threshold                       IMPLEMENTED_AND_TRUSTED
persistent state + on_bar + nested if/else   IMPLEMENTED_AND_TRUSTED
confirmed-bar MTF                            IMPLEMENTED_AND_TRUSTED
registered read-only ctx.* binding           IMPLEMENTED_AND_TRUSTED within current contract
whole-fill Broker lifecycle                  IMPLEMENTED_AND_TRUSTED
session.day_return_pct                       IMPLEMENTED_AND_TRUSTED
user.macd_normalized                         IMPLEMENTED_AND_TRUSTED
JMA base numeric trend series                IMPLEMENTED_AND_TRUSTED
```

기존 Phase 1 checkpoint는 별도 authority에 기록된 상태를 유지한다.

---

## 2. Step 1 잔여 exact audit 최종 판정

### 2-1. JMA 값 / 상승·하락 상태의 전략 접근

**PARTIAL**

확인된 사실:

- `ta.jma(...)`는 정식 등록된 `series<number>`이며 전략식에서 직접 사용할 수 있다.
- JMA 계산 결과에는 내부적으로 `trend_colors`가 함께 보존되고 기존 테스트가 이를 확인한다.
- Backtest projection은 이 metadata를 사용해 JMA 선의 상승/하락 색상을 생성한다.
- 그러나 DSL 함수 Registry에는 `JMA direction`, `JMA up`, `JMA down`을 직접 반환하는 정식 capability가 없다.
- 일반 전략식에서 `jma > jma[1]`, `jma < jma[1]` 같은 조합은 가능하지만, 이는 내부 `trend_colors`의 동일값 유지 semantics까지 포함한 정식 direction output과 동일 계약이라고 간주하지 않는다.

따라서:

```text
JMA numeric line direct access       YES
JMA chart direction metadata         YES
JMA direction as registered DSL data NO
```

새 AXIS 1에서는 multi-output 또는 일반 direction output 계약과 함께 정리한다.

### 2-2. JMA normalized slope strength 직접 접근

**NOT_IMPLEMENTED as canonical measurement**

현재 등록 함수는 `ta.jma` 하나이며 JMA normalized slope strength 전용 함수/출력은 없다.

DSL 산술과 history reference를 이용해 사용자가 임의의 1-bar 정규화 기울기 식을 만들 수는 있다. 그러나 그것을 현재 제품에서 의도하는 **공식 JMA normalized slope strength**와 동일하다고 간주할 근거와 단일 수식 authority가 없다.

따라서 이 항목은 문법 부족이 아니라 **측정값 contract 부족**으로 판정한다.

새 AXIS 1에서 수식/단위/NaN/warmup/direction semantics를 확정한 뒤 additive capability 또는 multi-output component로 구현한다.

### 2-3. 중간값 / threshold / permission / marker 차트 projection

**PARTIAL**

현재 Backtest는 전략의 numeric ndarray 중간값을 자동 수집해 `indicators`로 반환한다. JMA처럼 direction metadata를 가진 numeric series는 색상 정보도 함께 전달한다. 거래 체결 marker도 반환한다.

그러나 일반 projection 계약으로는 부족하다.

현재 부족한 점:

```text
numeric intermediate series     가능
JMA direction-colored series    가능
trade markers                    가능
scalar input threshold line      일반 자동 projection 없음
boolean permission series        chart projection 없음
ALLOW/BLOCK 같은 generic marker 일반 계약 없음
non-overlay indicator pane       현재 renderer가 overlay=true만 그림
projection role/type metadata    없음
```

따라서 향후 일반 계약은 최소 다음을 구분해야 한다.

```text
indicator series
intermediate series
threshold/reference series
permission/condition series
markers/events
pane/overlay intent
```

Chart가 값을 다시 계산해서 보완하는 것은 금지한다.

### 2-4. Strategy CRUD와 Feature Catalog 분리

**PARTIAL relative to final three-axis target**

현재 Feature Catalog는 `core/dsl_feature_catalog.py`의 실행 가능한 frozen verification cases로 관리되고 Strategy CRUD 데이터와 별개다.

현재 전략/결과물 persistence는 `strategies.db`와 `core/db.py`에서 관리한다. 따라서 **Feature Catalog와 전략 저장소가 같은 저장소를 공유하는 구조는 아니다.**

다만 현재 `strategies` 테이블은 `strategy`, `indicator`, `signal`, `strength`, `drawing` 등 여러 artifact type을 함께 수용하며, 새 최종 구조의:

```text
Condition CRUD
Strategy CRUD
Feature Catalog
```

세 경계가 물리적으로 완성된 상태는 아니다.

또한 현재 persistence 구현은 frozen legacy `core/db.py`에 있으므로 새 `axes/axis3_monetization/`로 아직 이식되지 않았다.

판정:

```text
Feature Catalog vs mutable artifact persistence separation  YES
final AXIS 3 Strategy CRUD physical separation              NO
Condition CRUD independent persistence                       NO
```

---

## 3. 기존 8개 strategy-composition audit 최종표

```text
1. normalized Histogram direct strategy access       IMPLEMENTED_AND_TRUSTED
2. JMA up/down/normalized slope direct access         PARTIAL / normalized slope NOT_IMPLEMENTED
3. session.day_return_pct direct access               IMPLEMENTED_AND_TRUSTED
4. arithmetic / comparison                            IMPLEMENTED_AND_TRUSTED
5. AND / OR / NOT                                     IMPLEMENTED_AND_TRUSTED
6. strategy parameter/input threshold                 IMPLEMENTED_AND_TRUSTED
7. intermediate + threshold chart projection          PARTIAL
8. Strategy CRUD vs Feature Catalog separation         PARTIAL relative to final target
```

이 결과로 인해 frozen `core/`를 보완하지 않는다. 부족한 기능은 새 구조 이식 후 각 권한 축에서 개발한다.

---

## 4. 확정된 AXIS 1 주요 gap

### G1. Tuple / multi-output typed return + destructuring

**NOT_IMPLEMENTED — TOP PRIORITY AFTER MIGRATION PARITY**

현재 assignment target은 단일 identifier이며 Registry/Semantic에 tuple/product type이 없다.

Python 내부에서는 예를 들어:

```text
CoreTALib.supertrend() -> line + direction
CoreTALib.bbands()     -> upper + mid + lower
```

를 만들 수 있으나 DSL에는 일반 multi-output contract가 없다.

목표:

```text
indicator -> typed multi-output
assignment/destructuring
semantic arity/type validation
runtime deterministic materialization
selected output projection
```

### G2. User-defined functions

**NOT_IMPLEMENTED**

함수 선언, parameter/local scope, return AST/runtime contract가 없다.

### G3. Bounded loops

**NOT_IMPLEMENTED**

DSL 수준 bounded loop가 없다.

### G4. on_tick / on_fill + rollback/commit model

**NOT_IMPLEMENTED**

open-bar provisional state, rollback, confirmed commit, fill-triggered recalculation과 deterministic event ordering이 없다.

### G5. Partial fills / partial exits

**NOT_IMPLEMENTED**

`PARTIALLY_FILLED`, cumulative/remaining quantity, multi-fill ledger와 부분청산 accounting이 없다.

### G6. Pyramiding / multi-position accounting

**NOT_IMPLEMENTED**

현재 Backtest는 단일 position slot을 사용하며 occupied 상태에서 추가 entry를 차단한다.

### G7. Full TA-Lib/reference differential fixtures

**NOT_IMPLEMENTED as full suite**

일부 지표 정합성 검증은 있으나 전체 등록 지표에 대한 versioned differential fixture suite는 없다.

### G8. Capability metadata completeness

**PARTIAL**

현재 Registry는 name/arity/returns/signature/category 중심이다. output names, lookback, warmup, NaN policy, incremental identity, reference source, causality metadata가 부족하다.

### G9. Full-engine batch/streaming parity

**PARTIAL**

일부 상태/MTF parity는 있으나 전체 indicator/state/order lifecycle을 한 계약으로 덮지 않는다.

### G10. Generic projection contract

**PARTIAL**

Step 1 exact audit 결과 numeric series와 거래 marker는 존재하지만 threshold/permission/non-overlay/pane metadata를 포함한 일반 projection은 미완성이다.

---

## 5. AXIS 2와 혼동하지 않을 항목

다음은 AXIS 1 gap이 아니다.

```text
market regime calculation
high-beta universe construction
sector strength ranking
cross-symbol normalized Histogram ranking
leader/follower universe selection
top-N candidate selection
```

이들은 사전 계산된 point-in-time snapshot을 사용하는 AXIS 2 책임이다.

---

## 6. Migration acceptance

새 AXIS 1은 기존 trusted behavior를 먼저 재현해야 한다.

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

차이가 나면 먼저 원인을 분류하고 assertion이나 compatibility exception으로 숨기지 않는다.

---

## 7. Step 1 결론

Step 1의 잔여 audit는 완료됐다.

핵심 결론:

```text
JMA base value는 사용 가능하지만 direction/normalized slope의 정식 DSL output은 부족하다.
projection은 numeric series 중심으로 존재하지만 threshold/permission까지 일반화되지 않았다.
Feature Catalog와 mutable strategy/artifact 저장은 분리되어 있으나 최종 AXIS 3 CRUD 경계는 미완성이다.
```

다음 작업은 **AXIS 1 migration manifest와 boundary 이식 순서를 확정하는 것**이다.

Broader repository status는 계속 `REMEDIATION_REQUIRED`다.
