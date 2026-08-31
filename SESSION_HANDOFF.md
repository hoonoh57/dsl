# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 7 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 AXIS 1 실행부는 안정된 실행 장비처럼 유지한다. 축간 연결은 versioned Request -> Response 계약으로만 수행한다.

---

## 현재 작업

```text
CURRENT_STEP = 7
CURRENT_SUBSTEP = 7-1 versioned common boundary + AXIS 1 BACKTEST Request/Response
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
Step 5 AXIS 1 신규 DSL 기능 개발/검증 = COMPLETE / USER-LOCAL PASS
Step 6 capability/diagnostic registry = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP6_CAPABILITY_DIAGNOSTIC_REGISTRY_CHECKPOINT_2026-09-01.md
```

Step 6 user-local evidence:

```text
test_axis1_capability_diagnostic_registry.py = OK
test_axis1_capability_metadata.py = OK
test_axis1_full_engine_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 7 구현

구현:

```text
bridges/contracts/common.py
bridges/contracts/axis1_execution.py
bridges/contracts/axis1_execution_request.v1.schema.json
bridges/contracts/axis1_execution_response.v1.schema.json
bridges/axis1_execution_bridge.py
tests/test_axis1_execution_bridge_contract.py
```

### 목적

AXIS 2/3/외부가 AXIS 1 내부 runtime/broker/context 객체를 직접 넘기지 않고, 명시적인 데이터 계약만으로 실행을 요청하도록 한다.

### Request

```text
schema = bridge.axis1_execution_request/v1
operation = BACKTEST
source_axis = AXIS2 | AXIS3 | EXTERNAL
target_axis = AXIS1
```

입력 데이터:

```text
request_id
instrument symbol/timeframe
strategy_id/version + DSL code
explicit OHLCV bars
settings
optional boolean entry_gate
optional prepared parent-context data
```

Bridge 입력은 JSON-safe 데이터만 허용한다. opaque Python object, NaN/Infinity 입력, unknown field/version/route는 fail-closed다.

### Parent context

prepared payload는 기존 `dsl_parent_context_series/v1` 데이터 형태만 허용한다.

```text
target_symbol == request symbol
target_times == market.time exact
feature_types keys == feature_values keys
binding_hash supplied 시 AXIS 1 재구성 hash와 exact
```

Bridge adapter가 AXIS 1 내부 `DSLContextSeriesBinding`을 새로 생성한다.

### Response

```text
schema = bridge.axis1_execution_response/v1
source_axis = AXIS1
status = OK | REJECTED | ERROR
request_hash
capability_registry_hash
result 또는 error
response_hash
```

실행결과에 의미있는 Infinity/NaN이 존재할 경우 0으로 바꾸지 않고 JSON tagged value로 보존한다.

```text
{"$number":"Infinity"}
{"$number":"-Infinity"}
{"$number":"NaN"}
```

### Adapter 경계

`bridges.axis1_execution_bridge`만 AXIS 1 public facade를 호출한다.

허용:

```text
Axis1BacktestEngine
DSLContextSeriesBinding
capability registry hash
```

금지:

```text
Axis2/Axis3 내부 import
provider/database 객체 전달
AXIS 1 계산식 재구현
Bridge 내 후보선정/랭킹/전략 CRUD
frozen core import/수정
```

---

## 검증 예정

```text
request schema/version/route/unknown field fail-closed
opaque/nonfinite request reject
deterministic request hash
entry_gate exact-length boolean contract
parent-context exact symbol/time contract
valid request -> AXIS 1 facade -> OK response
bad DSL -> structured REJECTED response
capability registry hash binding
nonfinite output tagged serialization
contract data-only import isolation
adapter cross-axis/frozen-core import isolation
Step 6 registry regression
Step 5-10 full-engine parity regression
frozen core guard
```

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

---

## 다음 순서

```text
7 Bridge common + AXIS 1 execution contract    CURRENT
8 AXIS 2 exact-as-of snapshot contract
9 AXIS 2 selection engine
10 AXIS 3 Condition/Strategy CRUD
11 3축 E2E Bridge
12 External LLM Authoring Lane
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_axis1_capability_diagnostic_registry.py" -v
python -m unittest discover -s tests -p "test_axis1_full_engine_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 7 checkpoint 후 Step 8 AXIS 2 exact-as-of snapshot contract로 이동한다.

실패 시 test defect / product defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
