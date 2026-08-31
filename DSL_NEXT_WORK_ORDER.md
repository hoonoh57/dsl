# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 11
CURRENT_STEP_NAME = AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
CURRENT_SUBSTEP = 11-1 selection -> promoted run plan -> per-candidate AXIS1 backtest routing
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 migration user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능/검증 user-local PASS
STEP 6 COMPLETE = capability/diagnostic registry user-local PASS
STEP 7 COMPLETE = Bridge common + AXIS 1 execution contract user-local PASS
STEP 8 COMPLETE = AXIS 2 exact-as-of snapshot contract user-local PASS
STEP 9 COMPLETE = AXIS 2 deterministic selection engine user-local PASS
STEP 10 COMPLETE = AXIS 3 Condition/Strategy CRUD + orchestration user-local PASS
  -> STEP10_AXIS3_CRUD_ORCHESTRATION_CHECKPOINT_2026-09-01.md
```

Step 10 user-local evidence:

```text
test_axis3_crud_orchestration.py = OK
test_axis2_selection_engine.py = OK
test_axis2_exact_asof_snapshot.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 11 현재 — versioned three-axis E2E Bridge

목표:

```text
exact PIT snapshot
 -> AXIS 2 deterministic CandidateSet
 -> AXIS 3 promoted exact Strategy/Condition + StrategyRunPlan
 -> 후보별 versioned AXIS 1 BACKTEST request
 -> ordered execution responses
```

세 축의 계산 권한을 합치지 않고 Bridge 계층에서 데이터 계약만 연결한다.

### 구현

```text
bridges/contracts/three_axis_e2e.py
bridges/contracts/three_axis_e2e_request.v1.schema.json
bridges/contracts/three_axis_e2e_response.v1.schema.json
bridges/three_axis_e2e_bridge.py
tests/test_three_axis_e2e_bridge.py
```

### E2E Request v1

```text
schema = bridge.three_axis_e2e_request/v1
route = source -> AXIS3 / SELECT_PLAN_BACKTEST
run_id
strategy_ref = id/version/artifact_hash
condition_ref = id/version/artifact_hash
axis2 point-in-time snapshot + snapshot_hash
axis2 selection spec + selection_hash
symbol별 explicit market / optional entry_gate / optional parent_context
```

입력은 JSON-safe data만 허용한다. opaque object / NaN / Infinity / unknown field / wrong route는 fail-closed다.

### Routing authority

Bridge 실행 순서:

```text
1. PointInTimeSnapshot exact hash/causality 검증
2. SelectionSpec selection_hash 검증
3. AXIS 2 SelectionEngine -> CandidateSet v1
4. AXIS 3 build_strategy_run_plan()
5. promoted exact Strategy/Condition + artifact_hash 재검증
6. 모든 selected candidate market 입력을 AXIS 1 Request로 사전검증
7. candidate ordinal 순서대로 기존 AXIS 1 execution Bridge 호출
8. CandidateSet / RunPlan / AXIS1 response trace 반환
```

### Partial routing 방지

선정된 후보 중 하나라도 market/entry_gate/context 입력이 잘못되거나 누락되면 AXIS 1 실행 시작 전에 전체 preflight가 실패한다.

AXIS 1 자체의 DSL/실행 rejection은 후보별 response에 그대로 남기고 전체 E2E status를 `REJECTED`로 표시한다. AXIS 2 CandidateSet과 AXIS 3 RunPlan trace는 보존한다.

### Deterministic trace

응답은 다음을 보존한다.

```text
outer request_hash / response_hash
AXIS 2 candidate_set_hash / selection_hash / snapshot_hash
AXIS 3 plan_hash / strategy_hash / condition_hash
candidate symbol + ordinal
후보별 AXIS1 request_hash + versioned response
```

같은 저장 artifact + snapshot + spec + market inputs이면 같은 route identity/hash가 나와야 한다.

### Step 11 경계

```text
AXIS 2가 DSL/Broker 실행하지 않음
AXIS 3가 selection/DSL compile을 재구현하지 않음
AXIS 1이 universe discovery/Strategy CRUD를 하지 않음
contracts/ 는 data-only이며 axes import 없음
three-axis Bridge는 AXIS1 내부 runtime을 직접 import하지 않고 기존 Axis1 Bridge만 호출
provider/network/nearest-time/fill-forward/default synthesis 없음
frozen core import/수정 없음
```

Step 11 완료 조건:

```text
outer version/schema/route/unknown/opaque/nonfinite fail-closed PASS
snapshot_hash + selection_hash tamper reject before AXIS1 PASS
AXIS2 CandidateSet deterministic candidate order PASS
PROMOTED exact Strategy/Condition + artifact hash binding PASS
CandidateSet -> RunPlan hash/ordinal/evidence preservation PASS
selected candidate execution inputs all preflight before first AXIS1 call PASS
RunPlan intent -> existing AXIS1 request contract exact conversion PASS
candidate ordinal order -> AXIS1 execution response order exact PASS
AXIS1 rejection visible while CandidateSet/RunPlan trace retained PASS
same inputs -> same outer request/response hash PASS
contracts data-only isolation PASS
Bridge no frozen-core / no direct AXIS1 internal import PASS
Step 10 CRUD/orchestration regression PASS
Step 9 selection regression PASS
Step 7 AXIS1 bridge regression PASS
frozen core guard PASS
focused user-local E2E test PASS
```

Step 11 PASS + checkpoint 전 Step 12 시작 금지.

---

## 이후 고정 순서

```text
12 External LLM Authoring Lane implementation
13 Continuous Improvement analysis tooling
14 Final natural-language E2E acceptance
15 Legacy docs disposition + repo-wide compliance audit
```

---

## 절대 원칙

```text
frozen legacy core 수정 금지
AXIS 1 = single-instrument deterministic execution
AXIS 2 = immutable PIT selection semantics
AXIS 3 = versioned Condition/Strategy lifecycle + orchestration
축간 연결 = versioned Request -> Response only
future value / nearest-time / fill-forward / default synthesis 금지
다른 축 내부 객체/state를 contract payload로 전달 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
