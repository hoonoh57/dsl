# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-5 / RETEST REQUIRED / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 DSL 기능은 가능한 한 명시적 contract + 얇은 compile-time lowering/facade 층으로 격리한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-5 bounded loops
STATUS = REMOTE_RETEST_REQUIRED
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

---

## 현재 5-5 검증상태

첫 user-local 결과:

```text
test_axis1_bounded_loops.py = Ran 7 / 1 failure
나머지 5-4/5-3/5-2/5-1 회귀검사와 frozen core guard = OK
```

첫 원인 분류:

```text
FEATURE_DEFECT — bounded-loop 결과를 ta.bbands multi-output에 넣을 때 warmup NaN parity 불일치
```

첫 수정은 upper/middle/lower 전체를 같은 연속-finite mask로 처리했다. 이 수정 후 user-local 재검증에서:

```text
test_axis1_bounded_loops.py = Ran 7 / 1 failure
test_axis1_multi_output.py = Ran 8 / 1 failure
```

재검증으로 확인된 정확한 contract:

```text
CoreTALib.bbands middle:
  CoreTALib.sma 사용
  SMA는 rolling 입력 NaN을 0으로 취급하는 기존 semantics

CoreTALib.bbands upper/lower deviation:
  직접 np.std(window) 사용
  window 안에 NaN이 하나라도 있으면 deviation은 NaN
```

따라서 BBands 세 출력의 warmup/NaN semantics는 동일하지 않다. 첫 보정은 middle까지 강제로 NaN 처리하여 과도한 masking을 만들었다.

현재 수정:

```text
axes/axis1_dsl/core/multi_output.py
middle은 ta.sma 결과를 그대로 사용
upper/lower에 쓰는 deviation만 period 연속 유효값 전까지 NaN 유지
기존 DSL primitive만 사용
migrated Parser/Semantic/Runtime/Backtest 직접 변경 없음
frozen core 변경 없음
assertion/expected 완화 없음
```

기존 회귀검사 `test_bbands_destructuring_preserves_input_nan_windows`는 direct `CoreTALib.bbands`와 세 component를 exact 비교하므로 현재 수정이 middle/upper/lower 각각의 기존 semantics를 모두 재현하는지 검증한다.

현재는 user-local 재검증 전이므로 5-5 PASS로 부르지 않는다.

---

## 5-5 bounded loop contract

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

Lowering 순서:

```text
bounded loops
 -> user functions
 -> multi-output
 -> migrated parser/semantic/runtime/backtest
 -> generic projection
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
새 feature를 frozen core에 역이식
runtime while/break/continue/dynamic bound 추가
신규기능 때문에 migrated core를 불필요하게 대수술
검증완화
```

---

## 다음 순서

```text
5-5 bounded loops                         CURRENT / RETEST REQUIRED
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
python -m unittest discover -s tests -p "test_axis1_bounded_loops.py" -v
python -m unittest discover -s tests -p "test_axis1_multi_output.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

세 검사 모두 PASS하면 앞서 이미 OK였던 나머지 회귀검사 결과와 합쳐 5-5 checkpoint 후 5-6으로 이동한다.

실패 시 새 오류를 test defect / feature defect / authority drift / environment issue / unknown으로 다시 분류하고 원칙/assertion을 약화하지 않는다.
