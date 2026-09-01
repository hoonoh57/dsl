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
SUBSTEP_STATUS = READY
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 migration user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능/검증 user-local PASS
STEP 6 COMPLETE = capability/diagnostic registry user-local PASS
STEP 7 COMPLETE = Bridge common + AXIS 1 execution contract user-local PASS
STEP 8 COMPLETE = AXIS 2 exact-as-of snapshot contract user-local PASS
STEP 9 COMPLETE = AXIS 2 deterministic selection engine user-local PASS
STEP 10 COMPLETE = AXIS 3 Condition/Strategy CRUD + orchestration user-local PASS
STEP 11 COMPLETE = three-axis versioned E2E Bridge user-local PASS
STEP 12 COMPLETE = External LLM Authoring Lane user-local PASS
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

대표 자연어 목표를 실제 분리 권한으로 끝까지 검증한다.

```text
최근 10일 EMA120 돌파 + 기준 Histogram 강도 증거
현재 EMA120 재돌파 + 기준 이상 Histogram 후보 선별
15분봉 close > EMA120 + Histogram >= reference
MACD 상향돌파 OR JMA 상승전환 매수
수익 확보 전 EMA120 위에서는 JMA 하락전환 매도 억제
수익 확보 후 JMA 하락전환 매도
```

### 고정 권한 분해

```text
Authoring Lane = 자연어 -> untrusted structured draft -> deterministic validation only
AXIS 2 precompute/snapshot = 과거 10일 event/reference/current comparison을 exact PIT evidence로 공급
AXIS 2 selection = snapshot filter/rank/top-N만 수행
AXIS 3 = exact Condition/Strategy version + lifecycle + run plan
Bridge = CandidateSet/RunPlan/context/execution data를 versioned contract로 연결
AXIS 1 = 15m single-symbol strategy 계산/실행
Chart/acceptance = 계산 재수행 없이 trace/projection/evidence 확인
```

AXIS 1이 universe/history cross-symbol search를 하지 않고, AXIS 2가 주문/DSL을 실행하지 않으며, AXIS 3이 선별 계산을 재구현하지 않는 상태가 유지되어야 한다.

### Step 14 핵심 acceptance

```text
1. representative natural-language request가 Authoring prompt에 verbatim 보존
2. material ambiguity는 human acceptance 전 blocked
3. accepted structured draft가 현재 registry/feature/source/context/DSL contract를 모두 PASS
4. 과거 breakout/reference/current re-breakout은 AXIS2 snapshot의 precomputed exact PIT evidence로 표현
5. SelectionSpec가 snapshot id/hash/as_of/cutoff에 exact binding
6. CandidateSet이 의도한 종목만 deterministic order로 반환
7. reference Histogram이 candidate별 exact read-only parent context로 AXIS1에 전달
8. Strategy/Condition immutable version + promoted state exact binding
9. AXIS1 15m DSL이 EMA120/reference Histogram/MACD/JMA/profit permission logic을 compile/execute
10. candidate ordinal / selection hash / strategy hash / condition hash / context binding / AXIS1 response trace 보존
11. future/nearest/fill-forward/default synthesis 없음
12. 같은 inputs는 같은 acceptance identity/trace hash
13. context/reference tamper는 실행 전에 fail-closed
14. frozen legacy core 변경 없음
```

### Step 14 구현 원칙

대표 시나리오용 고정 숫자나 feature identity는 test/acceptance fixture에 둘 수 있지만, AXIS 1/2/3 production core에 특정 전략 shortcut을 추가하지 않는다.

자연어에서 정확히 정해지지 않은 `수익 확보` 기준은 silent guess하지 않는다. acceptance 시나리오에서는 명시적 material assumption을 인간이 승인한 뒤에만 진행한다.

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
