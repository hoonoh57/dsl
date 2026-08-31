# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 10
CURRENT_STEP_NAME = AXIS 3 Condition / Strategy CRUD + orchestration
CURRENT_SUBSTEP = 10-1 versioned artifact store + deterministic strategy run plan
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
  -> STEP9_AXIS2_SELECTION_ENGINE_CHECKPOINT_2026-09-01.md
```

Step 9 user-local evidence:

```text
test_axis2_selection_engine.py = OK
test_axis2_exact_asof_snapshot.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 10 현재 — AXIS 3 versioned CRUD + orchestration

목표:

```text
Condition/Strategy 연구 결과를 Feature Catalog와 분리된 AXIS 3 저장소에서
immutable version + lineage + lifecycle로 관리하고,
promoted exact artifacts + CandidateSet data만으로 deterministic strategy run plan을 만든다.
```

### 권한 정리

Condition 책임은 의미와 lifecycle을 분리한다.

```text
AXIS 2 = Condition selection semantics / snapshot filter-rank-topN / CandidateSet authority
AXIS 3 = Condition artifact CRUD/version/lineage/promotion state
```

AXIS 3는 `axis2_selection_spec/v1` 데이터를 immutable product artifact로 보존하지만
AXIS 2 filter/rank/top-N을 재구현하거나 실행하지 않는다.

Strategy 책임:

```text
AXIS 3 = Strategy CRUD / immutable version / lineage / compare / promotion-rejection-archive
AXIS 1 = DSL parse/compile/execute authority
```

### 구현

```text
axes/axis3_monetization/__init__.py
axes/axis3_monetization/crud/__init__.py
axes/axis3_monetization/crud/versioned_store.py
axes/axis3_monetization/crud/condition_version.v1.schema.json
axes/axis3_monetization/crud/strategy_version.v1.schema.json
axes/axis3_monetization/orchestration/__init__.py
axes/axis3_monetization/orchestration/run_plan.py
axes/axis3_monetization/orchestration/strategy_run_plan.v1.schema.json
tests/test_axis3_crud_orchestration.py
```

### VersionedArtifactStore

독립 SQLite 저장소를 사용한다.

```text
Condition content table
Condition lifecycle state table
Strategy content table
Strategy lifecycle state table
append-only lifecycle event audit
```

규칙:

```text
content update = 새 version 생성
기존 version overwrite 금지
첫 version parent 없음
후속 version parent lineage 보존
Strategy condition_ref는 존재하는 exact Condition version만 허용
artifact content hash deterministic
NaN/Infinity/opaque payload 금지
```

CRUD의 delete 의미는 hard delete가 아니라 archive다. 연구/검증 계보를 삭제하지 않는다.

### Lifecycle

```text
DRAFT -> PROMOTED | REJECTED | ARCHIVED
PROMOTED -> ARCHIVED
REJECTED -> ARCHIVED
ARCHIVED -> terminal
```

content hash와 lifecycle state는 분리한다. promote/reject/archive가 immutable baseline content를 변경하지 않는다.

### Strategy comparison

동일 strategy_id의 두 version에 대해 다음 차이를 명시적으로 비교한다.

```text
name
timeframe
dsl_code
settings
condition_refs
artifact hash
```

### Deterministic orchestration plan

`build_strategy_run_plan()`은 다음 exact data만 사용한다.

```text
PROMOTED Strategy version
PROMOTED Condition version
Strategy가 실제로 참조하는 exact Condition version
axis2_candidate_set/v1 data snapshot
```

CandidateSet에 대해 다음을 확인한다.

```text
candidate_set_hash exact
selection_hash exact
condition_version label exact
snapshot_hash exact
as_of exact
knowledge_cutoff exact
candidate ordinal 1..N deterministic
```

출력 `axis3_strategy_run_plan/v1`은 후보별 execution intent를 만든다.

```text
symbol
candidate ordinal
strategy id/version/hash
DSL source + timeframe + settings
condition id/version/hash
candidate_set hash
evidence
```

중요:

```text
Step 10에서는 market/provider를 조회하지 않음
AXIS 1 실행을 호출하지 않음
AXIS 2 selection을 호출하지 않음
execution intent를 Bridge request로 변환하는 실제 E2E routing은 Step 11
```

### Step 10 경계

```text
AXIS 1/AXIS 2 내부 모듈 direct import 금지
frozen core import/수정 금지
Feature Catalog 수정 금지
DSL compile validation을 AXIS 3에서 재구현 금지
CandidateSet 재계산/순위 재계산 금지
lifecycle 변경으로 artifact content overwrite 금지
```

Step 10 완료 조건:

```text
Condition create/read/version-list + lineage persistence PASS
Strategy create/read/version-list + exact Condition ref validation PASS
content update가 overwrite가 아닌 새 immutable version 생성 PASS
SQLite reopen 후 동일 artifact/hash 복구 PASS
promote/reject/archive transition + audit PASS
invalid lifecycle transition fail-closed PASS
strategy version comparison PASS
nonfinite/opaque artifact input reject PASS
orchestration은 promoted exact artifacts만 허용 PASS
CandidateSet tamper/hash/selection/snapshot/as_of/cutoff drift fail-closed PASS
동일 inputs -> 동일 strategy run plan hash PASS
candidate ordinal/order 보존 PASS
AXIS1/AXIS2/frozen-core import isolation PASS
Step 9 selection regression PASS
Step 8 snapshot regression PASS
frozen core guard PASS
focused user-local AXIS3 CRUD/orchestration test PASS
```

Step 10 PASS + checkpoint 전 Step 11 시작 금지.

---

## 이후 고정 순서

```text
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
AXIS 1 = single-instrument deterministic execution
AXIS 2 = immutable PIT selection semantics
AXIS 3 = versioned Condition/Strategy product lifecycle + orchestration
축간 연결 = versioned Request -> Response only
future value / nearest-time / fill-forward / default synthesis 금지
다른 축 내부 객체/state direct import 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
