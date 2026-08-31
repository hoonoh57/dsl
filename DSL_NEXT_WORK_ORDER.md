# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 현재 번호가 검증되기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-4 user-defined functions
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
```

---

## 5-4 현재 — user-defined functions

목표:

```text
전략 안에서 반복되는 계산식을 이름 있는 순수 함수로 선언하고
인수/local scope/return을 fail-closed로 검증한 뒤 기존 DSL 표현식으로 안전하게 inline
```

구조:

```text
사용자 DSL
 -> user-function lowering
 -> 기존 multi-output lowering
 -> 검증된 migrated Parser/Semantic/Runtime/Backtest
```

구현:

```text
axes/axis1_dsl/core/user_functions.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_user_functions.py
```

v1 문법:

```text
function centered(source, period) {
    basis = ta.sma(source, period)
    return source - basis
}

value = centered(close, 20)
```

v1 contract:

```text
strategy top-level function 선언만 허용
함수는 순수 계산만 수행
인수는 위치 인수만 허용
ordered local assignment + 마지막 return expression 허용
local은 parameter 또는 앞서 선언된 local만 참조
시장값/ctx 등 외부값은 반드시 함수 인수로 명시해서 전달
등록 builtin 함수와 다른 user function 호출 허용
함수 간 합성 허용
직접/간접 재귀 금지
함수 내부 if/loop/state/order/on_bar 등 mutation/control block 금지
호출 결과 type은 inline 후 기존 Semantic이 동일 규칙으로 검증
함수 선언 블록은 동일 line 수의 blank line으로 낮춰 downstream 오류 line 보존
```

중요 원칙:

```text
migrated parser/semantic/runtime/backtest core 직접 확장 없음
frozen core 수정 없음
user function runtime registry/eval 권한 추가 없음
함수는 실행 전에 deterministic expression으로 완전히 소거
5-5 bounded loop를 5-4에서 선행 구현하지 않음
```

5-4 완료 조건:

```text
parameter/local/return scope 정상 동작
builtin을 사용하는 user function 결과가 직접 계산과 동일
user function -> user function 합성 정상
user function 결과를 multi-output 입력으로 사용 가능
Backtest facade가 함수 정의 diagnostics 보존
중복 parameter/local, free variable, bad arity, keyword call, recursion, nested block fail-closed
downstream runtime 오류 line이 원래 DSL line 유지
new feature layer frozen-core import 없음
5-1/5-2/5-3 회귀검사 PASS
frozen core guard PASS
focused user-local user-function test PASS
```

5-4 PASS + checkpoint 전 5-5 시작 금지.

---

## 이후 고정 순서

```text
5-5 bounded loops
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
