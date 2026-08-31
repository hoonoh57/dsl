# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 10 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> AXIS 1은 실행, AXIS 2는 immutable PIT selection, AXIS 3는 versioned Condition/Strategy lifecycle과 orchestration을 담당한다. 축간 연결은 versioned Request -> Response 계약으로만 수행한다.

---

## 현재 작업

```text
CURRENT_STEP = 10
CURRENT_SUBSTEP = 10-1 versioned artifact store + deterministic strategy run plan
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
Step 9 AXIS 2 deterministic selection engine = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP9_AXIS2_SELECTION_ENGINE_CHECKPOINT_2026-09-01.md
```

Step 9 user-local evidence:

```text
test_axis2_selection_engine.py = OK
test_axis2_exact_asof_snapshot.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 10 구현

### 책임

```text
AXIS 2 = Condition selection semantics / CandidateSet authority
AXIS 3 = Condition artifact CRUD/version/lifecycle + Strategy CRUD/version/lifecycle + orchestration
```

AXIS 3 Condition artifact는 AXIS 2 `axis2_selection_spec/v1` data를 immutable version으로 보존한다. AXIS 3가 filter/rank/top-N을 재실행하지 않는다.

### 구현 파일

```text
axes/axis3_monetization/crud/versioned_store.py
axes/axis3_monetization/crud/condition_version.v1.schema.json
axes/axis3_monetization/crud/strategy_version.v1.schema.json
axes/axis3_monetization/orchestration/run_plan.py
axes/axis3_monetization/orchestration/strategy_run_plan.v1.schema.json
tests/test_axis3_crud_orchestration.py
```

### 저장소

AXIS 3 전용 SQLite 저장소다.

```text
Condition immutable versions
Strategy immutable versions
separate lifecycle state
append-only lifecycle audit
```

Content 수정은 기존 row update가 아니라 새 version 생성이다.

```text
v1 -> v2 -> v3
parent_version lineage 보존
기존 hash/content 유지
```

Strategy는 존재하는 exact Condition version만 참조할 수 있다.

### Lifecycle

```text
DRAFT -> PROMOTED / REJECTED / ARCHIVED
PROMOTED -> ARCHIVED
REJECTED -> ARCHIVED
ARCHIVED terminal
```

lifecycle 변경은 content hash를 바꾸지 않는다.

### Orchestration

`build_strategy_run_plan()`은 실제 실행 전의 deterministic plan만 만든다.

필수:

```text
PROMOTED Strategy exact version
PROMOTED Condition exact version
Strategy condition_ref exact 일치
axis2_candidate_set/v1 data
CandidateSet hash / selection / snapshot / as_of / cutoff exact binding
```

출력은 후보별 execution intent다.

```text
symbol / ordinal
strategy version/hash
DSL/timeframe/settings
condition version/hash
candidate_set hash
evidence
```

Step 10에서는 AXIS 1 Bridge를 아직 호출하지 않는다. 실제 Axis2 -> Axis3 -> Axis1 routing은 Step 11이다.

### 경계

```text
AXIS 1 내부 import 없음
AXIS 2 내부 import 없음
frozen core import 없음
Feature Catalog 수정 없음
provider/market lookup 없음
CandidateSet 재계산 없음
DSL compile/execute 없음
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
10 AXIS 3 Condition/Strategy CRUD + orchestration    CURRENT
11 AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
12 External LLM Authoring Lane
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis3_crud_orchestration.py" -v
python -m unittest discover -s tests -p "test_axis2_selection_engine.py" -v
python -m unittest discover -s tests -p "test_axis2_exact_asof_snapshot.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 10 checkpoint 후 Step 11 versioned E2E Bridge로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
