# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 8 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> AXIS 1은 single-instrument deterministic execution, AXIS 2는 immutable point-in-time selection evidence를 담당한다. 축간 연결은 versioned Request -> Response 계약으로만 수행한다.

---

## 현재 작업

```text
CURRENT_STEP = 8
CURRENT_SUBSTEP = 8-1 immutable point-in-time feature/rank snapshot v1
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
Step 7 Bridge common + AXIS 1 execution contract = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP7_AXIS1_EXECUTION_BRIDGE_CHECKPOINT_2026-09-01.md
```

Step 7 user-local evidence:

```text
test_axis1_execution_bridge_contract.py = OK
test_axis1_capability_diagnostic_registry.py = OK
test_axis1_full_engine_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 8 구현

구현:

```text
axes/axis2_selection/snapshots/exact_asof.py
axes/axis2_selection/snapshots/point_in_time_snapshot.v1.schema.json
tests/test_axis2_exact_asof_snapshot.py
```

목적:

```text
precompute -> immutable exact-as-of snapshot -> selection
```

Snapshot:

```text
schema = axis2_point_in_time_snapshot/v1
snapshot_id
as_of
knowledge_cutoff
universe_id
feature_version
source_refs
rows
snapshot_hash
```

Row:

```text
symbol / feature_id / typed value / validity
source provenance
optional already-frozen ranking evidence
```

PIT 안전규칙:

```text
knowledge_cutoff <= as_of
observed_as_of <= knowledge_cutoff
모든 row cutoff exact 동일
모든 row formula_version exact 동일
undeclared source_ref 금지
nonfinite/opaque 값 금지
```

Missing/invalid:

```text
value = None 그대로 보존
0/false/중립값 합성 금지
invalid row에 ranking 금지
```

Exact access:

```text
require_exact(as_of, optional cutoff)
nearest-time / fill-forward / interpolation 없음
```

Ranking evidence:

```text
ranking_method
eligible_count
rank
percentile 0..100
peer_group_id
```

동일 feature + peer group에서 ranking method와 eligible_count가 달라지면 snapshot 자체를 거부한다.

Step 8은 provider나 selection engine을 구현하지 않는다. AXIS 1/AXIS 3 내부 구현 및 frozen core import도 없다.

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
8 AXIS 2 exact-as-of snapshot contract          CURRENT
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
python -m unittest discover -s tests -p "test_axis2_exact_asof_snapshot.py" -v
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 8 checkpoint 후 Step 9 AXIS 2 selection engine / core selectors로 이동한다.

실패 시 test defect / product defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
