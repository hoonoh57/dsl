# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 14
CURRENT_STEP_NAME = Final natural-language E2E acceptance
CURRENT_SUBSTEP = 14-1 representative natural-language authoring -> exact PIT selection -> promoted strategy -> AXIS1 execution trace
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1~12 COMPLETE = USER-LOCAL PASS
STEP 13 COMPLETE = Continuous Improvement analysis tooling user-local PASS
  -> STEP13_CONTINUOUS_IMPROVEMENT_CHECKPOINT_2026-09-01.md
```

Step 13 user-local evidence:

```text
test_authoring_continuous_improvement.py = OK
test_external_llm_authoring_lane.py = OK
test_three_axis_e2e_bridge.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 14 현재 — Final natural-language E2E acceptance

대표 자연어 목표:

```text
최근 10일 EMA120 돌파 + 기준 Histogram 강도 증거
현재 EMA120 재돌파 + 기준 이상 Histogram 후보 선별
15분봉 close > EMA120 + Histogram >= reference
MACD 상향돌파 OR JMA 상승전환 매수
수익 확보 전 EMA120 위에서는 JMA 하락전환 매도 억제
수익 확보 후 JMA 하락전환 매도
```

### 구현

```text
acceptance/__init__.py
acceptance/final_natural_language_scenario.py
tests/test_final_natural_language_e2e.py
```

Step 14 final acceptance 과정에서 발견된 generic Bridge preflight gap을 좁게 보강했다.

```text
bridges/axis1_execution_bridge.py
bridges/three_axis_e2e_bridge.py
```

변경 의미:

```text
prepared parent-context binding hash를 non-executing preflight에서 검증
모든 selected candidate의 context integrity 검증이 끝난 뒤에만 첫 AXIS1 실행 시작
후순위 후보 context tamper로 일부 후보만 먼저 실행되는 상태 차단
```

AXIS 1 DSL/지표/Backtest 계산 로직, AXIS 2 selection semantics, AXIS 3 CRUD semantics, frozen core는 변경하지 않았다.

### 대표 시나리오 권한 분해

```text
Authoring Lane
 -> 자연어 원문을 prompt에 그대로 보존
 -> structured draft strict validation
 -> '수익확보' 수치가 원문에 없으므로 +2% material assumption으로 human approval 전 BLOCKED
 -> 명시 승인 후 ACCEPTED_DRAFT

AXIS 2
 -> 최근 10일 EMA120 breakout 여부
 -> 현재 EMA120 re-breakout 여부
 -> current Histogram >= reference 여부
 -> reference Histogram numeric value
 -> normalized Histogram frozen rank
 위 값을 모두 precomputed exact PIT snapshot evidence로 소비
 -> filter/rank/top-N -> AAA, BBB

AXIS 3
 -> exact SelectionSpec를 Condition immutable version으로 저장
 -> accepted draft의 exact DSL을 Strategy immutable version으로 저장
 -> 둘 다 PROMOTED exact version/hash로 run plan 생성

Bridge / AXIS 1
 -> candidate별 snapshot reference Histogram을 exact read-only ctx.selection.reference_hist로 전달
 -> 15m EMA120 + normalized Histogram + MACD + JMA + state permission strategy 실행
```

### DSL acceptance state logic

대표 strategy는 product Core shortcut 없이 기존 범용 DSL만 조합한다.

```text
entry_setup = close > EMA120
              AND hist_strength >= reference_hist
              AND (MACD turn-up OR JMA turn-up)

in_trade / entry_price / profit_secured = explicit on_bar state

JMA turn-down AND profit 미확보 AND close > EMA120
 -> exit_blocked_now

JMA turn-down AND (profit 확보 OR close <= EMA120)
 -> exit_now
```

Acceptance market fixture는 EMA120 warmup 이후 다음 순서를 의도적으로 만든다.

```text
entry
 -> +2% 미만 JMA turn-down / exit blocked
 -> +2% profit secured
 -> JMA turn-down / exit allowed
```

### Step 14 완료 조건

```text
verbatim natural-language prompt preservation PASS
material assumption human gate PASS
accepted draft full deterministic validation PASS
AXIS2 precomputed PIT feature separation PASS
exact snapshot/spec hash/as_of/cutoff binding PASS
expected CandidateSet AAA/BBB + deterministic ordinal PASS
reference Histogram candidate evidence == AXIS1 prepared context value PASS
context binding hash/registry trace PASS
promoted Strategy/Condition exact version/hash PASS
AXIS1 entry + pre-profit blocked-exit + post-profit exit signals PASS
closed profitable trade + flat final position PASS
same request -> same E2E request/response hash PASS
context value tamper without matching binding hash -> before first AXIS1 execution REJECTED PASS
no provider/nearest/fill-forward/universe lookup inside AXIS1 DSL PASS
Step 13/12/11 regressions PASS
frozen core guard PASS
focused user-local Step 14 test PASS
```

Step 14 PASS + checkpoint 전 Step 15 시작 금지.

---

## 이후 고정 순서

```text
15 Legacy docs disposition + repo-wide compliance audit
```

---

## 절대 원칙

```text
frozen legacy core 수정 금지
AXIS 1 = single-instrument deterministic execution
AXIS 2 = immutable PIT selection semantics
AXIS 3 = versioned Condition/Strategy lifecycle + orchestration
External LLM = proposal only
Continuous Improvement = evidence analysis only, automatic mutation 없음
축간 연결 = versioned Request -> Response only
future value / nearest-time / fill-forward / default synthesis 금지
특정 최종 예제를 위한 Core shortcut 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
