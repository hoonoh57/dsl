# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-8 pyramiding / multi-position accounting
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
```

5-7 user-local evidence:

```text
test_axis1_partial_execution.py = OK
test_axis1_intrabar_lifecycle.py = OK
test_axis1_broker_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 5-8 현재 — pyramiding / multi-position accounting

목표:

```text
같은 방향의 여러 entry order를 독립 lot으로 보존하면서
aggregate position quantity / weighted average entry / fee / realized PnL을 결정적으로 관리
```

구현:

```text
axes/axis1_dsl/execution/pyramiding_execution.py
tests/test_axis1_pyramiding_execution.py
```

구조:

```text
PartialFillBroker (Step 5-7 재사용)
  -> entry order별 partial fill fact

PyramidingLedger
  -> entry order 1개 = position lot 1개
  -> 같은 order의 여러 fill은 동일 lot weighted cost로 합산
  -> 같은 방향 새 entry order는 새 lot 생성
  -> aggregate quantity / weighted average / remaining entry fee 계산

Exit allocation
  -> 기본 FIFO lot allocation
  -> lot_id를 명시하면 해당 lot만 부분청산
  -> 각 allocation마다 realized PnL / fee 기록

PyramidingExecutionSession
  -> broker fill fact + multi-lot accounting coordination
```

5-8 contract:

```text
same-direction pyramiding만 허용
기본 max_lots = 4, 호출자가 명시적으로 조정 가능
entry order별 deterministic lot identity
같은 entry order의 partial fills는 같은 lot에 누적
새 entry order는 새 lot 생성
aggregate average entry = active lot 수량가중 평균
aggregate quantity = active lot quantity 합
```

Exit contract:

```text
기본 exit은 FIFO(entry sequence)로 lot을 소비
lot_id 지정 시 target lot만 소비
한 exit fill이 여러 lot을 가로지르면 lot별 realized slice를 별도 기록
entry fee는 각 lot의 실제 청산수량 비율로 배분
exit fee와 gross/net PnL도 lot별 계산
aggregate quantity가 0이 될 때 position cycle 1회 종료
```

Fail-closed boundary:

```text
long exposure 중 SELL_SHORT 추가진입 금지
short exposure 중 BUY 추가진입 금지
동시 long/short hedge 금지
max_lots 초과 금지
lot quantity 초과 targeted exit 금지
aggregate quantity 초과 exit 금지
Step 5-8에서는 active exit order를 동시에 여러 개 두지 않음
```

5-7 호환성:

```text
기존 PartialExecutionSession은 계속 single-position + pyramiding fail-closed
새 pyramiding 권한은 PyramidingExecutionSession에만 존재
기존 PartialFillBroker lifecycle/partial-fill semantics 재사용
각 pyramiding fill slice는 기존 on_fill provisional state payload로 전달 가능
```

Batch boundary:

```text
migrated BacktestEngine의 기존 single-position whole-fill 실행은 Step 5-8에서 변경하지 않음
DSL order syntax에 pyramiding quantity/lot selection을 아직 혼입하지 않음
multi-lot event tape와 batch/stream 동일성은 Step 5-10에서 검증
```

중요 원칙:

```text
frozen core 수정 없음
migrated BrokerEmulator/BacktestEngine 직접 수정 없음
hedging/netting을 묵시적으로 허용하지 않음
lot allocation 규칙을 시장상황에 따라 임의 변경하지 않음
5-9 reference differential을 선행 구현하지 않음
검증완화 금지
```

5-8 완료 조건:

```text
같은 order partial fills -> 동일 lot weighted average 정확
같은 방향 여러 entry order -> 독립 lot + aggregate weighted average 정확
FIFO partial exit가 lot 경계를 결정적으로 소비
explicit target lot exit가 다른 lot을 건드리지 않음
lot별 entry fee / exit fee / realized PnL 정확
flatten 후 반대 방향 새 cycle 진입 가능
exposure 중 opposite entry fail-closed
max_lots 초과가 broker mutation 전 fail-closed
target lot over-exit가 broker/accounting mutation 전 fail-closed
각 fill -> 기존 on_fill provisional state 연동 가능
Step 5-7 single-position session의 pyramiding 금지 contract 유지
new module frozen-core/backtest import 없음
5-1~5-7 회귀검사 PASS
frozen core guard PASS
focused user-local pyramiding test PASS
```

5-8 PASS + checkpoint 전 5-9 시작 금지.

---

## 이후 고정 순서

```text
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
새 기능은 가능한 한 명시적 contract + 격리된 facade/session으로 추가
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
