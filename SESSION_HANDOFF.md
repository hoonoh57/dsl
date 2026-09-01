# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 14 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 세 축의 계산 권한을 섞지 않는다. External LLM은 proposal-only이며, 모든 연결은 exact versioned data contract를 사용한다.

---

## 현재 작업

```text
CURRENT_STEP = 14
CURRENT_SUBSTEP = 14-1 representative natural-language authoring -> exact PIT selection -> promoted strategy -> AXIS1 execution trace
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1~12 = COMPLETE / USER-LOCAL PASS
Step 13 Continuous Improvement analysis tooling = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP13_CONTINUOUS_IMPROVEMENT_CHECKPOINT_2026-09-01.md
```

Step 13 user-local evidence:

```text
test_authoring_continuous_improvement.py = OK
test_external_llm_authoring_lane.py = OK
test_three_axis_e2e_bridge.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 14 구현

구현:

```text
acceptance/final_natural_language_scenario.py
tests/test_final_natural_language_e2e.py
```

보강:

```text
bridges/axis1_execution_bridge.py
bridges/three_axis_e2e_bridge.py
```

### 최종 자연어 시나리오

```text
최근 10일 EMA120 breakout + 기준 Histogram evidence
현재 EMA120 re-breakout + current Histogram >= reference 후보 선별
15m close > EMA120 + hist >= reference
MACD upward crossover OR JMA turn-up entry
profit 확보 전 EMA120 위 JMA turn-down exit block
profit 확보 후 JMA turn-down exit
```

`수익확보` 수치는 원문에 없으므로 silent guess하지 않는다.

```text
material assumption A1 = 매수 신호 종가 대비 +2.0%
승인 전 = BLOCKED_USER_CLARIFICATION
명시 승인 후 = ACCEPTED_DRAFT
```

### AXIS 2 표현

과거 10일 event 검색을 AXIS1에 넣지 않는다. 다음은 이미 계산된 exact PIT snapshot evidence다.

```text
selection.ema120_breakout_within_10d
selection.current_ema120_rebreakout
selection.current_hist_ge_reference
selection.reference_hist
selection.hist_normalized + frozen HIGH_BETA rank
```

대표 snapshot에서 filter + rank + top-N 결과는 `AAA`, `BBB` 순서다.

### AXIS 1 전략

기존 범용 기능만 조합한다.

```text
ta.ema(close, 120)
user.macd_normalized(... macd/signal/hist_abs_pct ...)
ta.jma
state.edge / state.falling_edge
ctx.selection.reference_hist
on_bar persistent state
order.buy / order.close_long
```

fixture는 다음 실행상태를 만든다.

```text
entry
 -> profit 2% 미확보 상태에서 JMA down + EMA120 위 / exit blocked
 -> profit secured
 -> JMA down / exit
 -> profitable closed trade / flat
```

### Evidence -> context

CandidateSet에 실제 사용한 `selection.reference_hist` evidence가 남고, 해당 numeric value를 candidate별 exact read-only parent context vector로 만든다.

AXIS1 diagnostics에 다음이 남는다.

```text
target symbol
frame hash
registry/manifest hash
binding hash
feature id
bar count
```

### Step 14에서 발견한 Bridge preflight gap

기존 Step 11은 모든 AXIS1 request shape를 사전검사했지만 prepared context `binding_hash` 무결성은 실제 AXIS1 호출 시 확인했다.

이를 generic Bridge 계층에서 보강했다.

```text
preflight_axis1_request()
 -> request/market/context binding integrity 확인
 -> 모든 selected candidate preflight 완료
 -> 그 후 첫 AXIS1 execution 시작
```

따라서 후순위 후보 context가 변조되어도 앞 후보만 먼저 실행되는 partial pipeline이 생기지 않는다.

### 경계 유지

```text
frozen core 수정 없음
AXIS1 지표/DSL/Backtest 계산식 수정 없음
AXIS2 selection 의미 수정 없음
AXIS3 CRUD 의미 수정 없음
최종 예제 전용 production shortcut 없음
provider/network/nearest/fill-forward 없음
```

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_final_natural_language_e2e.py" -v
python -m unittest discover -s tests -p "test_three_axis_e2e_bridge.py" -v
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_external_llm_authoring_lane.py" -v
python -m unittest discover -s tests -p "test_authoring_continuous_improvement.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 14 checkpoint 후 마지막 Step 15 legacy docs disposition + repo-wide compliance audit로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
