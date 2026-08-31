# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 7
CURRENT_STEP_NAME = Bridge common + AXIS 1 execution contract
CURRENT_SUBSTEP = 7-1 versioned common boundary + AXIS 1 BACKTEST Request/Response
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능 개발 + 검증 전체 user-local PASS
STEP 6 COMPLETE = AXIS 1 machine-readable capability/diagnostic registry user-local PASS
  -> STEP6_CAPABILITY_DIAGNOSTIC_REGISTRY_CHECKPOINT_2026-09-01.md
```

Step 6 user-local evidence:

```text
test_axis1_capability_diagnostic_registry.py = OK
test_axis1_capability_metadata.py = OK
test_axis1_full_engine_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 7 현재 — Bridge common + AXIS 1 execution contract

목표:

```text
AXIS 2/3/외부 호출자가 AXIS 1 내부 객체/상태를 직접 참조하지 않고
versioned JSON-safe Request -> Response 계약으로만 AXIS 1 실행을 요청하도록 경계를 고정한다.
```

구현:

```text
bridges/contracts/common.py
bridges/contracts/axis1_execution.py
bridges/contracts/axis1_execution_request.v1.schema.json
bridges/contracts/axis1_execution_response.v1.schema.json
bridges/axis1_execution_bridge.py
tests/test_axis1_execution_bridge_contract.py
```

### Common Bridge contract

```text
contract_version = v1
request/response route = source_axis -> target_axis + operation
unknown schema/version/field/route = fail-closed
request payload는 JSON-safe scalar/list/mapping만 허용
opaque Python runtime object 전달 금지
request_hash / response_hash = deterministic canonical SHA-256
```

Bridge contract module은 AXIS 1/2/3 구현을 import하지 않는 data-only 계층이다.

### AXIS 1 execution Request v1

```text
schema = bridge.axis1_execution_request/v1
operation = BACKTEST
target_axis = AXIS1
```

Request가 소유하는 데이터:

```text
request identity / source axis
instrument symbol + timeframe
strategy_id + strategy_version + DSL source
explicit OHLCV market bars
execution settings
optional exact-length boolean entry_gate
optional prepared parent_context payload
```

Request에는 다음을 넣지 않는다.

```text
Axis2/Axis3 내부 객체
provider/database/session 객체
mutable runtime object
nearest-time/fill-forward instruction
AXIS 1 internal compiled/runtime/broker object
```

### Parent context boundary

```text
schema = dsl_parent_context_series/v1
target_symbol = request symbol exact 일치
target_times = request market.time exact 일치
feature type/value identity exact 일치
binding_hash가 제공되면 AXIS 1 재구성 hash와 exact 일치
```

AXIS 1 adapter가 `DSLContextSeriesBinding.from_prepared`로 자신의 immutable binding을 새로 만든다. 다른 축의 객체를 직접 전달받지 않는다.

### AXIS 1 execution Response v1

```text
schema = bridge.axis1_execution_response/v1
source_axis = AXIS1
status = OK | REJECTED | ERROR
request_hash 포함
현재 AXIS 1 capability_registry_hash 포함
response_hash 포함
```

정상 실행은 strategy/instrument reference와 AXIS 1 facade 결과를 JSON-safe snapshot으로 반환한다.

AXIS 1 계산 결과에 `Infinity/NaN`이 의미있는 진단값으로 존재하면 임의 0/default로 바꾸지 않고 다음 tagged JSON 형태로 명시한다.

```text
{"$number": "Infinity"}
{"$number": "-Infinity"}
{"$number": "NaN"}
```

Request 입력에서는 NaN/Infinity를 계속 금지한다.

### Adapter authority

```text
bridges.axis1_execution_bridge
  contract validate
  -> AXIS 1-owned market/context input 구성
  -> Axis1BacktestEngine public facade 호출
  -> JSON-safe versioned response
```

Adapter가 호출하는 AXIS 1 범위:

```text
Axis1BacktestEngine
DSLContextSeriesBinding
capability registry hash
```

AXIS 2/3 내부 구현 import 금지.

### 중요 경계

```text
Bridge는 AXIS 1 계산식을 재구현하지 않음
Bridge는 후보선정/랭킹/전략 CRUD를 수행하지 않음
AXIS 1이 universe discovery를 하지 않음
AXIS 2/3 내부 상태 direct import 금지
frozen core 수정/import 없음
Step 8 AXIS 2 snapshot 선행 구현 없음
```

Step 7 완료 조건:

```text
version/schema/route fail-closed PASS
unknown field + opaque object reject PASS
market bar count/time order/nonfinite validation PASS
entry_gate exact length/type PASS
prepared parent context symbol/time exact contract PASS
request hash deterministic PASS
valid request -> AXIS 1 facade -> versioned OK response PASS
valid envelope + invalid AXIS 1 DSL -> structured REJECTED response PASS
capability registry hash response 포함 PASS
non-finite execution result tagged serialization PASS
contract modules data-only import isolation PASS
adapter Axis2/Axis3/frozen-core import isolation PASS
Step 6 registry regression PASS
Step 5-10 full-engine parity regression PASS
frozen core guard PASS
focused user-local Bridge contract test PASS
```

Step 7 PASS + checkpoint 전 Step 8 시작 금지.

---

## 이후 고정 순서

```text
8 AXIS 2 exact-as-of snapshot contract
9 AXIS 2 selection engine / core selectors
10 AXIS 3 Condition / Strategy CRUD + orchestration
11 AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
12 External LLM Authoring Lane implementation
13 Continuous Improvement analysis tooling
14 Final natural-language E2E acceptance
15 Legacy docs disposition + repo-wide compliance audit
```

---

## 절대 원칙

```text
frozen legacy core 수정 금지
검증된 migrated core를 신규기능 때문에 불필요하게 흔들지 않음
축간 연결은 versioned Request -> Response로만 수행
다른 축 내부 객체/state direct import 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
