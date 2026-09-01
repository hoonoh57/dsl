# DSL Three-Axis Final Target

Status: **FINAL PRODUCT ARCHITECTURE AUTHORITY / ACTIVE / 2026-09-01 KST**

최종 제품은 세 축을 하나의 Core로 섞지 않고, 각 축의 책임을 독립적으로 유지한 채 versioned Bridge로 연결한다.

## 최종 실행 흐름

```text
precomputed market/context evidence
 -> AXIS 2 exact-PIT selection
 -> Candidate Set + evidence
 -> AXIS 3 promoted Condition/Strategy versions + deterministic run plan
 -> versioned Bridge
 -> AXIS 1 deterministic single-instrument execution
 -> result / diagnostics / projections
```

Chart는 위 결과를 표시하는 계측기이며 계산 권한을 가지지 않는다.

---

## AXIS 1 — DSL Capability / Execution

위치:

```text
axes/axis1_dsl/
```

책임:

```text
DSL Parser / Semantic
indicator kernel
state / bar / intrabar runtime
MTF / exact read-only context binding
order / broker / execution accounting
backtest
projection output
machine-readable capability/diagnostic registry
```

AXIS 1은 한 종목의 이미 주어진 입력을 결정론적으로 표현·실행한다.

금지:

```text
universe discovery
cross-symbol rank
sector/leader/follower selection
Condition/Strategy lifecycle DB 조회
provider/network lookup
특정 종목/전략 shortcut
```

상위 정보가 필요하면 외부에서 준비된 exact read-only context로 명시적으로 전달한다.

---

## AXIS 2 — Exact-PIT Selection

위치:

```text
axes/axis2_selection/
```

책임:

```text
immutable point-in-time snapshot contract
precomputed feature evidence consumption
filter
rank
top-N
Candidate Set
candidate evidence/reasons
```

예:

```text
market regime
beta/high-beta universe membership
sector strength / leader-follower evidence
EMA120 event evidence
normalized MACD Histogram strength/rank
relative strength
turnover / capital-flow
```

AXIS 2는 주문을 만들거나 DSL 전략을 실행하지 않는다.

### Condition 책임 분리

Condition의 **선별 의미**는 AXIS 2가 정의한다.

```text
selection spec
feature identities
filter/rank/top-N semantics
snapshot/evidence requirements
```

그러나 Condition의 저장·버전·계보·승격 lifecycle은 AXIS 3가 소유한다.

---

## AXIS 3 — Versioned Condition/Strategy Lifecycle + Orchestration

위치:

```text
axes/axis3_monetization/
```

책임:

```text
Condition immutable version CRUD/lifecycle
Strategy immutable version CRUD/lifecycle
lineage
promotion/rejection/archive
exact artifact hash/version binding
Candidate Set -> StrategyRunPlan orchestration
```

AXIS 3는 AXIS 2의 selection 의미를 재계산하지 않고, AXIS 1 Parser/Runtime/Backtest를 자체 구현하지 않는다.

```text
Condition artifact = approved/research AXIS 2 selection spec의 immutable version
Strategy artifact  = DSL + settings + condition refs의 immutable version
RunPlan            = exact promoted artifacts + CandidateSet identity + candidate intents
```

실제 AXIS 1 호출은 Bridge가 수행한다.

---

## Bridge

위치:

```text
bridges/contracts/
bridges/axis1_execution_bridge.py
bridges/three_axis_e2e_bridge.py
```

규칙:

```text
contracts = data-only
axis internal object 노출 금지
cross-axis internal state 직접 참조 금지
Request -> Response version 고정
opaque/nonfinite/unknown field fail-closed
exact hash/version/as_of binding
```

세 축의 내부 구현을 동시에 import해 조합할 수 있는 곳은 명시적인 Bridge adapter/routing 계층뿐이다.

---

## External LLM Authoring

External LLM은 전략 초안을 제안할 뿐이다.

```text
natural language
 -> generated current manifest prompt
 -> untrusted structured draft
 -> local deterministic validation
 -> accepted draft / correction / blocked
```

`ACCEPTED_DRAFT`는 저장·승격·백테스트·주문 권한을 의미하지 않는다.

---

## Continuous Improvement

반복 검증 실패는 구조화 evidence로 집계한다.

```text
validation events
 -> deterministic metrics/patterns
 -> evidence-gated remediation recommendation
 -> human review
```

자동 Prompt rewrite, capability 등록, Parser/Runtime 변경은 금지한다.

---

## Chart

Chart는 계산하지 않는다.

표시 대상:

```text
selector evidence
indicator/intermediate series
threshold / permission series
BUY/SELL markers
execution/trade diagnostics
```

계산값의 재생성, selection 재평가, strategy execution은 Chart 권한이 아니다.

---

## Feature Catalog와 product artifacts

```text
machine-readable capability registry
= DSL 지원/검증 상태 SSOT

Condition artifact
= AXIS 2 selection spec의 AXIS 3 versioned lifecycle copy

Strategy artifact
= AXIS 3 versioned DSL strategy
```

과거 정적 Feature Catalog 문서의 수치나 예제는 current support SSOT가 아니다.

---

## Frozen legacy Core

repository-root `core/`는 immutable reference다.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen tree         = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

신규 기능 개발은 `axes/axis1_dsl/`에서만 수행한다.

---

## 최종 수용 원칙

```text
same exact inputs -> same deterministic outputs/hashes
future value 금지
nearest-time/fill-forward/interpolation 금지
missing default synthesis 금지
axis authority 혼합 금지
specific-strategy Core shortcut 금지
External LLM execution authority 금지
continuous-improvement automatic mutation 금지
frozen core 변경 금지
```
