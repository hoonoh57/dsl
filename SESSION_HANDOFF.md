# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 11 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> AXIS 1은 실행, AXIS 2는 immutable PIT selection, AXIS 3는 versioned artifact lifecycle/orchestration을 담당한다. 세 축의 계산 권한은 섞지 않고 Bridge가 versioned data만 연결한다.

---

## 현재 작업

```text
CURRENT_STEP = 11
CURRENT_SUBSTEP = 11-1 selection -> promoted run plan -> per-candidate AXIS1 backtest routing
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 migration = COMPLETE / USER-LOCAL PASS
Step 5 AXIS 1 신규 DSL 기능/검증 = COMPLETE / USER-LOCAL PASS
Step 6 capability/diagnostic registry = COMPLETE / USER-LOCAL PASS
Step 7 Bridge common + AXIS 1 execution contract = COMPLETE / USER-LOCAL PASS
Step 8 AXIS 2 exact-as-of snapshot contract = COMPLETE / USER-LOCAL PASS
Step 9 AXIS 2 selection engine = COMPLETE / USER-LOCAL PASS
Step 10 AXIS 3 Condition/Strategy CRUD + orchestration = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP10_AXIS3_CRUD_ORCHESTRATION_CHECKPOINT_2026-09-01.md
```

Step 10 user-local evidence:

```text
test_axis3_crud_orchestration.py = OK
test_axis2_selection_engine.py = OK
test_axis2_exact_asof_snapshot.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 11 구현

구현:

```text
bridges/contracts/three_axis_e2e.py
bridges/contracts/three_axis_e2e_request.v1.schema.json
bridges/contracts/three_axis_e2e_response.v1.schema.json
bridges/three_axis_e2e_bridge.py
tests/test_three_axis_e2e_bridge.py
```

### 흐름

```text
exact PointInTimeSnapshot
 -> AXIS 2 SelectionSpec / CandidateSet
 -> promoted exact AXIS 3 Condition + Strategy
 -> deterministic StrategyRunPlan
 -> 후보별 existing AXIS 1 Bridge BACKTEST request
 -> ordered AXIS 1 responses
```

### Outer request

```text
bridge.three_axis_e2e_request/v1
run_id
strategy id/version/hash
condition id/version/hash
snapshot + snapshot_hash
selection spec + selection_hash
symbol별 explicit execution input
```

opaque object / nonfinite / unknown field / wrong route는 contract 단계에서 거부한다.

### Exact binding

```text
snapshot hash exact
selection hash exact
promoted strategy/condition exact version
strategy/condition artifact hash exact
CandidateSet -> RunPlan selection/snapshot/candidate hash exact
candidate ordinal 그대로 보존
```

선정된 모든 후보의 market/entry_gate/context 입력은 AXIS 1 호출 전에 먼저 preflight한다. 후순위 후보 입력이 잘못되어 일부 후보만 먼저 실행되는 상태를 만들지 않는다.

### AXIS 1 연결

RunPlan intent를 기존 `bridge.axis1_execution_request/v1`로 변환한다.

```text
source = AXIS3
target = AXIS1
operation = BACKTEST
strategy id/version/DSL/timeframe/settings = exact RunPlan intent
symbol = exact candidate
market/context/gate = outer request의 해당 symbol data
```

AXIS 1 실행 거부는 숨기지 않는다.

```text
CandidateSet trace 유지
RunPlan trace 유지
후보별 AXIS1 REJECTED response 유지
overall E2E status = REJECTED
```

### Trace

```text
outer request_hash / response_hash
CandidateSet + candidate_set_hash
StrategyRunPlan + plan_hash
candidate ordinal
AXIS1 request_hash + response
```

### 경계

```text
contracts는 axes import 없는 data-only
Bridge만 축 public authority를 조합
AXIS1 내부 runtime 직접 import 없음
provider/network 조회 없음
nearest-time/fill-forward/default synthesis 없음
frozen core import/수정 없음
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
11 AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge    CURRENT
12 External LLM Authoring Lane
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_three_axis_e2e_bridge.py" -v
python -m unittest discover -s tests -p "test_axis3_crud_orchestration.py" -v
python -m unittest discover -s tests -p "test_axis2_selection_engine.py" -v
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 11 checkpoint 후 Step 12 External LLM Authoring Lane implementation으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
