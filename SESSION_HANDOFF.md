# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-1 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 DSL 기능은 가능한 한 명시적 contract + 얇은 lowering/facade 층으로 격리해 기존 메인 로직 오염을 피한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-1 tuple / multi-output typed return + destructuring
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
```

Step 4 최종 checkpoint:

```text
STEP4_BOUNDARY9_BACKTEST_PROJECTION_PARITY_CHECKPOINT_2026-08-31.md
```

Boundary 9 재검증 과정의 2개 오류는 TEST_DEFECT였다. Legacy에서도 금지된 `order.close_long(type = "MARKET")` fixture를 `order.close_long()`으로 수정했고, product/core/assertion을 바꾸지 않은 상태에서 최종 user-local OK를 확인했다.

---

## 현재 5-1 구현

신규 문법은 migrated Parser/Semantic/Runtime을 직접 확장하는 대신 먼저 안전하게 낮춘다.

```text
신규 DSL 문법
 -> typed multi-output lowering
 -> 기존 migrated DSL
 -> 기존 migrated runtime/backtest
```

파일:

```text
axes/axis1_dsl/core/multi_output.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_multi_output.py
```

지원 v1:

```text
line, direction = ta.supertrend([period, multiplier])
upper, middle, lower = ta.bbands(series[, period, multiplier])
macd, signal, hist, strength = user.macd_normalized_all(series[, short, long, signal, method])
```

특징:

```text
component 이름/형식을 등록
반환 개수와 대상 변수 개수 exact 일치
strategy top-level만 허용
중복/예약 이름 fail-closed
등록되지 않은 multi-output 함수 fail-closed
v1은 위치 인수만 허용
lowering 뒤 기존 semantic/runtime 검증 재사용
오류 line은 원래 DSL line으로 remap
```

Runtime facade:

```text
Axis1DSLRuntime
```

Backtest facade:

```text
Axis1BacktestEngine
```

Backtest diagnostics에는 multi-output binding metadata를 보존한다. 다음 5-2 generic projection은 이 metadata를 사용하되 5-1 PASS 전 시작하지 않는다.

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
새 feature를 frozen core에 역이식
신규기능 때문에 migrated core를 불필요하게 대수술
검증완화
```

---

## 다음 순서

```text
5-1 multi-output + destructuring          CURRENT
5-2 tuple-aware generic projection
5-3 capability metadata
5-4 user-defined functions
5-5 bounded loops
5-6 on_tick / on_fill commit/rollback
5-7 partial fills / partial exits
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
python -m unittest discover -s tests -p "test_axis1_multi_output.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

둘 다 PASS하면 5-1 checkpoint 후 5-2 tuple-aware generic projection으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 원칙/assertion을 약화하지 않는다.
