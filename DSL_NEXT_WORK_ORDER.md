# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-6 on_tick / on_fill commit/rollback
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
STEP 5-1 COMPLETE = tuple / multi-output + destructuring user-local PASS
  -> STEP5_1_MULTI_OUTPUT_CHECKPOINT_2026-08-31.md
STEP 5-2 COMPLETE = tuple-aware generic projection user-local PASS
  -> STEP5_2_GENERIC_PROJECTION_CHECKPOINT_2026-08-31.md
STEP 5-3 COMPLETE = capability/function metadata completeness user-local PASS
  -> STEP5_3_CAPABILITY_METADATA_CHECKPOINT_2026-08-31.md
STEP 5-4 COMPLETE = user-defined functions user-local PASS
  -> STEP5_4_USER_FUNCTIONS_CHECKPOINT_2026-08-31.md
STEP 5-5 COMPLETE = bounded loops user-local PASS
  -> STEP5_5_BOUNDED_LOOPS_CHECKPOINT_2026-09-01.md
```

5-5 final user-local evidence:

```text
test_axis1_bounded_loops.py = Ran 7 / OK
test_axis1_multi_output.py = Ran 8 / OK
test_frozen_legacy_core_guard.py = Ran 1 / OK
```

---

## 5-6 현재 — on_tick / on_fill commit/rollback

목표:

```text
실시간 bar가 확정되기 전 tick/fill event로 바뀌는 state를 provisional 영역에만 보관하고
bar 확정 시 commit, 취소/재구성 시 rollback하여 마지막 확정 state를 정확히 보존
```

구조:

```text
사용자 DSL
 -> on_tick/on_fill handler extraction
 -> bounded loops
 -> user functions
 -> multi-output
 -> migrated Parser/Semantic/Runtime

live continuation:
committed state
 -> begin_bar
 -> ordered on_tick/on_fill provisional mutations
 -> commit_bar OR rollback_bar
```

구현:

```text
axes/axis1_dsl/runtime/intrabar_lifecycle.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_intrabar_lifecycle.py
```

v1 DSL 예:

```text
state peak = 0
state fill_count = 0

on_tick {
    if (tick.price > peak) {
        set peak = tick.price
    }
}

on_fill {
    set fill_count = fill_count + 1
}
```

v1 contract:

```text
on_tick/on_fill은 strategy top-level 각각 최대 1개
handler는 선언된 state만 변경
on_tick event fields = tick.price / tick.volume / tick.time
on_fill event fields = fill.price / fill.quantity / fill.side / fill.order_id / fill.time
handler 내부 = set + if/else + scalar arithmetic/comparison/boolean only
indicator/function call, order placement, provider/context access, loop 금지
state type 변경 금지
begin_bar 이후 event만 허용
모든 event mutation은 provisional
한 event 실행 실패 시 그 event 직전 provisional snapshot으로 atomic rollback
rollback_bar = 현재 bar의 모든 provisional mutation 폐기
commit_bar = provisional snapshot을 새 committed state로 승격
commit revision은 commit에서만 증가
on_fill은 같은 bar에서 앞선 on_tick provisional state를 순서대로 관찰
source line 수 보존
```

Batch policy:

```text
Step 5-6 batch backtest는 intrabar event tape를 아직 소비하지 않음
따라서 on_tick/on_fill 전략을 event tape 없이 batch backtest하면 fail-closed
침묵 무시/임의 bar-close 치환 금지
full batch/stream event parity는 Step 5-10 authority
```

중요 원칙:

```text
migrated Parser/Semantic/Runtime/Broker 직접 변경 없음
frozen core 수정 없음
실시간 indicator 재계산 권한 추가 없음
provisional state를 committed처럼 외부 노출하지 않음
5-7 partial fill을 선행 구현하지 않음
5-8 pyramiding을 선행 구현하지 않음
검증완화 금지
```

5-6 완료 조건:

```text
tick/fill ordered provisional mutation 정상
committed state는 commit 전 불변
rollback 후 exact committed snapshot 복원
commit 후 새 snapshot과 revision 확정
failed event atomic rollback
state coverage/type mismatch fail-closed
wrong event field/free variable/call/undeclared target fail-closed
bar lifecycle 순서 위반 fail-closed
batch backtest no-event-tape fail-closed
기존 5-1~5-5 facade 회귀검사 PASS
frozen core guard PASS
focused user-local intrabar lifecycle test PASS
```

5-6 PASS + checkpoint 전 5-7 시작 금지.

---

## 이후 고정 순서

```text
5-7 partial fills / partial exits
5-8 pyramiding / multi-position accounting
5-9 full reference differential fixtures
5-10 full-engine batch/streaming parity
6 AXIS 1 machine-readable capability/diagnostic registry
7 Bridge common + AXIS 1 execution contract
8 AXIS 2 exact-as-of snapshot contract
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
검증된 migrated core를 신규기능 때문에 불필요하게 흔들지 않음
새 기능은 가능한 한 명시적 contract + lowering/facade로 격리
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
