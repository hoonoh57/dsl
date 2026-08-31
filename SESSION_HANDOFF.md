# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 4 BOUNDARY 3 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> **중요 방침/로직 변경은 그 턴에서 문서에 반영한다. 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호와 현재 boundary를 건너뛰지 않는다.**

> **사용자 진행보고는 기본적으로 `한 일 / 할 일`만 짧게 한다.**

---

## 1. 복구 순서

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. DSL_AXIS1_MIGRATION_MANIFEST.md
4. STEP4_BOUNDARY2_FUNCTION_REGISTRY_PARITY_CHECKPOINT_2026-08-31.md
5. STEP4_BOUNDARY1_PARSER_PARITY_CHECKPOINT_2026-08-31.md
6. STEP3_FROZEN_CORE_GUARD_CHECKPOINT_2026-08-31.md
7. STEP2_AXIS1_MIGRATION_PLAN_CHECKPOINT_2026-08-31.md
8. STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md
9. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
10. DSL_FROZEN_CORE_MIGRATION_POLICY.md
11. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
12. DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
13. DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
14. DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
15. DSL_THREE_AXIS_FINAL_TARGET.md
16. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
17. current dsl-live-studio HEAD
```

---

## 2. 현재 작업 포인터

```text
CURRENT_STEP = 4
CURRENT_STEP_NAME = AXIS 1 경계별 이식 + parity
CURRENT_BOUNDARY = 3 Assignment Flow + Semantic
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
Step 1 = 기존 DSL 남은 기능 점검 COMPLETE
Step 2 = AXIS 1 migration manifest + 9개 boundary 순서 COMPLETE
Step 3 = Frozen Core 보호 gate COMPLETE / user-local PASS
Step 4 Boundary 1 = Parser / AST COMPLETE / user-local PASS
Step 4 Boundary 2 = Function Registry COMPLETE / user-local PASS
```

사용자는 Boundary 2 진행 시 frozen guard와 function-registry parity가 모두 `OK`임을 보고했다.

---

## 3. Frozen legacy Core — 절대 보존

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

허용:

```text
read / golden regression / migration parity comparison
```

---

## 4. Step 4 migration 순서

```text
1 Parser / AST                         COMPLETE / PASS
2 Function Registry                    COMPLETE / PASS
3 Assignment Flow + Semantic           CURRENT
4 Indicator Kernel
5 State + Bar Runtime
6 MTF + Read-Only Context Binding
7 DSL Runtime
8 Broker
9 Backtest + Projection Output
```

원칙:

```text
한 boundary만 이식
focused parity
frozen comparison
regression
checkpoint
다음 boundary
```

전체 core 일괄복사, migration 중 신규기능 추가, compatibility exception, frozen core 수정 금지.

---

## 5. Boundary 3 — Assignment Flow + Semantic 현재 상태

```text
legacy:
  core/assignment_flow.py
  core/dsl_semantic.py

axis1:
  axes/axis1_dsl/core/assignment_flow.py
  axes/axis1_dsl/core/dsl_semantic.py
```

이식 방식:

```text
기존 behavior 보존
내부 import만 새 AXIS 1 Parser/Registry/Assignment Flow로 변경
신규 문법/기능 추가 없음
```

focused parity:

```text
tests/test_axis1_semantic_parity.py
```

검증 범위:

```text
on_bar 전/후 assignment dependency partition
valid semantic symbol/type 결과
undefined symbol / bad arity / bad argument type
on_bar function-call rejection
context-binding required rejection
error message/code/line/column
new semantic boundary의 frozen-core runtime import 부재
```

현재 remote compare상 이번 Boundary 3 tranche는 checkpoint + 새 AXIS 1 파일 + focused test만 변경됐고 `core/` 변경은 없다.

아직 user-local PASS가 없으므로 Boundary 3은 `REMOTE_UNVALIDATED`다.
Boundary 3 PASS 전 Boundary 4 Indicator Kernel 시작 금지.

---

## 6. AXIS 1 기능 gap — migration 뒤 즉시 개발

```text
TOP tuple / multi-output typed return + destructuring
generic projection
capability metadata
user-defined functions
bounded loops
on_tick/on_fill rollback/commit
partial fills/exits
pyramiding/multi-position
full reference differential fixtures
full-engine batch/streaming parity
```

Step 1 판정:

```text
JMA 기본 값 = implemented
JMA up/down 공식 DSL access = partial
JMA normalized slope strength = not implemented
numeric intermediate projection = implemented
threshold/permission generic projection = partial
final AXIS 3 CRUD = not yet implemented
```

---

## 7. 3축 책임

```text
AXIS 1 = single-instrument deterministic DSL capability/execution
AXIS 2 = precomputed exact-as-of market/cross-symbol selection
AXIS 3 = Condition/Strategy CRUD + lineage/monetization/orchestration
Chart  = 계산 없이 projection/evidence 표시
```

시장레짐/고베타/섹터/종목간 Histogram ranking은 AXIS 1 DSL이 계산하지 않는다.

---

## 8. External LLM + 지속개선

```text
사용자 자연어 -> Prompt Builder -> 사람 -> 외부 LLM -> 구조화 초안
-> Local validation -> PASS 또는 Correction Prompt -> 반복
```

LLM은 proposal only다. 검증 오류는 누적해 Prompt/Skill/DSL/Data contract 개선 근거로 사용한다. 자동 self-modification과 검증완화는 금지한다.

---

## 9. 사용자 커뮤니케이션 / 콘솔

사용자 진행보고 기본 형식:

```text
한 일
할 일
```

내부 hash/schema/error code/class 이름은 기본 생략한다.

콘솔:

```text
정상 = 가능하면 [PASS] 한 줄
오류 = 디버깅에 필요한 최소 원인/위치만
상세 trace/structured event = 내부 로그
```

---

## 10. 현재 상태

```text
Step 1: COMPLETE
Step 2: COMPLETE
Step 3: COMPLETE / USER-LOCAL PASS
Step 4 Boundary 1: COMPLETE / USER-LOCAL PASS
Step 4 Boundary 2: COMPLETE / USER-LOCAL PASS
Step 4 Boundary 3: WRITTEN / REMOTE_UNVALIDATED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
repository-wide compliance: REMEDIATION_REQUIRED
```

새 executable 변경은 user-local PASS 전 TRUSTED로 부르지 않는다.

---

## 11. 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
python -m unittest discover -s tests -p "test_axis1_parser_parity.py" -v
python -m unittest discover -s tests -p "test_axis1_function_registry_parity.py" -v
python -m unittest discover -s tests -p "test_axis1_semantic_parity.py" -v
```

모두 PASS하면 Boundary 3 checkpoint 후 Boundary 4 Indicator Kernel로 이동한다.

실패 시 먼저 test defect / migration defect / authority drift / environment issue / unknown으로 분류하며 assertion을 약화하지 않는다.

---

## 12. 세션 복구 행동

```text
1. 복구 문서를 순서대로 읽는다.
2. current HEAD와 CURRENT_STEP/BOUNDARY를 확인한다.
3. frozen Core 무변경을 전제로 한다.
4. 기존 결정을 다시 묻지 않는다.
5. 사용자에게 `한 일 / 할 일`만 짧게 제시한다.
6. CURRENT boundary 외 구현을 시작하지 않는다.
7. 실패는 원인분류 후 수정하며 원칙/assertion을 약화하지 않는다.
8. boundary 완료 시 checkpoint/handoff/current pointer를 함께 갱신한다.
```
