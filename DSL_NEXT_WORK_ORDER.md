# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-10 full-engine batch/streaming parity
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
STEP 5-1 COMPLETE = tuple / multi-output + destructuring user-local PASS
STEP 5-2 COMPLETE = tuple-aware generic projection user-local PASS
STEP 5-3 COMPLETE = capability/function metadata completeness user-local PASS
STEP 5-4 COMPLETE = user-defined functions user-local PASS
STEP 5-5 COMPLETE = bounded loops user-local PASS
STEP 5-6 COMPLETE = on_tick/on_fill commit/rollback user-local PASS
STEP 5-7 COMPLETE = partial fills / partial exits user-local PASS
STEP 5-8 COMPLETE = pyramiding / multi-position accounting user-local PASS
STEP 5-9 COMPLETE = full reference differential fixtures user-local PASS
  -> STEP5_9_REFERENCE_DIFFERENTIAL_CHECKPOINT_2026-09-01.md
```

5-9 user-local evidence:

```text
test_axis1_reference_differential.py = OK
test_axis1_indicator_parity.py = OK
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 5-10 현재 — full-engine batch/streaming parity

목표:

```text
같은 causal market 입력과 같은 ordered event tape에 대해
batch 계산과 bar/event 순차 입력 결과가 상태/신호/체결/손익 수준에서 동일함을 한 검증 계약으로 묶는다.
```

구현:

```text
axes/axis1_dsl/execution/full_engine_parity.py
tests/test_axis1_full_engine_parity.py
```

### A. Runtime causal-prefix parity

```text
full market 1회 batch compile
vs
1 bar -> 2 bars -> ... -> N bars prefix compile
```

매 prefix마다 다음을 exact 비교한다.

```text
모든 ndarray runtime value
NaN/warmup 위치
JMA 등 trend metadata
on_bar state output
MTF confirmed output
multi-output result
이벤트 condition
주문 argument series/scalar
```

이 방식은 성능 최적화용 incremental kernel이 아니라 **correctness oracle**이다. 미래 bar가 과거 값을 바꾸는지 직접 검출한다.

### B. Backtest prefix parity

```text
full batch backtest
vs
동일 데이터를 2..N bar prefix로 반복 replay
```

비교:

```text
equity curve
execution/trade records
closed trades
broker lifecycle history
open-position state
closed-trade count
```

prefix 끝을 인위적 세션 종료로 오인하지 않도록 이 parity fixture는 market/GTC lifecycle을 사용한다.

### C. Ordered intrabar/execution event-tape parity

기존 Step 5-6/5-7/5-8 session을 하나의 ordered tape consumer로 묶는다.

```text
BEGIN_BAR
TICK
SUBMIT_ENTRY / SUBMIT_EXIT
FILL
CANCEL
COMMIT_BAR / ROLLBACK_BAR
```

동일 tape를:

```text
전체 sequence replay
vs
event 1개씩 streaming apply
```

하여 exact final snapshot과 event result를 비교한다.

권위 분리:

```text
실제 broker/accounting fill fact는 authoritative
strategy intrabar provisional state rollback은 fill fact를 되돌리지 않음
```

### 경계

```text
migrated runtime/backtest/broker core 직접 수정 없음
frozen legacy core 수정 없음
prefix replay 검증을 성능 좋은 실시간 incremental engine이라고 과장하지 않음
Axis1BacktestEngine에 intrabar tape를 침묵 삽입하지 않음
batch/stream parity는 동일 입력/동일 event ordering에서만 주장
```

5-10 완료 조건:

```text
runtime 모든 causal prefix exact parity PASS
state + MTF + multi-output + event condition parity PASS
batch backtest equity/trade/broker lifecycle prefix parity PASS
intrabar + partial fill + pyramiding ordered tape batch/stream parity PASS
rollback 후 strategy state와 execution fact authority separation PASS
new parity layer frozen-core import 없음
5-9 reference differential 회귀 PASS
5-8/5-7 execution 회귀 PASS
frozen core guard PASS
focused user-local full-engine parity test PASS
```

5-10 PASS + checkpoint 전 Step 6 시작 금지.

---

## 이후 고정 순서

```text
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
새 기능은 가능한 한 명시적 contract + 격리된 facade/session으로 추가
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
