# DSL AXIS 1 Migration Manifest

Status: **STEP 2 ACTIVE / MIGRATION PLAN AUTHORITY / 2026-08-31 KST**

목적: frozen legacy `core/`에서 **DSL Capability Engine에 실제로 필요한 코드만** 새 `axes/axis1_dsl/`로 경계 단위 이식한다. 과거 `core/`에 함께 존재하던 selection/research/strategy persistence/provider/UI 성격 코드를 AXIS 1에 다시 섞지 않는다.

중요:

```text
이 문서는 이식 설계도다.
아직 실제 이식 코드를 쓰지 않는다.
Step 3 frozen-core 보호 gate PASS 이후에만 Step 4 실제 이식을 시작한다.
```

Frozen source:

```text
legacy path: core/
frozen tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

Target root:

```text
axes/axis1_dsl/
  core/
  indicators/
  runtime/
  execution/
  tests/
```

---

## 1. Migration 원칙

```text
1. 전체 core/ 복사 금지
2. 한 boundary씩 이식
3. 기능 추가와 migration을 섞지 않음
4. 내부 import만 새 AXIS 1 package 경로로 변경 가능
5. 의도적 기능 변경은 Step 5 이후
6. 각 boundary는 frozen legacy와 focused parity를 먼저 통과
7. 새 AXIS 1 production code가 frozen core/를 import하는 상태로 완료 처리 금지
8. selection / monetization / provider / authoring 책임을 AXIS 1에 재유입 금지
```

---

## 2. 최종 이식 경계 순서

### Boundary 1 — Parser / AST

Source:

```text
core/dsl_parser.py
```

Target:

```text
axes/axis1_dsl/core/dsl_parser.py
```

방식:

```text
COPY_AS_IS_BEHAVIOR
package 위치만 변경
기능 추가/문법 변경 금지
```

의존성:

```text
stdlib only
```

Parity:

```text
동일 DSL corpus parse success/failure
strategy name/timeframe 동일
AST node 구조/필드 동일
미인식 문법 fail-closed 동일
error line/column/code 동일
```

**첫 실제 migration boundary로 확정한다.**

이유: 다른 프로젝트 내부 모듈에 의존하지 않아 가장 작은 독립 경계이며, 이후 모든 language/runtime 계층의 기반이다.

---

### Boundary 2 — Function Registry

Source:

```text
core/function_registry.py
```

Target:

```text
axes/axis1_dsl/core/function_registry.py
```

방식:

```text
COPY_AS_IS_BEHAVIOR
```

Parity:

```text
등록 함수 identity 집합 동일
arity / return type / signature / category 동일
```

주의: metadata 확장은 migration 중 하지 않고 Step 5~6에서 수행한다.

---

### Boundary 3 — Assignment Flow + Semantic

Source:

```text
core/assignment_flow.py
core/dsl_semantic.py
```

Target:

```text
axes/axis1_dsl/core/assignment_flow.py
axes/axis1_dsl/core/dsl_semantic.py
```

방식:

```text
COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
```

의존성:

```text
Boundary 1 Parser
Boundary 2 Registry
```

Parity:

```text
assignment before/after on_bar partition 동일
동일 valid DSL accept
동일 invalid DSL reject
value type 판정 동일
function arity/type error 동일
error line/column/code 동일
```

---

### Boundary 4 — Indicator Kernel

Source:

```text
core/indicators.py
core/user_indicators.py
```

Target:

```text
axes/axis1_dsl/indicators/indicators.py
axes/axis1_dsl/indicators/user_indicators.py
```

방식:

```text
COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
```

Parity:

```text
동일 deterministic fixtures에서 numeric arrays 동일
NaN 위치 동일
JMA reference 값 동일
JMA trend metadata 동일
normalized MACD component 동일
기존 supported indicator 결과 동일
```

주의: tuple/multi-output, JMA normalized slope 같은 신규 기능은 여기서 추가하지 않는다.

---

### Boundary 5 — State + Bar Runtime

Source:

```text
core/state.py
core/bar_runtime.py
```

Target:

```text
axes/axis1_dsl/runtime/state.py
axes/axis1_dsl/runtime/bar_runtime.py
```

방식:

```text
COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
```

의존성:

```text
Boundary 1 Parser
```

Parity:

```text
edge/falling-edge/hold/persist/latch/count/regime 동일
persistent state 동일
nested on_bar if/else 동일
prefix/streaming 기존 검증 동일
```

---

### Boundary 6 — MTF + Read-Only Context Binding

Source:

```text
core/multitimeframe.py
core/dsl_context.py
```

Legacy support sources currently referenced by context binding:

```text
core/parent_context_frame.py
core/parent_feature_provider.py
```

Target:

```text
axes/axis1_dsl/runtime/multitimeframe.py
axes/axis1_dsl/runtime/dsl_context.py
```

방식:

```text
multitimeframe.py = COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
dsl_context.py    = BOUNDARY_REFACTOR_REQUIRED
```

이유:

현재 `dsl_context.py`가 legacy provider/frame 내부 class를 직접 참조한다. 최종 AXIS 1은 provider를 소유하면 안 되므로 새 구현에서는 **이미 준비된 typed read-only context binding만 소비**해야 한다.

금지:

```text
parent provider 계산을 AXIS 1로 이식
market/sector/group provider를 AXIS 1로 이식
nearest-time/fill-forward/default 추가
```

Parity:

```text
confirmed higher-timeframe 값 동일
exact-time context 값 동일
missing/stale/future context fail-closed 동일
provider call 없음
binding 결과/type/hash-equivalent evidence 비교
```

Migration test 전용 adapter가 legacy frame/registry를 새 binding 입력으로 변환하는 것은 허용한다. production AXIS 1이 legacy provider class를 import하는 것은 금지한다.

---

### Boundary 7 — DSL Runtime

Source:

```text
core/dsl_runtime.py
```

Target:

```text
axes/axis1_dsl/runtime/dsl_runtime.py
```

방식:

```text
COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
```

의존성:

```text
Boundary 1~6
```

Parity:

```text
compiled strategy identity/timeframe 동일
assignment values 동일
event conditions 동일
order argument materialization 동일
ctx.* 실행 동일
runtime diagnostics 동일
existing additive indicator behavior 동일
```

---

### Boundary 8 — Broker

Source:

```text
core/broker.py
```

Target:

```text
axes/axis1_dsl/execution/broker.py
```

방식:

```text
COPY_AS_IS_BEHAVIOR
```

Parity:

```text
order lifecycle 동일
MARKET/LIMIT/STOP/STOP_LIMIT 동일
GTC/DAY/OCO/cancel 동일
fill price/quantity/history 동일
reject/expire behavior 동일
```

부분체결/다중포지션은 migration 중 추가하지 않는다.

---

### Boundary 9 — Backtest + Projection Output

Source:

```text
core/backtest_parent_context.py
core/backtest.py
```

Target:

```text
axes/axis1_dsl/execution/backtest_parent_context.py
axes/axis1_dsl/execution/backtest.py
```

방식:

```text
backtest.py = COPY_BEHAVIOR_WITH_INTERNAL_IMPORT_REWRITE
backtest_parent_context.py = BOUNDARY_REFACTOR_REQUIRED
```

의존성:

```text
Boundary 6 context binding
Boundary 7 DSL Runtime
Boundary 8 Broker
```

현재 Backtest 내부 projection은 migration parity 동안 그대로 보존한다.

```text
candles
markers
indicators
metrics
trades
closed trades
equity
diagnostics
```

일반 threshold/permission/pane projection 확장은 Step 5에서 별도 기능으로 수행한다.

Context adapter는 legacy provider object를 AXIS 1 production API로 끌고 오지 않고 이미 준비된 read-only binding/request input을 받는 방향으로 바꾼다.

Parity:

```text
trade sequence 동일
fill price/quantity 동일
metrics numeric 동일
markers 동일
numeric indicator projection 동일
JMA color projection 동일
signal counts/rejections 동일
bar_close/next_open 동일
MTF/context causal result 동일
```

---

## 3. AXIS 1에 이식하지 않는 legacy core 파일군

현재 legacy `core/`에는 DSL 실행엔진 외 책임이 많이 섞여 있다. 다음은 **AXIS 1 production migration 대상이 아니다.**

### Feature verification evidence / legacy test authority

```text
core/dsl_feature_catalog.py
core/dsl_feature_invariants.py
core/dsl_feature_invariants_impl.py
core/dsl_feature_invariants_v3.py
core/dsl_feature_invariants_v4.py
```

처리:

```text
frozen verification source로 보존
Step 4 parity harness에서 legacy-side evidence로 사용 가능
새 AXIS 1 production dependency로 복사하지 않음
Step 6 machine registry 확정 후 새 검증체계와 연결
```

### Strategy/artifact persistence — future AXIS 3

```text
core/db.py
```

AXIS 1로 이식 금지. 최종 Condition/Strategy CRUD는 Step 10에서 새 AXIS 3에 독립 구현한다.

### Authoring / compatibility adapters

```text
core/prompt_template.py
core/transpiler.py
```

AXIS 1 deterministic execution core로 이식하지 않는다. 필요한 기능은 향후 Authoring/adapter 경계에서 별도 판단한다.

### Data/vendor adapter

```text
core/kiwoom_rest.py
```

AXIS 1로 이식하지 않는다. 시장데이터 제공은 외부 adapter/Bridge 책임이다.

### Parent/context providers

```text
core/parent_context_frame.py
core/parent_feature_provider.py
core/parent_context_orchestrator.py
core/parent_context_dependency_orchestrator.py
core/market_parent_feature_provider.py
core/sector_parent_feature_provider.py
core/group_evidence_parent_feature_provider.py
```

AXIS 1은 계산 provider를 소유하지 않는다. 사전계산 결과를 표준 read-only input으로 소비한다.

### Multi-symbol / leader-follower research and evidence

```text
core/multi_symbol.py
core/multi_symbol_*.py
```

AXIS 1로 이식하지 않는다. point-in-time selection/evidence로 재평가할 부분은 향후 AXIS 2 책임이다.

### Tactical / adaptive / research families

```text
core/tactical_*.py
core/stage1_*.py
core/strategy_factory.py
core/tactic_family.py
core/tactic_family_catalog.py
core/battlecase_provider.py
core/battlefield_context.py
core/h1_entry_permission.py
core/range_detector_equipment.py
core/transition_shock_guard.py
```

AXIS 1 deterministic language/runtime로 이식하지 않는다. 필요한 아이디어/기능은 향후 해당 AXIS 또는 Strategy/Research layer에서 별도 검토한다. 기존 tactical 의미를 새 DSL Core에 숨겨 넣지 않는다.

### UI/static/templates

```text
core/static/
core/templates/
```

AXIS 1 실행엔진 migration 대상이 아니다.

### Legacy capability prompt list

```text
core/capabilities.py
```

현재 prompt/documentation 성격의 legacy 목록이다. Step 6에서 새 AXIS 1 machine-readable registry를 권한으로 만들기 전에는 frozen evidence로만 보존한다.

---

## 4. Package/import 전환 규칙

새 AXIS 1 production 파일은 완료 시 다음을 만족해야 한다.

```text
NO from core....
NO import core....
```

허용:

```text
새 AXIS 1 내부 package import
Python stdlib / numpy 같은 일반 dependency
Bridge에서 전달된 표준 입력 type
```

Parity test 자체는 legacy와 new implementation을 동시에 불러 비교하기 위해 frozen `core/`를 import할 수 있다. 이것은 production dependency가 아니다.

---

## 5. 첫 boundary parity test 설계

Boundary 1 Parser를 위한 focused parity test를 Step 4 첫 tranche에서 만든다.

입력 corpus:

```text
valid: Feature Catalog에서 대표 grammar/order/state DSL
valid: examples/jma_cross.dsl
invalid: unknown statement
invalid: bad order command
invalid: malformed braces/parentheses
invalid: duplicate/illegal declarations
```

비교 항목:

```text
parse PASS/FAIL 동일
StrategyNode field 동일
각 AST node type/field/value/line 동일
error class 의미 동일
error code/line/column 동일
```

테스트 출력은 정상 시 한 줄 `[PASS]` 중심으로 유지한다.

---

## 6. Step 2 완료 조건 체크

```text
[x] production migration 대상 분리
[x] AXIS 1에 가져오지 않을 legacy 책임 분리
[x] target path 정의
[x] 9개 migration boundary 순서 정의
[x] 각 boundary의 parity 기준 정의
[x] first boundary = Parser/AST 확정
[x] context provider coupling을 migration 위험으로 명시
[x] projection 확장은 migration 뒤로 분리
[x] 신규 DSL 기능은 migration 뒤 Step 5로 분리
```

Step 2에서 실제 AXIS 1 source migration은 수행하지 않는다.

다음 Step은 **Step 3 — Frozen Core 보호 gate 검증**이다.
