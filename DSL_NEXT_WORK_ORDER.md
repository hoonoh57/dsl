# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 현재 번호가 검증되기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-2 tuple-aware generic projection
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
  -> STEP4_BOUNDARY9_BACKTEST_PROJECTION_PARITY_CHECKPOINT_2026-08-31.md
STEP 5-1 COMPLETE = tuple / multi-output typed return + destructuring user-local PASS
  -> STEP5_1_MULTI_OUTPUT_CHECKPOINT_2026-08-31.md
```

Step 4 최종 상태:

```text
1 Parser / AST                         PASS
2 Function Registry                    PASS
3 Assignment Flow + Semantic           PASS
4 Indicator Kernel                     PASS
5 State + Bar Runtime                  PASS
6 MTF + Read-Only Context Binding      PASS
7 DSL Runtime                          PASS
8 Broker                               PASS
9 Backtest + Projection Output         PASS
```

---

## 5-2 현재 — tuple-aware generic projection

목표는 multi-output 결과를 특정 지표 이름별 예외처리 없이 공통 projection contract로 노출하는 것이다.

원칙:

```text
지표/조건 값을 Chart에서 재계산하지 않음
이미 실행된 Backtest indicator output + multi-output binding metadata만 소비
사용자가 붙인 target 이름과 등록 component identity를 보존
pane/overlay와 direction-color는 기존 실행 output을 그대로 재사용
특정 ta.supertrend / ta.bbands / MACD 이름을 renderer logic에 하드코딩하지 않음
projection이 없어도 거래/백테스트 실행 결과를 바꾸지 않음
```

구조:

```text
Axis1BacktestEngine
 -> migrated BacktestEngine 결과
 -> generic projection manifest 부착
 -> 기존 indicators data는 재계산 없이 참조/주석만 추가
```

5-2 완료 조건:

```text
single-output numeric series도 공통 projection manifest에 노출
multi-output 각 target이 function/component/type identity를 보존
기존 indicator data/overlay/direction-color를 그대로 사용
값이 없는 warmup-only component를 임의 값으로 합성하지 않음
projection module이 indicator kernel/runtime/provider/frozen core를 호출하지 않음
기존 5-1 multi-output test PASS
frozen core guard PASS
focused user-local projection test PASS
```

금지:

```text
Chart에서 indicator 재계산
missing 값을 0/default/fill-forward로 생성
특정 지표별 renderer 분기 확대
5-3 capability metadata를 선행 구현
migrated execution core 대수술
```

5-2 PASS + checkpoint 전 5-3 시작 금지.

---

## 이후 고정 순서

```text
5-3 capability/function metadata completeness
5-4 user-defined functions
5-5 bounded loops
5-6 on_tick / on_fill commit/rollback
5-7 partial fills / partial exits
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
새 기능은 가능한 한 명시적 contract + lowering/facade로 격리
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
