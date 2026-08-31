# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 4 BOUNDARY 9 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 중요한 방침/로직 변경은 그 턴에서 문서에 반영한다. 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호와 현재 boundary를 건너뛰지 않는다.

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다. 기계용 상세정보는 내부에서 관리하고 콘솔도 디버깅에 필요한 최소 정보만 출력한다.

---

## 현재 작업

```text
CURRENT_STEP = 4
CURRENT_BOUNDARY = 9 Backtest + Projection Output
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Boundary 1 Parser / AST = COMPLETE / USER-LOCAL PASS
Boundary 2 Function Registry = COMPLETE / USER-LOCAL PASS
Boundary 3 Assignment Flow + Semantic = COMPLETE / USER-LOCAL PASS
Boundary 4 Indicator Kernel = COMPLETE / USER-LOCAL PASS
Boundary 5 State + Bar Runtime = COMPLETE / USER-LOCAL PASS
Boundary 6 MTF + Read-Only Context Binding = COMPLETE / USER-LOCAL PASS
Boundary 7 DSL Runtime = COMPLETE / USER-LOCAL PASS
Boundary 8 Broker = COMPLETE / USER-LOCAL PASS
```

Boundary 8 user-local evidence:

```text
broker parity = OK
frozen core guard = OK
```

Checkpoint:

```text
STEP4_BOUNDARY8_BROKER_PARITY_CHECKPOINT_2026-08-31.md
```

---

## 현재 Boundary 9

이식 대상:

```text
legacy:
  core/backtest.py
  core/backtest_parent_context.py

axis1:
  axes/axis1_dsl/execution/backtest.py
  axes/axis1_dsl/execution/backtest_parent_context.py
```

현재 remote 상태:

```text
백테스트 엔진 이식 완료
새 AXIS 1 Runtime/Broker만 사용
기존 candles/markers/trades/closed-trades/metrics/equity/indicator projection 보존
focused parity test 추가:
  tests/test_axis1_backtest_projection_parity.py
```

Context boundary:

```text
legacy ParentContextFrame / ParentFeatureRegistry를 AXIS 1 API에 받지 않는다.
이미 준비된 DSLContextSeriesBinding만 받는다.
market instrument와 target symbol exact 일치 필요.
market bar times와 binding target_times exact 일치 필요.
nearest/fill-forward/interpolation/default 없음.
```

검증 대상:

```text
거래 순서 / 체결값 / 수량
metrics numeric
markers / candles / equity
numeric indicator projection / JMA trend-color projection
closed trades / risk exits
strategy/timeframe
prepared context exact binding
timeframe mismatch fail-closed
new backtest/context adapter의 frozen-core/provider import 부재
```

Boundary 9는 user-local PASS 전 TRUSTED로 부르지 않는다. PASS 전 Step 5 신규 DSL 기능 개발 시작 금지.

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
새 기능 역이식
새 AXIS production code가 frozen core 내부 구현에 영구 의존
expected frozen hash 변경으로 위반 수용
```

---

## Step 4 상태

```text
1 Parser / AST                         PASS
2 Function Registry                    PASS
3 Assignment Flow + Semantic           PASS
4 Indicator Kernel                     PASS
5 State + Bar Runtime                  PASS
6 MTF + Read-Only Context Binding      PASS
7 DSL Runtime                          PASS
8 Broker                               PASS
9 Backtest + Projection Output         CURRENT / REMOTE_UNVALIDATED
```

Boundary 9 PASS 후에만 Step 4 전체 migration parity를 COMPLETE 처리한다.

---

## 이후 작업순서

```text
5-1 tuple / multi-output + destructuring
5-2 generic projection
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

새 아이디어는 PARKING LOT에 기록만 하고 현재 순서를 계속한다.

---

## 사용자 커뮤니케이션 / 콘솔

```text
사용자 화면 = 한 일 / 할 일
성공 콘솔 = 가능하면 [PASS] 한 줄
실패 콘솔 = 디버깅에 필요한 최소 원인/위치
상세 hash/schema/error code/event = 내부 관리
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis1_backtest_projection_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

둘 다 PASS하면 Boundary 9 checkpoint 후 Step 4 전체 migration parity를 COMPLETE 처리하고, 순서대로 Step 5-1 tuple / multi-output로 이동한다.

실패 시 test defect / migration defect / authority drift / environment issue / unknown 순으로 원인분류하고 assertion이나 원칙을 약화하지 않는다.
