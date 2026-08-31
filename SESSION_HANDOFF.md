# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-6 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 DSL 기능은 가능한 한 명시적 contract + 얇은 compile-time lowering/facade 또는 별도 runtime session으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-6 on_tick / on_fill commit/rollback
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
Step 5-1 multi-output + destructuring = COMPLETE / USER-LOCAL PASS
Step 5-2 tuple-aware generic projection = COMPLETE / USER-LOCAL PASS
Step 5-3 capability/function metadata = COMPLETE / USER-LOCAL PASS
Step 5-4 user-defined functions = COMPLETE / USER-LOCAL PASS
Step 5-5 bounded loops = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_5_BOUNDED_LOOPS_CHECKPOINT_2026-09-01.md
```

5-5 final evidence:

```text
test_axis1_bounded_loops.py = Ran 7 / OK
test_axis1_multi_output.py = Ran 8 / OK
test_frozen_legacy_core_guard.py = Ran 1 / OK
```

5-5 검증 중 발견된 BBands multi-output NaN component semantics 결함도 direct CoreTALib.bbands 비교를 유지한 채 수정되어 최종 PASS했다.

---

## 현재 5-6 구현

목표:

```text
open bar에서 발생하는 tick/fill 기반 state 변경을 provisional transaction으로 격리하고
bar 확정 전에는 committed state를 바꾸지 않음
```

구현 파일:

```text
axes/axis1_dsl/runtime/intrabar_lifecycle.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_intrabar_lifecycle.py
```

Lowering/실행 경계:

```text
on_tick/on_fill handler extraction
 -> bounded loops
 -> user functions
 -> multi-output
 -> migrated Parser/Semantic/Runtime

compiled history의 마지막 state
 -> Axis1DSLRuntime.open_intrabar_session
 -> begin_bar
 -> on_tick / on_fill ...
 -> commit_bar | rollback_bar
```

v1 handler contract:

```text
on_tick/on_fill 각각 최대 하나
선언된 strategy state만 set 가능
if/else 허용
함수 호출/indicator/order/context/provider/loop 금지
state type 변경 금지
```

Event fields:

```text
on_tick: tick.price, tick.volume, tick.time
on_fill: fill.price, fill.quantity, fill.side, fill.order_id, fill.time
```

Transaction semantics:

```text
begin_bar에서 committed -> provisional 복사
on_tick/on_fill은 provisional만 순서대로 변경
각 event는 atomic: 실행 실패 시 그 event 직전 provisional로 복구
rollback_bar는 현재 bar 전체 provisional 변경 폐기
commit_bar는 provisional을 committed로 승격하고 revision +1
rollback은 revision을 증가시키지 않음
commit/rollback 후 다음 begin_bar 전 event 실행 금지
```

중요 정책:

```text
batch backtest는 Step 5-6에서 intrabar event tape를 아직 소비하지 않는다.
on_tick/on_fill 전략을 batch backtest가 조용히 무시하면 잘못된 결과가 되므로 event tape 없이 호출 시 fail-closed한다.
full batch/stream event parity는 Step 5-10에서 검증한다.
```

기존 migrated parser/semantic/runtime/broker와 frozen legacy core는 직접 수정하지 않았다.

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
새 feature를 frozen core에 역이식
intrabar handler에서 order placement/indicator recomputation/provider access 추가
provisional state를 committed state처럼 취급
5-7 partial fills 선행 구현
5-8 pyramiding 선행 구현
검증완화
```

---

## 다음 순서

```text
5-6 on_tick / on_fill commit/rollback       CURRENT
5-7 partial fills / partial exits
5-8 pyramiding / multi-position
5-9 reference differential fixtures
5-10 full-engine batch/streaming parity
6 machine-readable capability/diagnostic registry
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
python -m unittest discover -s tests -p "test_axis1_intrabar_lifecycle.py" -v
python -m unittest discover -s tests -p "test_axis1_bounded_loops.py" -v
python -m unittest discover -s tests -p "test_axis1_user_functions.py" -v
python -m unittest discover -s tests -p "test_axis1_multi_output.py" -v
python -m unittest discover -s tests -p "test_axis1_generic_projection.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-6 checkpoint 후 5-7 partial fills / partial exits로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
