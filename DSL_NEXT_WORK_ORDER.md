# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 현재 번호가 검증되기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-1 tuple / multi-output typed return + destructuring
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
  -> STEP4_BOUNDARY9_BACKTEST_PROJECTION_PARITY_CHECKPOINT_2026-08-31.md
```

Step 4 최종 상태:

```text
1 Parser / AST                         PASS
2 Function Registry                    PASS
3 Assignment Flow + Semantic           PASS
4 Indicator Kernel                     PASS
5 State + Bar Runtime                  PASS
6 MTF + Read-Only Context Binding      PASS
7 DSL Runtime                          PASS
8 Broker                               PASS
9 Backtest + Projection Output         PASS
```

Boundary 9 첫 재검증 실패 2건은 legacy에서도 금지된 close-order 인수를 사용한 TEST_DEFECT였고, fixture만 정상 문법으로 수정한 뒤 user-local PASS했다. Product/core/assertion 완화는 없었다.

---

## 5-1 현재 — multi-output + destructuring

사용자 우려에 따라 신규 기능은 검증된 migration core를 자주 뜯어고치지 않는다.

```text
사용자 DSL 신규문법
 -> fail-closed typed lowering
 -> 검증된 migrated Parser/Semantic/Runtime/Backtest
```

즉, **기존 실행 core는 안정된 장비처럼 유지하고 신규 문법은 얇은 compiler lowering 층에서 수용**한다.

현재 구현:

```text
axes/axis1_dsl/core/multi_output.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_multi_output.py
```

지원 v1:

```text
line, direction = ta.supertrend([period, multiplier])
upper, middle, lower = ta.bbands(series[, period, multiplier])
macd, signal, hist, strength = user.macd_normalized_all(series[, short, long, signal, method])
```

규칙:

```text
multi-output는 strategy top-level 선언만 허용
등록된 multi-output 함수만 허용
반환 component 수와 대상 변수 수 exact 일치
component type을 명시적으로 등록
중복/예약 이름 fail-closed
v1 multi-output 호출은 위치 인수만 허용
lowering 뒤 기존 semantic/runtime 검증을 다시 통과해야 함
frozen core import/수정 없음
```

5-1 완료 조건:

```text
3개 등록 multi-output 함수의 component 결과가 기존 kernel/component 결과와 동일
destructuring 결과를 후속 조건식에서 정상 사용
잘못된 arity/함수/대상/인수 방식 fail-closed
backtest facade가 destructuring을 소비
multi-output typed metadata 보존
new additive modules에 frozen core import 없음
frozen core guard PASS
user-local focused test PASS
```

5-1 PASS + checkpoint 전 5-2 시작 금지.

---

## 이후 고정 순서

```text
5-2 tuple-aware generic projection
5-3 capability/function metadata completeness
5-4 user-defined functions
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
