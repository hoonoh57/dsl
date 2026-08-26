# E7 Evolution Memory / Evidence UI — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## 1. Trusted predecessor

E6 Validation / Harsh Arena was operator-validated at exact DSL checkout:

```text
ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E6 is trusted Full-green at that SHA.

## 2. E7 objective

E7 turns the append-only evolution ledger into a deterministic, inspectable lineage without creating a second promotion authority.

The evidence flow is:

```text
TacticalEvolutionStore
  profiles
  failures
  generations
  train decisions
  explicit family head
        +
E6 validation-arena evidence
        ↓
read-only lineage projection
        ↓
Generation skill tree
 + failed/reviewed attempts
 + why each accepted skill was acquired
 + Train / Validation / OOS / HARSH evidence
 + explicit current head
        ↓
read-only Tactical UI
```

A displayed ACCEPT or `promotion_eligible=true` does not move the family head. Head mutation remains an explicit `TacticalEvolutionStore.promote(...)` operation outside the E7 read API/UI.

## 3. Lineage/evidence layer

`core/tactical_evolution_lineage.py`

Projection schema:

```text
tactical_evolution_lineage/v1
```

The layer wraps the existing `TacticalEvolutionStore` rather than replacing it.

Existing append-only authorities remain:

```text
evolution_profiles
evolution_failures
evolution_generations
evolution_decisions
evolution_heads
```

E7 additionally preserves E6 results in an append-only validation evidence table:

```text
evolution_validation_arenas
```

Each validation row records family, immutable `arena_hash`, parent generation, child candidate, skill, final decision and the full `tactical_validation_arena/v1` payload. The same `arena_hash` may be repeated only with an identical payload; mismatched evidence fails closed.

## 4. Validation evidence contract

`record_validation(...)` accepts only evidence whose family and parent generation exist and match. `promotion_eligible` must equal `(decision == ACCEPT)`. ACCEPT must carry an accepted generation pointing to the exact parent and child; REJECT/REVIEW may not carry one.

Recording E6 evidence never calls `promote()`.

## 5. Read-only lineage projection

`TacticalEvolutionLineage.build(family_id)` returns:

```text
family_id
head_generation_hash
nodes[]
attempts[]
summary
projection_policy
lineage_hash
```

Projection policy:

```text
READ_ONLY_APPEND_ONLY_EVIDENCE_NO_AUTOMATIC_PROMOTION
```

The projection re-validates immutable one-skill lineage at read time. Generation 0 has no parent or acquired skills. Every later accepted generation must point to the previous generation, preserve the parent's acquired-skill prefix, and add exactly one skill. Stored generation/profile candidate identities must match. Malformed stored lineage fails closed.

## 6. Evidence exposed per generation

Each node exposes generation/candidate/profile identity, parent generation, acquired skills, exactly one new skill, capability usage, explicit head state, compact profile metrics and acquisition evidence.

Acquisition evidence keeps the causal chain visible:

```text
failure_hash / failure tags
Train decision / decision hash
improvements / survival violations
E6 arena hash
Validation / OOS / HARSH statuses
```

Rejected and reviewed attempts remain outside accepted lineage nodes.

## 7. Tactical read API / UI

`tactical_main.py` exposes only:

```text
GET /api/stage1/tactical/evolution/{family_id}
```

No promotion write endpoint was added. The lineage reader is lazy-loaded so importing the Tactical application does not eagerly initialize evolution memory.

The Tactical page shows explicit head, lineage hash, accepted generations, new skills, failure tags, Train/Validation/OOS/HARSH evidence, compact return/MDD evidence, and rejected/reviewed attempts. Browser code contains no `/promote` operation.

Chart rendering remains under the external Chart SSOT; E7 does not change Chart Document semantics or Chart SSOT source.

## 8. Regression coverage

```text
test_stage1_tactical_evolution_lineage.py
test_stage1_tactical_evolution_ui.py
```

Coverage includes append-only validation evidence, one-skill lineage integrity, explicit-head semantics, deterministic lineage hash, GET-only API/UI behavior and absence of automatic promotion controls.

## 9. Mutation boundary

E7 does not modify Parser, Semantic, Runtime, indicators, Backtest accounting, BrokerEmulator, BattleCase semantics, E3 seeker, E4 characterizer, E5 renderer, E6 adjudication, or the family skill catalog.

## 10. Trusted Full checkpoint

The operator fast-forwarded to the exact E7 boundary and confirmed:

```text
dc420d7f7961a4f0517b00c059d159b8face706c
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E7 is trusted Full-green at `dc420d7f7961a4f0517b00c059d159b8face706c`.**

## 11. Nonclaims

This checkpoint does not establish that a real JMA generation has been promoted through E6, autonomous family-head promotion, profitability/generalization/live readiness, trained adaptive learning, parent-context DSL binding, functioning multi-symbol deployment selection, or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains a separate broader repository status.

## 12. Next boundary

E8 Macro Context Attribution / Deployment may begin only from the trusted E7 checkpoint above. E8 must preserve historical micro evidence and use point-in-time parent context as an external attribution/command layer rather than rewriting the Instrument DSL or trusted execution engine.
