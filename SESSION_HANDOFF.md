# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-5 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 DSL 기능은 가능한 한 명시적 contract + 얇은 compile-time lowering/facade 층으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-5 bounded loops
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
```

최근 checkpoint:

```text
STEP5_4_USER_FUNCTIONS_CHECKPOINT_2026-08-31.md
```

5-4 user-local evidence:

```text
test_axis1_user_functions.py = OK
test_axis1_multi_output.py = OK
test_axis1_generic_projection.py = OK
test_axis1_capability_metadata.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 5-5 구현

목표:

```text
반복 횟수가 compile 전에 확정되는 순수 계산만 허용하고
runtime에 loop 실행권한이나 무한반복 가능성을 추가하지 않음
```

구현 파일:

```text
axes/axis1_dsl/core/bounded_loops.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_bounded_loops.py
```

Lowering 순서:

```text
bounded loops
 -> user functions
 -> multi-output
 -> migrated parser/semantic/runtime/backtest
 -> generic projection
```

v1 범위:

```text
user-defined function 내부에서만 for ... in range(...) 허용
range는 1~3개의 compile-time 정수 위치 인수
최대 64회
step=0 금지
index read-only
앞서 선언된 function local accumulator만 loop에서 갱신
parameter mutation 금지
nested loop/control block 금지
compile-time 전개 후 runtime loop는 존재하지 않음
source line 수 보존
과도한 expression 전개는 fail-closed
```

Backtest diagnostics에는 function/index/range/iteration-count/target metadata를 보존한다. 내부 helper 이름은 user-function lowering에서 소거되어 실행 indicator/projection으로 나오지 않아야 한다.

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
runtime while/break/continue/dynamic bound 추가
신규기능 때문에 migrated core를 불필요하게 대수술
검증완화
```

---

## 다음 순서

```text
5-5 bounded loops                         CURRENT
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

사용자 local에서:

```text
python -m unittest discover -s tests -p "test_axis1_bounded_loops.py" -v
python -m unittest discover -s tests -p "test_axis1_user_functions.py" -v
python -m unittest discover -s tests -p "test_axis1_multi_output.py" -v
python -m unittest discover -s tests -p "test_axis1_generic_projection.py" -v
python -m unittest discover -s tests -p "test_axis1_capability_metadata.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-5 checkpoint 후 5-6 on_tick/on_fill commit/rollback으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 원칙/assertion을 약화하지 않는다.
