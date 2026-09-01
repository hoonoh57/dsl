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
STATUS = READY
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

## 현재 Step 14 목표

대표 자연어 전략을 실제 end-to-end acceptance fixture로 검증한다.

```text
최근 10일 EMA120 돌파 시 기준 Histogram 기록
현재 EMA120 재돌파 + 현재 Histogram >= 기준 Histogram 후보 선별
15분봉 close > EMA120 + Histogram >= reference
MACD 상향돌파 OR JMA 상승전환 매수
수익 확보 전 EMA120 위면 JMA 하락전환 매도 금지
수익 확보 후 JMA 하락전환 매도
```

분해:

```text
Authoring Lane
 -> exact AXIS2 feature/source/context manifest 기반 structured draft validation

AXIS2 snapshot/selection
 -> precomputed breakout/reference/current comparison evidence
 -> CandidateSet

AXIS3
 -> immutable promoted Condition/Strategy exact versions
 -> deterministic run plan

Bridge
 -> candidate evidence/context + explicit market bars
 -> AXIS1 BACKTEST request

AXIS1
 -> 15m deterministic strategy execution
```

### 중요한 acceptance 규칙

- 과거 10일 universe/event 탐색은 AXIS1 DSL에서 하지 않는다.
- reference Histogram은 AXIS2/prepared evidence에서 candidate별 exact read-only context로 전달한다.
- `수익 확보`의 정확한 임계치는 자연어에 없으므로 자동 추측하지 않는다. material assumption으로 막힌 뒤 human acceptance가 있어야 한다.
- 동일 입력의 candidate order / hashes / execution trace는 반복 가능해야 한다.
- context/reference tamper는 fail-closed 해야 한다.
- 최종 예제 전용 Core 함수/shortcut을 추가하지 않는다.

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

---

## 다음 순서

```text
14 natural-language E2E acceptance                 CURRENT
15 legacy docs disposition + repo-wide compliance audit
```

Step 14 user-local PASS + checkpoint 전 Step 15 시작 금지.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
