# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-8 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 dsl-live-studio 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 한 일 / 할 일만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 기능은 가능한 한 별도 lowering/facade/session으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-8 pyramiding / multi-position accounting
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
Step 5-7 partial fills / partial exits = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_7_PARTIAL_EXECUTION_CHECKPOINT_2026-09-01.md
```

5-7 user-local evidence:

```text
test_axis1_partial_execution.py = OK
test_axis1_intrabar_lifecycle.py = OK
test_axis1_broker_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 5-8 구현

목표:

```text
같은 방향의 분할진입을 entry order별 독립 lot으로 관리하고
여러 lot의 총 수량/평균단가/비용/실현손익을 결정적으로 계산
```

구현 파일:

```text
axes/axis1_dsl/execution/pyramiding_execution.py
tests/test_axis1_pyramiding_execution.py
```

주요 객체:

```text
PositionLot
LotRealization
PyramidingLedger
PyramidingExecutionSession
```

Step 5-7의 `PartialFillBroker`를 그대로 재사용한다. 기존 `PartialExecutionSession`은 수정하지 않아 single-position + pyramiding fail-closed contract를 유지한다.

Entry contract:

```text
같은 entry order의 여러 partial fill = 같은 lot에 누적
새 same-direction entry order = 새 lot
기본 max_lots = 4
aggregate quantity = active lot 수량 합
aggregate average entry = active lot 수량가중 평균
long exposure 중 SELL_SHORT 추가진입 금지
short exposure 중 BUY 추가진입 금지
hedging/netting 금지
```

Exit contract:

```text
기본 allocation = FIFO(entry sequence)
lot_id를 지정하면 그 lot만 target exit
한 exit fill이 lot 여러 개를 건너가면 lot별 realized slice 생성
각 lot의 remaining entry fee를 실제 청산수량 비율로 배분
exit fee/gross/net PnL도 allocation별 계산
aggregate quantity가 0이 될 때 closed cycle +1
flat 이후에는 반대 방향 새 cycle 가능
```

Fail-closed:

```text
max_lots 초과
opposite-direction 추가진입
aggregate over-exit
target lot over-exit
inactive/unknown lot target
Step 5-8에서는 동시 active exit order 여러 개 금지
```

5-6 intrabar 연동:

```text
각 pyramiding partial fill result를 기존 IntrabarStateSession.on_fill payload로 변환 가능
strategy state rollback은 실제 broker/accounting execution fact를 되돌리지 않음
```

Batch boundary:

```text
기존 migrated BacktestEngine은 그대로 single-position whole-fill authoritative
현재 Step 5-8은 별도 execution session에만 multi-lot 권한 추가
DSL order syntax와 batch event tape 통합은 아직 하지 않음
full batch/stream parity는 Step 5-10 authority
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
migrated BrokerEmulator/BacktestEngine 직접 대수술
hedging/netting 묵시 허용
lot allocation 규칙의 비결정적 변경
검증완화
```

---

## 다음 순서

```text
5-8 pyramiding / multi-position              CURRENT
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
python -m unittest discover -s tests -p "test_axis1_pyramiding_execution.py" -v
python -m unittest discover -s tests -p "test_axis1_partial_execution.py" -v
python -m unittest discover -s tests -p "test_axis1_intrabar_lifecycle.py" -v
python -m unittest discover -s tests -p "test_axis1_broker_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-8 checkpoint 후 5-9 reference differential fixtures로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
