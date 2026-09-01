# Quant DSL Current State

Status: **FINAL USER-LOCAL PASS / THREE-AXIS IMPLEMENTATION + REPO COMPLIANCE COMPLETE**  
Updated: 2026-09-01 KST

## Recovery authority

세션 전환 시 읽는 순서:

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. active architecture/policy documents
6. checkpoints/evidence
7. historical documents
```

과거 root 문서와 정적 Feature Catalog가 충돌하면 `DSL_DOCUMENT_AUTHORITY_INDEX.md`의 disposition을 따른다.

## Current branch

```text
dsl-live-studio
```

`main`은 현재 작업 권한이 아니다.

## Final product architecture

```text
AXIS 2 exact-PIT selection
 -> Candidate Set + evidence
 -> AXIS 3 exact promoted Condition/Strategy versions + RunPlan
 -> versioned Bridge all-candidate preflight
 -> AXIS 1 deterministic single-instrument execution
```

권한:

```text
AXIS 1 = DSL parser/semantic/runtime/indicators/state/execution/backtest/projection
AXIS 2 = precomputed immutable PIT snapshot consumption + filter/rank/top-N/evidence
AXIS 3 = Condition/Strategy immutable version lifecycle + lineage + promotion + orchestration
Bridge = data-only contracts + explicit cross-axis composition
External LLM = proposal-only authoring
Continuous Improvement = structured evidence analysis only; automatic mutation 없음
Chart = supplied result/projection 표시; 계산 재구현 없음
```

Condition 책임:

```text
selection semantics = AXIS 2
artifact lifecycle  = AXIS 3
```

## Completed validation

```text
Step 1  legacy capability audit
Step 2  migration manifest/boundaries
Step 3  frozen core guard
Step 4  AXIS 1 migration parity
Step 5  AXIS 1 additive DSL/execution capabilities + parity/reference verification
Step 6  machine-readable capability/diagnostic registry
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

All planned Steps 1–15 are **COMPLETE / USER-LOCAL PASS**.

Final checkpoints:

```text
STEP14_FINAL_NATURAL_LANGUAGE_E2E_CHECKPOINT_2026-09-01.md
STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

## Final user-local regression

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

## AXIS 1 support truth

Migration is complete. New capabilities live under `axes/axis1_dsl/`, never repository-root `core/`.

Current support truth is machine-readable:

```text
axes/axis1_dsl/core/capability_diagnostic_registry.py
```

Historical static Feature Catalog counts are evidence only, not current support authority.

## AXIS 2 current contract

```text
precompute
 -> immutable exact-as-of snapshot
 -> exact knowledge cutoff/formula/source provenance
 -> filter/rank/top-N
 -> CandidateSet + evidence
```

Forbidden:

```text
future values
nearest-time lookup
fill-forward
interpolation
missing-value default synthesis
mixed cutoff/formula versions
order/strategy execution semantics
```

## AXIS 3 current contract

```text
content update -> new immutable version
promotion/rejection/archive -> separate lifecycle event
run plan -> exact promoted versions/hashes + CandidateSet identity
```

AXIS 3 does not parse/execute DSL or reimplement AXIS 2 selection.

## External authoring and improvement

External LLM output is untrusted proposal data. Local deterministic validation owns acceptance and never grants execution authority.

Continuous Improvement aggregates structured validation evidence and emits human-reviewed remediation candidates only. It does not rewrite Prompt/Skill/Validator/DSL automatically.

## Frozen legacy Core

Repository-root `core/` remains immutable forever.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under `core/` is allowed.

## Remaining work

```text
NONE in the completed strict remediation sequence.
```

Future product changes are new work and must preserve the final architecture boundaries, exact PIT rules, fail-closed contracts, deterministic validation, and frozen-Core guard.
