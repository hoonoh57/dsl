# Quant DSL Current State

Status: **THREE-AXIS IMPLEMENTATION COMPLETE THROUGH STEP 14 / FINAL REPO COMPLIANCE AUDIT PENDING USER-LOCAL PASS**  
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
 -> AXIS 3 exact promoted Condition/Strategy versions + run plan
 -> versioned Bridge
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

Condition은 두 책임을 섞지 않는다.

```text
selection semantics = AXIS 2
artifact lifecycle  = AXIS 3
```

## Completed validation

User-local PASS가 확인된 순서:

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
Step 13 continuous-improvement evidence analysis tooling
Step 14 representative natural-language E2E acceptance
```

Step 14 checkpoint:

```text
STEP14_FINAL_NATURAL_LANGUAGE_E2E_CHECKPOINT_2026-09-01.md
```

## AXIS 1 current capabilities

Migration is complete. New capabilities live under `axes/axis1_dsl/`, not repository-root `core/`.

Representative additive capabilities include:

```text
typed multi-output lowering
generic projection
machine-readable capability metadata/diagnostics
pure user-defined functions
bounded loops
on_tick/on_fill provisional lifecycle
partial fills/exits
same-direction pyramiding / multi-lot accounting
full reference differential fixtures
batch/stream full-engine parity verification
```

Current support truth is machine-readable:

```text
axes/axis1_dsl/core/capability_diagnostic_registry.py
```

Static historical Feature Catalog counts are not current support authority.

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

AXIS 3 stores immutable versioned Condition/Strategy artifacts and lifecycle state.

```text
content update -> new immutable version
promotion/rejection/archive -> separate lifecycle event
run plan -> exact promoted versions/hashes + CandidateSet identity
```

AXIS 3 does not parse/execute DSL or reimplement AXIS 2 selection.

## External authoring and improvement

External LLM output is untrusted proposal data. Local deterministic validation owns acceptance and never grants execution authority.

Continuous-improvement tooling aggregates structured validation evidence and emits human-reviewed remediation candidates only. It does not rewrite Prompt/Skill/Validator/DSL automatically.

## Frozen legacy Core

Repository-root `core/` remains immutable forever.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under `core/` is allowed.

## Current remaining work

Only Step 15 remains:

```text
legacy docs disposition
+ active authority alignment
+ current product-surface import/boundary audit
+ Bridge contract isolation audit
+ critical-test no-skip audit
+ frozen core guard regression
+ final user-local regression
```

Repo-wide final PASS must not be claimed until Step 15 focused audit and frozen-core regression are user-local `OK` and the final checkpoint is written.
