# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-7 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 dsl-live-studio 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 한 일 / 할 일만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 기능은 가능한 한 별도 lowering/facade/session으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-7 partial fills / partial exits
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
Step 5-1 multi-output + destructuring = COMPLETE / USER-LOCAL PASS
Step 5-2 tuple-aware generic projection = COMPLETE / USER-LOCAL PASS
Step 5-3 capability/function metadata = COMPLETE / USER-LOCAL PASS
Step 5-4 user-defined functions = COMPLETE / USER-LOCAL PASS
Step 5-5 bounded loops = COMPLETE / USER-LOCAL PASS
Step 5-6 on_tick/on_fill commit/rollback = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_6_INTRABAR_LIFECYCLE_CHECKPOINT_2026-09-01.md
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

## 현재 5-7 구현

목표:

```text
한 주문의 여러 partial fill과 한 position의 여러 partial exit를
누적수량/잔량/평균체결가/비용/PnL 기준으로 결정적으로 관리
```

구현 파일:

```text
axes/axis1_dsl/execution/partial_execution.py
tests/test_axis1_partial_execution.py
```

주요 객체:

```text
PartialFillBroker
PartialFillOrder
PartialFillRecord
SinglePositionLedger
PartialExecutionSession
```

Order contract:

```text
status = CREATED / ACCEPTED / TRIGGERED / PARTIALLY_FILLED / FILLED / CANCELED / REJECTED / EXPIRED
quantity = original requested quantity
filled_quantity = cumulative executed quantity
remaining_quantity = unexecuted quantity
average_fill_price = cumulative weighted average
fills = immutable fill-slice records
```

Partial fill rules:

```text
remaining 초과 fill 금지
부분체결 상태는 active order로 유지
부분체결 후 cancel/expire는 체결분을 취소하지 않음
full quantity를 한 번에 fill하면 기존 whole-fill CREATED->ACCEPTED->FILLED status shape 유지
OCO sibling은 한쪽이 실제 execution을 시작하면 다른 active sibling의 잔량을 취소
```

Single-position accounting:

```text
같은 original entry order의 잔여 fill은 허용
다른 entry order로 position 추가는 Step 5-8 전까지 금지
entry fill 여러 건은 weighted average entry price로 합산
partial exit는 현재 position quantity 이내만 허용
entry fee remaining을 exit quantity 비율로 배분
exit slice마다 realized gross/net PnL 기록
position quantity=0일 때만 완전 종료
```

5-6 intrabar 연동:

```text
각 partial fill result는 기존 IntrabarStateSession.on_fill payload로 변환 가능
strategy provisional state가 rollback되어도 실제 execution/accounting fill은 rollback하지 않음
```

Batch boundary:

```text
기존 migrated BacktestEngine은 계속 whole-fill authoritative
Step 5-7에서 기존 batch 결과를 partial-fill로 임의 변경하지 않음
partial event tape batch/stream parity는 Step 5-10에서 검증
```

검증 예정:

```text
whole-fill status compatibility
cumulative/remaining/weighted fill accounting
partial cancel
atomic order-overfill rejection
partial entry + sequential partial exits
fee allocation and realized PnL
position over-exit atomic rejection
pyramiding fail-closed
partial fill -> on_fill provisional state integration
frozen-core import isolation
```

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정 / 이동 / 삭제 / 신규 파일 추가
expected frozen hash 변경으로 위반 수용
migrated BrokerEmulator/BacktestEngine을 partial-fill 때문에 직접 대수술
position occupied 상태에서 새 entry를 추가하는 pyramiding 선행 구현
multi-position/lot selection 선행 구현
검증완화
```

---

## 다음 순서

```text
5-7 partial fills / partial exits            CURRENT
5-8 pyramiding / multi-position
5-9 reference differential fixtures
5-10 full-engine batch/streaming parity
6 machine-readable capability/diagnostic registry
7 Bridge common + AXIS 1 execution contract
8 AXIS 2 exact-as-of snapshot contract
9 AXIS 2 selection engine
10 AXIS 3 Condition/Strategy CRUD
11 3축 E2E Bridge
12 External LLM Authoring Lane
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 사용자 커뮤니케이션 / 콘솔

```text
사용자 화면 = 한 일 / 할 일
정상 콘솔 = 가능하면 [PASS] 한 줄
실패 콘솔 = 디버깅에 필요한 최소 원인/위치
기계용 상세정보 = 내부 관리
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis1_partial_execution.py" -v
python -m unittest discover -s tests -p "test_axis1_intrabar_lifecycle.py" -v
python -m unittest discover -s tests -p "test_axis1_broker_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-7 checkpoint 후 5-8 pyramiding / multi-position accounting으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
