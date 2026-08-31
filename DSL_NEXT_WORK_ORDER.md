# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 8
CURRENT_STEP_NAME = AXIS 2 exact-as-of snapshot contract
CURRENT_SUBSTEP = 8-1 immutable point-in-time feature/rank snapshot v1
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
STEP 7 COMPLETE = Bridge common + AXIS 1 execution contract user-local PASS
  -> STEP7_AXIS1_EXECUTION_BRIDGE_CHECKPOINT_2026-09-01.md
```

Step 7 user-local evidence:

```text
test_axis1_execution_bridge_contract.py = OK (7)
test_axis1_capability_diagnostic_registry.py = OK (6)
test_axis1_full_engine_parity.py = OK (5)
test_frozen_legacy_core_guard.py = OK (1)
```

---

## Step 8 현재 — AXIS 2 exact-as-of snapshot contract

목표:

```text
provider/precompute 단계가 만든 cross-market/cross-symbol feature와 rank evidence를
정확한 as_of + knowledge_cutoff 기준 immutable snapshot으로 동결하고,
AXIS 2 selection은 이후 이 snapshot만 소비하도록 S0 계약을 고정한다.
```

구현:

```text
axes/axis2_selection/__init__.py
axes/axis2_selection/snapshots/__init__.py
axes/axis2_selection/snapshots/exact_asof.py
axes/axis2_selection/snapshots/point_in_time_snapshot.v1.schema.json
tests/test_axis2_exact_asof_snapshot.py
```

### Snapshot v1 최소 계약

```text
schema_version = axis2_point_in_time_snapshot/v1
snapshot_id
as_of = YYYYMMDDHHMMSS exact
knowledge_cutoff = YYYYMMDDHHMMSS exact
universe_id
feature_version
source_refs[]
rows[]
```

각 row:

```text
symbol
feature_id
value_type = NUMBER | BOOLEAN | STRING
value
validity = VALID | MISSING | INVALID
provenance
  source_ref
  observed_as_of
  knowledge_cutoff
  formula_version
optional ranking
  ranking_method
  eligible_count
  rank
  percentile (0..100)
  peer_group_id
```

### Point-in-time fail-closed 규칙

```text
snapshot knowledge_cutoff > as_of 금지
row observed_as_of > knowledge_cutoff 금지
row별 knowledge_cutoff 혼합 금지
row별 formula_version 혼합 금지
snapshot에 선언되지 않은 source_ref 금지
non-finite numeric value 금지
opaque value 금지
중복 row identity 금지
동일 feature/peer group에서 ranking_method/eligible_count 혼합 금지
```

Missing/invalid 값은 다음처럼만 보존한다.

```text
validity != VALID -> value = None
validity != VALID -> ranking 없음
0/false/중립값 자동대체 금지
```

### Exact lookup 규칙

`PointInTimeSnapshot.require_exact()`은 exact `as_of`와 optional exact `knowledge_cutoff`만 허용한다.

```text
nearest-time 없음
previous-nearest 없음
fill-forward 없음
interpolation 없음
현재값으로 과거 snapshot 재구성 없음
```

### Immutable / identity

```text
frozen dataclass + tuple rows/source refs
canonical JSON SHA-256 snapshot_hash
supplied snapshot_hash 불일치 fail-closed
```

### Step 8 경계

```text
이 단계는 snapshot data contract만 구현
provider/raw feature calculation 미구현
selection filter/rank/top-N engine 미구현 (Step 9)
AXIS 1 DSL/runtime 호출 없음
AXIS 3 내부 import 없음
frozen core import/수정 없음
```

Step 8 완료 조건:

```text
schema/version/unknown field fail-closed PASS
snapshot deterministic hash + roundtrip PASS
immutable snapshot/row PASS
future observation/future cutoff reject PASS
mixed cutoff/formula version reject PASS
missing/invalid no-default contract PASS
rank range + peer ranking contract PASS
exact as_of/cutoff lookup only PASS
duplicate/nonfinite/opaque input reject PASS
snapshot hash tamper detection PASS
AXIS1/AXIS3/provider/frozen-core import isolation PASS
Step 7 Bridge regression PASS
frozen core guard PASS
focused user-local AXIS2 snapshot test PASS
```

Step 8 PASS + checkpoint 전 Step 9 시작 금지.

---

## 이후 고정 순서

```text
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
AXIS 1은 single-instrument deterministic execution 권한만 유지
AXIS 2는 immutable point-in-time evidence만 사용
축간 연결은 versioned Request -> Response로만 수행
future value / nearest-time / fill-forward / default synthesis 금지
다른 축 내부 객체/state direct import 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
