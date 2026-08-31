# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-5 bounded loops
SUBSTEP_STATUS = REMOTE_RETEST_REQUIRED
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
```

---

## 5-5 현재 — bounded loops

목표:

```text
반복 횟수가 compile 전에 확정되는 순수 반복 계산만 허용하고
runtime에 동적 loop 권한이나 무한반복 가능성을 추가하지 않음
```

구조:

```text
사용자 DSL
 -> bounded-loop compile-time lowering
 -> user-function lowering
 -> multi-output lowering
 -> 검증된 migrated Parser/Semantic/Runtime/Backtest
```

구현:

```text
axes/axis1_dsl/core/bounded_loops.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_bounded_loops.py
```

v1 contract:

```text
bounded loop는 user-defined function 내부에서만 허용
range 인수는 compile-time 정수 상수만 허용
Python range와 같은 start/stop/step 의미
최대 반복 횟수 = 64
step=0 금지
loop index는 read-only
loop target은 앞에서 선언된 function local accumulator만 허용
parameter mutation 금지
nested loop / if / return / state / order 등 loop 내부 control/mutation 확장 금지
loop는 compile-time expression으로 완전히 소거
runtime loop 없음
source line 수를 보존하여 downstream 오류 line 유지
전개식이 과도하게 커지면 fail-closed
```

최근 user-local 검증:

```text
test_axis1_bounded_loops.py = Ran 7 / 1 failure
나머지 5-4/5-3/5-2/5-1 회귀검사와 frozen core guard = OK
```

원인 분류:

```text
FEATURE_DEFECT — bounded-loop 자체가 아니라 기존 5-1 ta.bbands multi-output lowering의 NaN-window parity 결함
```

근거:

```text
bounded loop가 만든 mean3 series는 앞쪽 2개 bar가 NaN
CoreTALib.bbands는 period window 안에 NaN이 하나라도 있으면 band 전체를 NaN으로 유지
기존 ta.bbands lowering은 ta.sma + ta.stdev 조합이어서 stdev의 NaN 정책 차이 때문에 2개 bar를 너무 일찍 materialize
```

조치:

```text
migrated core/frozen core/assertion 변경 없음
multi-output lowering에서 기존 DSL primitive만 사용해 period 연속 finite input이 모일 때까지 NaN window를 보존
multi-output 회귀검사에 warmup/NaN-window case 추가
```

5-5 완료 조건:

```text
고정 range accumulator 결과가 수동 history expression과 동일
step range와 복수 accumulator 결정적 동작
bounded-loop function 결과를 기존 multi-output 입력으로 사용 가능
Backtest diagnostics에 loop contract 보존
내부 helper가 실행 output/projection에 노출되지 않음
dynamic bound / 초과 반복 / zero step / scope 위반 / parameter mutation / nested block fail-closed
source line count와 downstream 오류 line 보존
5-1~5-4 회귀검사 PASS
frozen core guard PASS
focused user-local bounded-loop test PASS
```

5-5 PASS + checkpoint 전 5-6 시작 금지.

---

## 이후 고정 순서

```text
5-6 on_tick / on_fill commit/rollback
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
