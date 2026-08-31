# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 6 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 기능/검증/registry는 가능한 한 별도 계층으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 6
CURRENT_SUBSTEP = 6-1 canonical capability + diagnostic registry
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
Step 5 AXIS 1 신규 DSL 기능 개발/검증 = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_10_FULL_ENGINE_PARITY_CHECKPOINT_2026-09-01.md
```

5-10 user-local evidence:

```text
test_axis1_full_engine_parity.py = OK
test_axis1_reference_differential.py = OK
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 6 구현

구현 파일:

```text
axes/axis1_dsl/core/capability_diagnostic_registry.py
tests/test_axis1_capability_diagnostic_registry.py
```

목표:

```text
AXIS 1 기능 지원여부/경계/권위/검증근거와
진단값 producer/path/authority/shape를
하나의 deterministic machine-readable snapshot으로 제공
```

Step 5-3의 함수 metadata를 복사해 별도 truth를 만들지 않고 직접 집계한다.

Function registry:

```text
모든 single-output capability metadata
모든 multi-output capability metadata
output name/type
lookback/warmup/NaN policy
causality/reference source
incremental identity certification 상태
```

Feature registry:

```text
dsl.multi_output
dsl.user_functions
dsl.bounded_loops
runtime.parent_context
runtime.mtf_confirmed
runtime.intrabar_state
execution.partial_fills
execution.pyramiding
projection.generic
verification.reference_differential
verification.batch_stream_parity
```

Negative/boundary 상태도 숨기지 않는다.

```text
execution.hedging = NOT_SUPPORTED
runtime.optimized_incremental_kernel = NOT_CERTIFIED
verification capability = VERIFICATION_ONLY
```

Diagnostic registry:

```text
batch signal/rejection/broker history
parent-context/entry-policy
bounded-loop/user-function/multi-output/projection facade diagnostics
intrabar audit
partial execution snapshot
pyramiding lot snapshot
runtime/backtest parity reports
```

Registry snapshot:

```text
schema = axis1_capability_diagnostic_registry/v1
sorted deterministic manifest
SHA-256 registry_hash
unknown capability/diagnostic = fail-closed
require_supported = product execution support만 허용
```

중요 경계:

```text
registry module은 execution/runtime/indicator/provider를 import하지 않음
계산/체결/지표 재계산 권한 없음
frozen core import/수정 없음
Step 7 Bridge contract 선행 구현 없음
```

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정 / 이동 / 삭제 / 신규 파일 추가
expected frozen hash 변경으로 위반 수용
registry에서 uncertified 기능을 supported로 임의 승격
registry가 execution kernel을 호출하거나 값을 다시 계산
검증완화
```

---

## 다음 순서

```text
6 machine-readable capability/diagnostic registry   CURRENT
7 Bridge common + AXIS 1 execution contract
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

## 사용자 커뮤니케이션 / 콘솔

```text
사용자 화면 = 한 일 / 할 일
정상 콘솔 = 가능하면 [PASS] 한 줄
실패 콘솔 = 디버깅에 필요한 최소 원인/위치
기계용 상세정보 = 내부 관리
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis1_capability_diagnostic_registry.py" -v
python -m unittest discover -s tests -p "test_axis1_capability_metadata.py" -v
python -m unittest discover -s tests -p "test_axis1_full_engine_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 6 checkpoint 후 Step 7 Bridge common + AXIS 1 execution contract로 이동한다.

실패 시 test defect / product defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
