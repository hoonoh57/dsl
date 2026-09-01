# DSL Strict Sequential Next-Work Order

Status: **ALL PLANNED STEPS COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

이 문서는 프로젝트의 strict sequential 작업 순서 SSOT다.

## 현재 포인터

```text
CURRENT_STEP = COMPLETE
CURRENT_STEP_NAME = Steps 1 through 15 complete
CURRENT_SUBSTEP = NONE
SUBSTEP_STATUS = USER-LOCAL PASS / FINAL CHECKPOINT WRITTEN
```

최종 checkpoint:

```text
STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

## 완료된 순서

```text
Step 1  legacy capability audit
Step 2  AXIS 1 migration manifest/boundaries
Step 3  frozen legacy core guard
Step 4  AXIS 1 migration parity
Step 5  AXIS 1 additive DSL/execution capabilities + verification
Step 6  capability/diagnostic registry
Step 7  common Bridge + AXIS 1 execution contract
Step 8  AXIS 2 exact-as-of snapshot contract
Step 9  AXIS 2 deterministic selection engine
Step 10 AXIS 3 Condition/Strategy CRUD + orchestration
Step 11 AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
Step 12 External LLM proposal-only authoring lane
Step 13 Continuous Improvement evidence-analysis tooling
Step 14 representative natural-language E2E acceptance
Step 15 legacy docs disposition + repo-wide compliance audit
```

모든 Step은 required focused/regression/frozen-core user-local 검증을 통과했고 각 완료 tranche의 checkpoint/evidence가 보존되어 있다.

## 최종 제품 권한

```text
AXIS 1 = deterministic single-instrument DSL/runtime/execution
AXIS 2 = immutable exact-PIT selection semantics + filter/rank/top-N/evidence
AXIS 3 = immutable versioned Condition/Strategy lifecycle + orchestration
Bridge = versioned Request -> Response cross-axis composition
External LLM = proposal only
Continuous Improvement = evidence analysis only; automatic mutation 없음
Chart = supplied result/projection presentation only
```

Condition 책임:

```text
selection semantics = AXIS 2
artifact lifecycle  = AXIS 3
```

최종 실행 순서:

```text
AXIS 2 CandidateSet
 -> AXIS 3 promoted exact artifacts + RunPlan
 -> Bridge all-candidate preflight
 -> AXIS 1 deterministic one-symbol execution
```

## 최종 user-local 검증

```text
test_repo_wide_compliance.py = OK
test_final_natural_language_e2e.py = OK
test_three_axis_e2e_bridge.py = OK
test_axis1_execution_bridge_contract.py = OK
test_axis1_full_engine_parity.py = OK
test_axis2_exact_asof_snapshot.py = OK
test_axis2_selection_engine.py = OK
test_axis3_crud_orchestration.py = OK
test_external_llm_authoring_lane.py = OK
test_authoring_continuous_improvement.py = OK
test_frozen_legacy_core_guard.py = OK
```

## Frozen legacy Core

```text
path = core/
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

영구 금지:

```text
core/ 수정/이동/추가/삭제
AXIS 1/2/3 권한 혼합
cross-axis direct internal state/import dependency
future / nearest / fill-forward / interpolation / default synthesis
특정 전략 Core shortcut
External LLM execution authority
Continuous Improvement automatic mutation
검증완화/skip/compatibility exception
historical 문서를 current SSOT로 부활
```

## 이후 작업 규칙

현재 계획된 remediation sequence는 종료되었다. 이후 기능 추가·버그 수정·제품 변경은 **새 작업**으로 시작하며, 기존 final checkpoints를 재해석하거나 검증을 약화하지 않는다.

새 작업은 현재 active authority를 먼저 확인하고 작은 tranche + focused verification + regression 방식으로 진행한다.
