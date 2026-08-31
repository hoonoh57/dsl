# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 구현은 현재 번호/경계가 끝나기 전 다음으로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 4
CURRENT_STEP_NAME = AXIS 1 경계별 이식 + parity
CURRENT_BOUNDARY = 9 Backtest + Projection Output
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 / BOUNDARY 1 COMPLETE = Parser / AST user-local PASS
STEP 4 / BOUNDARY 2 COMPLETE = Function Registry user-local PASS
STEP 4 / BOUNDARY 3 COMPLETE = Assignment Flow + Semantic user-local PASS
STEP 4 / BOUNDARY 4 COMPLETE = Indicator Kernel user-local PASS
STEP 4 / BOUNDARY 5 COMPLETE = State + Bar Runtime user-local PASS
STEP 4 / BOUNDARY 6 COMPLETE = MTF + Read-Only Context Binding user-local PASS
STEP 4 / BOUNDARY 7 COMPLETE = DSL Runtime user-local PASS
STEP 4 / BOUNDARY 8 COMPLETE = Broker user-local PASS
  -> STEP4_BOUNDARY8_BROKER_PARITY_CHECKPOINT_2026-08-31.md
```

각 경계는 반드시:

```text
이식 -> focused parity -> frozen guard -> user-local PASS -> checkpoint -> 다음 경계
```

---

## Step 4 이식 순서

```text
1 Parser / AST                         COMPLETE / PASS
2 Function Registry                    COMPLETE / PASS
3 Assignment Flow + Semantic           COMPLETE / PASS
4 Indicator Kernel                     COMPLETE / PASS
5 State + Bar Runtime                  COMPLETE / PASS
6 MTF + Read-Only Context Binding      COMPLETE / PASS
7 DSL Runtime                          COMPLETE / PASS
8 Broker                               COMPLETE / PASS
9 Backtest + Projection Output         CURRENT
```

현재 Boundary 9:

```text
legacy:
  core/backtest.py
  core/backtest_parent_context.py

axis1:
  axes/axis1_dsl/execution/backtest.py
  axes/axis1_dsl/execution/backtest_parent_context.py
```

방식:

```text
백테스트/거래/지표 projection 동작은 기존 behavior 보존
내부 실행기는 새 AXIS 1 Runtime/Broker만 사용
parent context는 legacy provider/frame을 받지 않고 이미 준비된 exact-time read-only binding만 소비
```

완료 조건:

```text
trade sequence / fill price / quantity 동일
metrics numeric 동일
markers 동일
numeric indicator projection 동일
trend-color projection 동일
candles/equity/closed trades 동일
risk exit behavior 동일
timeframe mismatch fail-closed 동일
prepared context exact-time binding 검증
new AXIS 1 backtest에 frozen-core/provider production import 없음
frozen core guard PASS
focused user-local parity PASS
```

금지:

```text
legacy core 수정
legacy provider/frame을 AXIS 1 production API로 유입
nearest-time / fill-forward / interpolation / default
migration 중 generic projection 확장
migration 중 partial fill / pyramiding 등 신규기능 추가
parity 차이를 compatibility exception으로 숨기기
```

Boundary 9 PASS + checkpoint 전 Step 5 시작 금지.

---

## 이후 고정 순서

```text
5. AXIS 1 신규 DSL 기능 개발
   5-1 tuple / multi-output typed return + destructuring
   5-2 tuple-aware generic projection
   5-3 capability/function metadata completeness
   5-4 user-defined functions
   5-5 bounded loops
   5-6 on_tick / on_fill commit/rollback
   5-7 partial fills / partial exits
   5-8 pyramiding / multi-position accounting
   5-9 full reference differential fixtures
   5-10 full-engine batch/streaming parity
6. AXIS 1 machine-readable capability/diagnostic registry
7. Bridge common + AXIS 1 execution contract
8. AXIS 2 exact-as-of snapshot contract
9. AXIS 2 selection engine / core selectors
10. AXIS 3 Condition / Strategy CRUD + orchestration
11. AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
12. External LLM Authoring Lane implementation
13. Continuous Improvement analysis tooling
14. Final natural-language E2E acceptance
15. Legacy docs disposition + repo-wide compliance audit
```

새 아이디어는 PARKING LOT에 기록만 하고 현재 순서를 계속한다. 긴급한 frozen-core/신뢰경계 위반만 예외적으로 현재 작업을 중단할 수 있다.

중요 방침/로직/순서 변경은 그 턴에 관련 authority + 이 문서 + `SESSION_HANDOFF.md`에 반영한다.
