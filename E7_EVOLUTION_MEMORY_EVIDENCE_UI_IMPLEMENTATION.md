# E7 Evolution Memory / Evidence UI — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

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

## 3. New lineage/evidence layer

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

Each validation row records:

```text
family_id
arena_hash
parent_generation_hash
child_candidate_hash
skill_id
decision
full tactical_validation_arena/v1 payload
created_at
```

The same `arena_hash` may be recorded repeatedly only when its complete payload is identical. Different evidence under the same immutable hash fails closed.

## 4. Validation evidence contract

`record_validation(...)` accepts only:

```text
schema == tactical_validation_arena/v1
family_id matches requested family
parent generation exists in the family
ACCEPT / REJECT / REVIEW only
promotion_eligible == (decision == ACCEPT)
```

For ACCEPT, the carried `accepted_generation` must point back to the exact parent generation and exact child candidate.

For REJECT/REVIEW, an accepted generation payload is forbidden.

Recording E6 evidence never calls `promote()`.

## 5. Read-only lineage projection

`TacticalEvolutionLineage.build(family_id)` reads append-only evidence and produces:

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

The deterministic `lineage_hash` includes accepted lineage identity, attempts and the explicit current head.

## 6. Accepted generation nodes

Each node exposes:

```text
generation_index
generation_hash
parent_generation_hash
candidate_hash
profile_run_hash
acquired_skills[]
new_skill
capability_usage
is_head
profile_summary
acquisition_evidence
```

`acquisition_evidence` exposes the causal reason/evidence chain without inventing a score:

```text
failure_hash
failure_tags[]
decision_hash
decision improvements[]
decision survival violations[]
validation arena hash
Validation / OOS / HARSH statuses
```

Generation 0 must have no parent and no acquired skills.

Every later accepted generation must preserve its parent's acquired-skill prefix and add exactly one skill. A malformed stored lineage fails closed at projection time rather than being rendered as a plausible skill tree.

## 7. Attempts remain separate from accepted lineage

Rejected and reviewed children are evidence, not generations.

`attempts[]` exposes:

```text
parent_generation_hash
child_candidate_hash
skill_id
Train decision / decision_hash
failure_hash
improvements[]
survival_violations[]
validation arena / holdout result
promoted_generation_hash if it actually exists in accepted lineage
```

This preserves the difference between:

```text
ACCEPT evidence
promotion eligible
recorded accepted generation
explicit current family head
```

Those concepts are not collapsed into one boolean.

## 8. Tactical read API

`tactical_main.py` now exposes:

```text
GET /api/stage1/tactical/evolution/{family_id}
```

The endpoint returns only the read-only lineage projection.

No POST/PUT/DELETE promotion endpoint is introduced in E7.

The lineage service is lazy-loaded so importing the Tactical application does not eagerly initialize evolution memory.

The tactical health endpoint advertises:

```text
evolution_lineage_read_only
```

## 9. Evidence UI

The existing Tactical page receives a read-only Evolution panel through:

```text
core/templates/tactical.html
core/static/tactical.js
```

The UI shows:

```text
current explicit head
lineage hash
Generation rows
new skill per generation
failure tags
Train / Validation / OOS / HARSH status
profile average return / worst MDD
attempt rows
holdout failures
whether an attempt became an accepted generation
```

The browser code contains no `/promote` call and no family-head mutation control.

Chart rendering authority remains the external Chart SSOT. E7 does not change chart-document semantics or Chart SSOT source code.

## 10. Regression coverage

`test_stage1_tactical_evolution_lineage.py` verifies:

- accepted one-skill lineage projection;
- why-skill-acquired failure/decision/validation evidence;
- explicit head remains unchanged by projection;
- head changes only after explicit store promotion;
- append-only/idempotent E6 validation evidence;
- invalid family/promotion eligibility fails closed;
- rejected validation evidence does not move head;
- deterministic lineage identity.

`test_stage1_tactical_evolution_ui.py` verifies:

- GET-only lineage API contract;
- no Tactical evolution promotion route;
- no UI `/promote` action;
- Generation and Attempts panels are present;
- health exposes the read-only capability.

The Tactical P1 Full verifier discovers both tests through `test_stage1_*.py`.

## 11. Mutation boundary

E7 does not modify:

```text
Parser
Semantic
Runtime
TA/indicator authority
Backtest accounting
BrokerEmulator
BattleCase semantics
E3 numeric seeker
E4 characterizer
E5 structural renderer
E6 validation adjudication
family skill catalog
```

E7 adds memory projection/API/UI only.

## 12. Nonclaims

This tranche does **not** establish:

- that a real JMA generation has been promoted through E6;
- autonomous family-head promotion;
- production-quality evolution operations/authorization;
- profitability or live readiness;
- trained adaptive learner;
- parent-context DSL binding;
- functioning multi-symbol deployment selector;
- macro context attribution;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains a separate broader repository status.

## 13. Next boundary

Do not begin E8 Macro Context Attribution / Deployment executable work until this E7 executable/UI boundary receives trusted Full validation at an exact repository SHA.
