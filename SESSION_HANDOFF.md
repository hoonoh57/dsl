# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-10 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 기능/검증은 가능한 한 별도 lowering/facade/session/parity 층으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-10 full-engine batch/streaming parity
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
Step 5-8 pyramiding / multi-position = COMPLETE / USER-LOCAL PASS
Step 5-9 reference differential fixtures = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_9_REFERENCE_DIFFERENTIAL_CHECKPOINT_2026-09-01.md
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

## 현재 5-10 구현

구현 파일:

```text
axes/axis1_dsl/execution/full_engine_parity.py
tests/test_axis1_full_engine_parity.py
```

검증 계약은 세 부분이다.

### 1. Runtime causal-prefix parity

```text
full batch compile
vs
1..N bar prefix compile
```

모든 runtime ndarray, NaN/warmup, trend metadata, on_bar state, MTF output, multi-output, event condition/order argument를 prefix 기준 exact 비교한다.

이 prefix replay는 correctness oracle이며 성능 최적화된 incremental 계산기라고 부르지 않는다.

### 2. Backtest prefix parity

```text
full batch backtest
vs
2..N bar prefix backtest replay
```

비교:

```text
equity curve
trades/executions
closed trades
broker lifecycle history
open-position state
```

Artificial prefix-end expiry가 결과를 오염시키지 않도록 parity fixture는 market/GTC 주문을 사용한다.

### 3. Ordered event tape parity

`Axis1EventTapeSession`이 다음 Step 5-6~5-8 권한을 하나의 ordered tape로 연결한다.

```text
intrabar provisional state
partial fill broker
pyramiding multi-lot accounting
```

지원 event:

```text
BEGIN_BAR
TICK
SUBMIT_ENTRY
SUBMIT_EXIT
FILL
CANCEL
COMMIT_BAR
ROLLBACK_BAR
```

같은 tape를 한 번에 replay한 결과와 event별 streaming apply 결과가 exact 동일해야 한다.

중요 권위:

```text
broker/accounting fill fact는 실제 체결 사실로 보존
strategy provisional rollback은 실제 fill을 취소하지 않음
```

현재 migrated runtime/backtest/broker와 frozen core는 직접 수정하지 않았다.

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
prefix replay를 실시간 성능 구현으로 과장
intrabar event tape를 기존 backtest에 침묵 삽입
batch/stream 입력조건을 다르게 놓고 parity 주장
검증완화
```

---

## 다음 순서

```text
5-10 full-engine batch/streaming parity       CURRENT
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
python -m unittest discover -s tests -p "test_axis1_full_engine_parity.py" -v
python -m unittest discover -s tests -p "test_axis1_reference_differential.py" -v
python -m unittest discover -s tests -p "test_axis1_pyramiding_execution.py" -v
python -m unittest discover -s tests -p "test_axis1_partial_execution.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 5-10 checkpoint 후 Step 6 machine-readable capability/diagnostic registry로 이동한다.

실패 시 test defect / product defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
