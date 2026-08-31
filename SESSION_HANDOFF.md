# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 9 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> AXIS 1은 single-instrument deterministic execution, AXIS 2는 immutable point-in-time evidence 기반 selection을 담당한다. 축간 연결은 versioned Request -> Response 계약으로만 수행한다.

---

## 현재 작업

```text
CURRENT_STEP = 9
CURRENT_SUBSTEP = 9-1 deterministic snapshot filter / rank / top-N + CandidateSet v1
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
```

최근 checkpoint:

```text
STEP8_AXIS2_EXACT_ASOF_SNAPSHOT_CHECKPOINT_2026-09-01.md
```

Step 8 user-local evidence:

```text
test_axis2_exact_asof_snapshot.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 9 구현

구현:

```text
axes/axis2_selection/engine/selection.py
axes/axis2_selection/engine/selection_spec.v1.schema.json
axes/axis2_selection/engine/candidate_set.v1.schema.json
tests/test_axis2_selection_engine.py
```

### 데이터 흐름

```text
provider/precompute
 -> Step 8 immutable PointInTimeSnapshot
 -> Step 9 SelectionSpec
 -> deterministic filter/order/top-N
 -> CandidateSet
```

Step 9는 feature 계산기가 아니다.

### Filter

```text
metric = VALUE | RANK | PERCENTILE
operator = EQ | NE | GT | GTE | LT | LTE | IN | NOT_IN
모든 filters = AND
```

Typed exact comparison을 사용한다.

```text
NUMBER ordered comparison
BOOLEAN exact bool
STRING exact string
```

### Ranking / ordering

```text
RANK/PERCENTILE = snapshot에 이미 동결된 RankingEvidence만 사용
VALUE = snapshot에 이미 동결된 numeric value로 deterministic ordering만 수행
```

VALUE ordering을 새로운 cross-sectional rank evidence라고 주장하지 않는다.

동점은 symbol ASC로 고정한다. top-N은 sort 계약 없이는 허용하지 않는다.

### Missing / invalid

```text
ROW_NOT_FOUND
ROW_MISSING
ROW_INVALID
```

해당 symbol은 explicit exclusion으로 기록하고 0/false/neutral 값을 합성하지 않는다.

### Snapshot binding

SelectionSpec가 다음을 exact 고정한다.

```text
snapshot_id
snapshot_hash
as_of
knowledge_cutoff
```

하나라도 다르면 selection 실행 자체를 거부한다.

### Peer group

동일 feature의 rank가 MARKET / HIGH_BETA / SECTOR:* 등 여러 peer group으로 존재할 수 있다.

```text
peer_group_id exact 지정 가능
생략했는데 후보 row가 여러 개면 AMBIGUOUS_FEATURE fail-closed
```

### CandidateSet

반환값은 다음을 포함한다.

```text
selection/snapshot identity
source symbol count
eligible-before-top-N count
selected symbol + ordinal
실제 사용한 feature/rank/provenance evidence
제외된 symbol + reason
ordering contract
canonical candidate_set_hash
```

### 현재 대표 가능 사용례

```text
high-beta filter
normalized Histogram top-N / percentile
sector membership filter
sector 내 frozen rank
relative strength / turnover / capital-flow threshold/order
provider-precomputed EMA120 position filter
```

### 금지

```text
selection 요청 중 provider 계산
AXIS 1 DSL로 종목별 feature 재계산
nearest-time / fill-forward / default synthesis
AXIS 3 내부 상태 direct import
frozen core import/수정
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
9 AXIS 2 selection engine                    CURRENT
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
python -m unittest discover -s tests -p "test_axis2_selection_engine.py" -v
python -m unittest discover -s tests -p "test_axis2_exact_asof_snapshot.py" -v
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 9 checkpoint 후 Step 10 AXIS 3 Condition / Strategy CRUD + orchestration으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
