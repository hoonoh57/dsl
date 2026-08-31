# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 9
CURRENT_STEP_NAME = AXIS 2 selection engine / core selectors
CURRENT_SUBSTEP = 9-1 deterministic snapshot filter / rank / top-N + CandidateSet v1
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
STEP 8 COMPLETE = AXIS 2 exact-as-of immutable snapshot contract user-local PASS
  -> STEP8_AXIS2_EXACT_ASOF_SNAPSHOT_CHECKPOINT_2026-09-01.md
```

Step 8 user-local evidence:

```text
test_axis2_exact_asof_snapshot.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 9 현재 — AXIS 2 deterministic selection engine

목표:

```text
동일 immutable snapshot + 동일 selection spec
-> 언제 실행해도 동일 CandidateSet
```

구현:

```text
axes/axis2_selection/engine/__init__.py
axes/axis2_selection/engine/selection.py
axes/axis2_selection/engine/selection_spec.v1.schema.json
axes/axis2_selection/engine/candidate_set.v1.schema.json
tests/test_axis2_selection_engine.py
```

### SelectionSpec v1

```text
schema = axis2_selection_spec/v1
selection_id
condition_version
snapshot_id + snapshot_hash
exact as_of + knowledge_cutoff
filters[]
optional sort
optional top_n
optional exact symbol_scope
```

SelectionSpec는 snapshot identity에 강하게 바인딩된다.

```text
snapshot_id mismatch -> FAIL
snapshot_hash mismatch -> FAIL
as_of mismatch -> FAIL
knowledge_cutoff mismatch -> FAIL
```

nearest-time / previous snapshot / fill-forward mode는 없다.

### Generic filter

지원 metric:

```text
VALUE
RANK
PERCENTILE
```

지원 operator:

```text
EQ / NE / GT / GTE / LT / LTE / IN / NOT_IN
```

규칙:

```text
모든 filter는 AND
NUMBER ordered comparison만 허용
BOOLEAN/STRING은 exact typed comparison
operand type mismatch는 fail-closed
rank/percentile metric은 snapshot에 동결된 RankingEvidence만 사용
동일 feature가 여러 peer group에 있으면 peer_group_id 생략 시 ambiguous FAIL
```

### Missing / invalid evidence

```text
row 없음      -> 해당 symbol 명시적 제외 / ROW_NOT_FOUND
MISSING       -> 해당 symbol 명시적 제외 / ROW_MISSING
INVALID       -> 해당 symbol 명시적 제외 / ROW_INVALID
```

0 / false / neutral default 합성은 하지 않는다.

### Ordering / top-N

두 방식만 허용한다.

```text
1. 이미 동결된 RANK/PERCENTILE evidence 정렬
2. 이미 동결된 numeric VALUE 정렬
```

VALUE 정렬은 selection ordering일 뿐 snapshot ranking evidence를 새로 만들거나 수정하지 않는다.

Tie-break:

```text
동일 sort value -> symbol ASC
```

`top_n`은 explicit sort가 있을 때만 허용한다.

### CandidateSet v1

```text
schema = axis2_candidate_set/v1
selection identity/hash
snapshot identity/hash
as_of/cutoff/universe
source symbol count
eligible count before top-N
selected candidates + deterministic ordinal
candidate별 실제 사용 evidence/provenance
명시적 exclusions/reason
ordering contract
candidate_set_hash
```

### 대표 가능한 selection

generic feature id를 사용하므로 다음을 hardcoded 계산 없이 표현 가능하다.

```text
high-beta boolean/percentile filter
normalized Histogram threshold / rank / percentile / top-N
sector membership string filter
sector 내부 frozen rank (peer_group_id exact)
relative strength / turnover / capital-flow numeric threshold/order
EMA120 position 등 provider-precomputed deterministic feature filter
```

시장레짐/섹터강도/feature 자체의 계산은 이 엔진이 하지 않는다.

### Step 9 경계

```text
immutable Step 8 snapshot만 입력
provider/network/DB 호출 없음
AXIS 1 DSL/runtime 호출 없음
AXIS 3 CRUD/import 없음
frozen core import/수정 없음
Broker/Chart 권한 없음
```

Step 9 완료 조건:

```text
exact snapshot id/hash/as_of/cutoff binding PASS
numeric/boolean/string typed filter PASS
VALUE sort + top-N + symbol tie-break deterministic PASS
frozen RANK/PERCENTILE filter/order PASS
peer-group ambiguity fail-closed PASS
missing/invalid/absent explicit exclusion + no-default PASS
selection spec unknown/nonfinite/type mismatch fail-closed PASS
symbol_scope exact subset only PASS
CandidateSet canonical hash repeatability PASS
schema contracts PASS
AXIS1/AXIS3/provider/frozen-core import isolation PASS
Step 8 snapshot regression PASS
Step 7 Bridge regression PASS
frozen core guard PASS
focused user-local AXIS2 selection engine test PASS
```

Step 9 PASS + checkpoint 전 Step 10 시작 금지.

---

## 이후 고정 순서

```text
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
