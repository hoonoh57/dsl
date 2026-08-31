# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-7 partial fills / partial exits
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
```

5-6 user-local evidence:

```text
test_axis1_intrabar_lifecycle.py = OK
test_axis1_bounded_loops.py = OK
test_axis1_user_functions.py = OK
test_axis1_multi_output.py = OK
test_axis1_generic_projection.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 5-7 현재 — partial fills / partial exits

목표:

```text
하나의 주문이 여러 체결로 나뉘어도 누적체결/잔량/평균체결가를 권위 있게 보존하고
하나의 보유 포지션을 여러 차례 부분청산해도 수량/비용/PnL이 정확히 이어지도록 함
```

구현:

```text
axes/axis1_dsl/execution/partial_execution.py
tests/test_axis1_partial_execution.py
```

구조:

```text
PartialFillBroker
  order requested quantity
  -> fill slice 1 ... N
  -> PARTIALLY_FILLED | FILLED
  -> cumulative quantity / remaining quantity / weighted average fill / fill ledger

SinglePositionLedger
  one original entry order may complete through multiple fill slices
  -> weighted average entry price
  -> partial exit slices
  -> proportional entry-fee allocation
  -> realized PnL per exit slice
  -> remaining position quantity

PartialExecutionSession
  broker fill fact + single-position accounting coordination
```

5-7 contract:

```text
PARTIALLY_FILLED 상태를 명시적으로 보유
requested / cumulative filled / remaining quantity를 별도 보존
fill quantity는 remaining을 초과할 수 없음
각 fill은 별도 immutable fill record
weighted average fill price 유지
부분체결 후 cancel은 이미 체결된 수량을 되돌리지 않고 잔량만 취소
부분청산은 현재 position quantity 이하만 허용
entry fee는 partial exit quantity 비율로 배분
exit fill마다 gross/net realized PnL 기록
position quantity가 0이 될 때만 position 완전 종료
```

Step 5-8 경계 보호:

```text
새 entry order로 기존 position에 추가 진입 금지
같은 원 original entry order의 잔여 partial fill만 계속 허용
동시에 여러 active exit order 금지
pyramiding / multi-position / lot selection은 Step 5-8 전까지 금지
```

Step 5-6 연동:

```text
각 partial fill slice는 on_fill event payload로 변환 가능
strategy intrabar state rollback은 실제 broker/accounting fill fact를 되돌리지 않음
exchange execution fact와 provisional strategy state의 authority를 분리
```

Batch policy:

```text
migrated BacktestEngine의 기존 whole-fill 동작은 Step 5-7에서 변경하지 않음
partial-fill event tape 기반 batch/stream 동일성은 Step 5-10에서 검증
기존 백테스트 결과를 임의 partial-fill로 바꾸지 않음
```

중요 원칙:

```text
frozen core 수정 없음
migrated BrokerEmulator/BacktestEngine 직접 수정 없음
기존 whole-fill lifecycle은 full-quantity 한 번 체결 시 동일 status shape 유지
검증완화 금지
5-8 선행 구현 금지
```

5-7 완료 조건:

```text
full fill 기존 lifecycle status shape 유지
partial fill cumulative/remaining/weighted average 정확
partial cancel executed quantity 보존
order overfill atomic fail-closed
partial entry 여러 fill 후 weighted position 정확
partial exit 여러 fill/order 후 remaining quantity/PnL 정확
entry fee proportional allocation 정확
position over-exit atomic fail-closed
pyramiding fail-closed
각 partial fill -> 기존 on_fill provisional state 연동 가능
new module frozen-core import 없음
5-1~5-6 회귀검사 PASS
frozen core guard PASS
focused user-local partial-execution test PASS
```

5-7 PASS + checkpoint 전 5-8 시작 금지.

---

## 이후 고정 순서

```text
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
새 기능은 가능한 한 명시적 contract + 격리된 facade/session으로 추가
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
