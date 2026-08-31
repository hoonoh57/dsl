# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-9 full reference differential fixtures
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
STEP 5-6 COMPLETE = on_tick/on_fill commit/rollback user-local PASS
  -> STEP5_6_INTRABAR_LIFECYCLE_CHECKPOINT_2026-09-01.md
STEP 5-7 COMPLETE = partial fills / partial exits user-local PASS
  -> STEP5_7_PARTIAL_EXECUTION_CHECKPOINT_2026-09-01.md
STEP 5-8 COMPLETE = pyramiding / multi-position accounting user-local PASS
  -> STEP5_8_PYRAMIDING_EXECUTION_CHECKPOINT_2026-09-01.md
```

5-8 user-local evidence:

```text
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_axis1_intrabar_lifecycle.py = OK
test_axis1_broker_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 5-9 현재 — full reference differential fixtures

목표:

```text
AXIS 1 TA/user indicator 계산을 frozen core와의 단순 복제 비교가 아니라
독립된 test-side NumPy 기준 구현과 대량 differential 비교하여
수식/warmup/NaN/event-history/runtime mapping drift를 조기에 검출
```

구현:

```text
tests/axis1_reference_indicators.py
tests/test_axis1_reference_differential.py
```

Reference isolation:

```text
reference fixture는 axes.axis1_dsl 또는 frozen core를 import하지 않음
NumPy + 명시적 수식/상태전이만 사용
production 구현을 호출해서 expected를 만들지 않음
```

검증 범위:

```text
moving/rolling:
  shift, sma, ema, rma, wma, ma, highest, lowest, rolling sum, stdev, roc

recursive/trend:
  true range, ATR, RSI, MACD, TRIX, CCI, ADX, JMA, Supertrend

range/event history:
  nrange, Williams %R, abs range, sum abs return, VHF
  crossover/crossunder, bars_since, count_since, highest_since, lowest_since, value_when

multi-output/user:
  BBands upper/middle/lower
  Supertrend line/direction
  normalized MACD macd/signal/hist/hist_abs_pct

runtime mapping:
  등록된 모든 ta/user FUNCTION_SPECS가 explicit differential coverage set에 포함
  DSL Runtime facade로 실제 함수 호출 결과도 reference와 비교
```

Fixture matrix:

```text
결정적 비선형 가격/고가/저가/거래량 series
복수 period = 2/3/5/8/14/21
NaN warmup + 중간 NaN fixture
flat/zero-range edge fixture
JMA phase/length/power 여러 조합
Supertrend period/multiplier 여러 조합
normalized MACD simple/exponential/weighted 조합
```

중요 원칙:

```text
Step 5-9는 검증 확장 단계이며 production indicator/runtime 로직을 임의 변경하지 않음
차이가 발견되면 먼저 reference defect / product defect / authority drift로 분류
expected/tolerance를 결과에 맞춰 완화하지 않음
reference implementation이 production module을 import하면 FAIL
frozen core 수정 없음
Step 5-10 batch/stream parity 선행 구현 금지
```

5-9 완료 조건:

```text
독립 reference import isolation PASS
registered ta/user surface coverage completeness PASS
core indicator family differential PASS
복수 period matrix PASS
NaN/flat edge fixture PASS
JMA/Supertrend/BBands state/reference PASS
normalized MACD component/method matrix PASS
actual DSL runtime mapping differential PASS
multi-output lowering differential PASS
기존 5-1~5-8 핵심 회귀검사 PASS
frozen core guard PASS
focused user-local reference differential test PASS
```

5-9 PASS + checkpoint 전 5-10 시작 금지.

---

## 이후 고정 순서

```text
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
새 기능은 가능한 한 명시적 contract + 격리된 facade/session으로 추가
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
