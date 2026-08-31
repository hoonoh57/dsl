# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 구현은 현재 번호/경계가 끝나기 전 다음으로 넘어가지 않는다.

새 아이디어는 PARKING LOT에 기록하고 현재 작업을 계속한다.

---

## 현재 포인터

```text
CURRENT_STEP = 4
CURRENT_STEP_NAME = AXIS 1 경계별 이식 + parity
CURRENT_BOUNDARY = 5 State + Bar Runtime
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
  -> STEP4_BOUNDARY4_INDICATOR_PARITY_CHECKPOINT_2026-08-31.md
```

현재 경계를 완료할 때마다:

```text
결과 기록 -> PASS/FAIL 원인분류 -> checkpoint/handoff 갱신 -> 다음 경계
```

---

## Step 4 이식 순서

```text
1 Parser / AST                         COMPLETE / PASS
2 Function Registry                    COMPLETE / PASS
3 Assignment Flow + Semantic           COMPLETE / PASS
4 Indicator Kernel                     COMPLETE / PASS
5 State + Bar Runtime                  CURRENT
6 MTF + Read-Only Context Binding
7 DSL Runtime
8 Broker
9 Backtest + Projection Output
```

현재 Boundary 5:

```text
legacy:
  core/state.py
  core/bar_runtime.py

axis1:
  axes/axis1_dsl/runtime/state.py
  axes/axis1_dsl/runtime/bar_runtime.py
```

방식:

```text
behavior-preserving migration
bar runtime 내부 Parser import만 새 AXIS 1 경로로 변경
신규 state/event 기능 추가 금지
```

완료 조건:

```text
state primitive 결과 동일
오류 동작 동일
persistent on_bar state 결과 동일
nested if/else 결과 동일
context read 동작 동일
new runtime에 frozen-core production import 없음
frozen core guard PASS
focused user-local parity PASS
```

Boundary 5 PASS + checkpoint 전 Boundary 6 시작 금지.

---

## 이후 고정 순서

```text
5. AXIS 1 신규 DSL 기능 개발
   tuple/multi-output -> generic projection -> metadata -> user functions -> loops
   -> tick/fill lifecycle -> partial fills/exits -> pyramiding/multi-position
6. AXIS 1 machine-readable capability/diagnostic registry
7. Bridge common + AXIS 1 실행계약
8. AXIS 2 사전계산 snapshot 계약
9. AXIS 2 종목선별 엔진/핵심 feature
10. AXIS 3 Condition/Strategy CRUD
11. 3축 E2E Bridge
12. 외부 LLM 자연어 작성 workflow
13. 지속개선 분석도구
14. 최종 자연어 E2E 검증
15. Legacy 문서 정리 + repo-wide compliance audit
```

---

## 절대 금지

```text
frozen core 수정
전체 core 일괄복사
migration 중 신규기능 추가
parity 차이를 compatibility exception으로 숨기기
현재 번호/경계 건너뛰기
```

중요 방침/로직/순서 변경은 그 턴에 관련 authority + 이 문서 + `SESSION_HANDOFF.md`에 반영한다.
