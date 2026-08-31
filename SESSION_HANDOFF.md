# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-9 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 dsl-live-studio 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 한 일 / 할 일만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 기능과 검증은 가능한 한 별도 lowering/facade/session/test-reference 층으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-9 full reference differential fixtures
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
```

최근 checkpoint:

```text
STEP5_8_PYRAMIDING_EXECUTION_CHECKPOINT_2026-09-01.md
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

## 현재 5-9 구현

목표:

```text
기존 frozen core 복제 비교만으로는 잡기 어려운 공통 결함을 피하기 위해
TA/user indicator를 독립 NumPy reference와 대량 differential 비교
```

구현 파일:

```text
tests/axis1_reference_indicators.py
tests/test_axis1_reference_differential.py
```

Reference 원칙:

```text
AXIS 1 production module import 금지
frozen core import 금지
NumPy와 명시적 수식/상태전이만 사용
production 결과로 expected 생성 금지
```

검증 대상:

```text
rolling/moving average/warmup 계열
recursive ATR/RSI/MACD/TRIX/CCI/ADX
JMA trend values + direction metadata
Supertrend line + direction
range/VHF/Williams 계열
cross/bars-since/value-when 등 event-history 계열
BBands multi-output
normalized MACD 전체 component
실제 Axis1DSLRuntime 함수 mapping
```

범위 완전성 gate:

```text
FUNCTION_SPECS에서 category=ta/user인 모든 등록 함수가
명시적인 differential coverage set에 들어있어야 한다.
새 ta/user 함수가 registry에 추가되고 reference test가 빠지면 자동 FAIL한다.
```

Fixture matrix:

```text
결정적 비선형 OHLCV
복수 period 2/3/5/8/14/21
NaN warmup + 중간 NaN
flat/zero-range edge
JMA 여러 phase/length/power
Supertrend 여러 period/multiplier
normalized MACD simple/exponential/weighted
```

Step 5-9에서 production indicator/runtime를 변경하지 않았다. 차이가 나오면 test/reference defect와 product defect를 먼저 구분하고 assertion/tolerance를 약화하지 않는다.

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
reference expected를 actual에 맞춰 임의 완화
Step 5-10 batch/stream parity 선행 구현
검증완화
```

---

## 다음 순서

```text
5-9 reference differential fixtures          CURRENT
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
python -m unittest discover -s tests -p "test_axis1_reference_differential.py" -v
python -m unittest discover -s tests -p "test_axis1_indicator_parity.py" -v
python -m unittest discover -s tests -p "test_axis1_pyramiding_execution.py" -v
python -m unittest discover -s tests -p "test_axis1_partial_execution.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-9 checkpoint 후 5-10 full-engine batch/streaming parity로 이동한다.

실패 시 reference defect / product defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
