# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 4 BOUNDARY 1 / 2026-08-31 KST**

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
4. STEP3_FROZEN_CORE_GUARD_CHECKPOINT_2026-08-31.md
5. STEP2_AXIS1_MIGRATION_PLAN_CHECKPOINT_2026-08-31.md
6. STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md
7. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
8. DSL_FROZEN_CORE_MIGRATION_POLICY.md
9. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
10. DSL_THREE_AXIS_FINAL_TARGET.md
11. DSL_THREE_AXIS_MODULE_BOUNDARY.md
12. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
13. CURRENT_STATE.md
14. current dsl-live-studio HEAD
```

---

## 2. 현재 작업 포인터

```text
CURRENT_STEP = 4
CURRENT_STEP_NAME = AXIS 1 경계별 이식 + parity
CURRENT_BOUNDARY = 1 Parser / AST
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
Step 1 = 기존 DSL 남은 기능 점검 COMPLETE
Step 2 = AXIS 1 migration manifest + 9개 boundary 순서 COMPLETE
Step 3 = Frozen Core 보호 gate COMPLETE / user-local PASS
```

Step 3 user-local evidence:

```text
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py"
Ran 1 test in 0.046s
OK
```

판정:

```text
PASS / no defect detected / frozen legacy core unchanged
```

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
expected frozen hash를 변경해 위반을 수용
```

허용:

```text
read / golden regression / migration parity comparison
```

---

## 4. Step 4 migration 순서

```text
1 Parser / AST                         <- CURRENT
2 Function Registry
3 Assignment Flow + Semantic
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

## 5. Boundary 1 — Parser / AST 현재 상태

Source:

```text
core/dsl_parser.py
```

New target:

```text
axes/axis1_dsl/core/dsl_parser.py
```

현재 remote evidence:

```text
legacy blob sha = 8f22472c01144dbb7bad8aef1f8989af81768805
new blob sha    = 8f22472c01144dbb7bad8aef1f8989af81768805
```

즉 현재 이식 파일은 source content 기준 exact copy다.

추가된 focused parity:

```text
tests/test_axis1_parser_parity.py
```

검증 범위:

```text
AST dataclass field contract
successful parse result equality
fail-closed diagnostic message/code/line/column equality
new parser production source에 frozen core runtime import 없음
```

아직 user-local PASS가 없으므로 Boundary 1은 `REMOTE_UNVALIDATED`다.

Boundary 1 PASS 전 Boundary 2 시작 금지.

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

Step 1 추가 판정:

```text
JMA 기본 값 direct strategy access = implemented
JMA up/down = metadata/비공식 접근만 있어 partial
JMA normalized slope strength = not implemented
numeric intermediate projection = implemented
threshold/permission generic projection = partial
Feature Catalog vs mutable Strategy persistence = physically separate in legacy
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

## 8. 현재 상태

```text
Step 1: COMPLETE
Step 2: COMPLETE
Step 3: COMPLETE / USER-LOCAL PASS
Step 4 Boundary 1 parser migration: WRITTEN / REMOTE_UNVALIDATED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
repository-wide compliance: REMEDIATION_REQUIRED
```

새 executable 변경은 user-local PASS 전 TRUSTED로 부르지 않는다.

---

## 9. 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
python -m unittest discover -s tests -p "test_axis1_parser_parity.py" -v
```

둘 다 PASS하면:

```text
Boundary 1 checkpoint
CURRENT_BOUNDARY -> 2 Function Registry
```

실패 시 먼저 test defect / migration defect / authority drift / environment issue / unknown으로 분류하며 assertion을 약화하지 않는다.
