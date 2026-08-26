# E6 Validation / Harsh Arena — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

E5 Bounded Structural Skill Generator was operator-validated at exact DSL checkout:

```text
c1351152d58e4219b9998f0b35b7636f340dc986
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E5 is trusted Full-green at that SHA.

## 2. E6 objective

E6 must stop a child from becoming the new family head merely because it looks good on the frozen training battles that produced it.

The executable seam is:

```text
one fixed parent generation/candidate
 + one fixed E5 child candidate
 + one registered SkillSpec
 + parent failure evidence
 + explicit Train / Validation / OOS / HARSH BattleCase partitions
        ↓
replay parent and child on every partition
        ↓
Train: existing EvolutionArena ACCEPT / REJECT / REVIEW
Validation/OOS/HARSH: declared axis-by-axis holdout contract
        ↓
final ACCEPT / REJECT / REVIEW evidence
        ↓
explicit promotion may happen elsewhere
```

E6 does not tune parameters, generate new structure or mutate the family head.

## 3. New executable

`core/tactical_validation_arena.py`

Schema:

```text
tactical_validation_arena/v1
```

Primary types:

```text
ValidationPartition
HoldoutContract
TacticalValidationArena
```

## 4. Explicit partition contract

E6 v1 requires:

```text
exactly one TRAIN
exactly one VALIDATION
exactly one OOS
one or more HARSH partitions
```

Every partition contains explicit frozen `BattleCase` objects. E6 never guesses, downloads, synthesizes or silently substitutes battles.

HARSH partitions must declare:

```text
metadata.adverse_reason
```

Examples may later include persistent trend-against-tactic sessions, range/whipsaw clusters, high-cost/slippage contracts, poor-liquidity sessions or other deliberately hostile but explicitly sourced cases.

E6 v1 requires `case_id` to be globally disjoint across all partitions. A future overlap policy, if needed, must be explicit and separately validated rather than silently reusing the same battle as both training and holdout evidence.

## 5. Fixed-child provenance lock

Before replay, the child must carry the E5 one-skill provenance:

```text
child.metadata.family_id == parent_generation.family_id
child.metadata.parent_generation_hash == parent_generation.generation_hash
child.metadata.proposed_skill_id == skill.skill_id
child.metadata.mutation_policy == ONE_REGISTERED_SKILL_ONLY
child.metadata.failure_hash == failure_report.failure_hash
```

E3 numeric tuning is compatible because the seeker preserves the E5 metadata while changing only declared numeric DSL inputs.

The child may not be replaced or structurally changed after holdout evidence is observed.

## 6. Train identity lock

The TRAIN partition is not merely another similar sample. Replaying the parent on TRAIN must reproduce the exact immutable parent-generation authority:

```text
TRAIN parent run_hash == parent_generation.profile_run_hash
TRAIN parent case_set_hash == parent_generation.case_set_hash
TRAIN parent context policy hash == parent_generation.context_policy_hash
```

Any mismatch fails closed.

The parent failure report must also match that exact generation/run/case-set identity.

## 7. Train adjudication

TRAIN uses the existing `EvolutionArena.evaluate_upgrade(...)` unchanged.

Therefore the trusted one-skill contract still enforces:

- same frozen Train case set for parent and child;
- observed failure relevance;
- `CapabilityBudget`;
- one-skill generation accounting;
- mission/survival improvement;
- no hidden universal score;
- ACCEPT / REJECT / REVIEW.

E6 does not weaken or replace this authority.

## 8. Holdout adjudication

Validation, OOS and HARSH are judged independently through a declared `HoldoutContract`.

Current axes are:

```text
average_return_pct
median_return_pct
profitable_case_rate
worst_mdd_pct
worst_case_return_pct
cost_per_case
average_mfe_giveback_pct
top1_positive_return_concentration
```

Each axis has an explicit maximum regression tolerance. Default tolerance is zero, meaning a caller must deliberately relax a boundary rather than receiving an implicit weighted trade-off.

There is no combined score.

Output policy:

```text
DECLARED_AXES_NO_HIDDEN_UNIVERSAL_SCORE
```

## 9. Engagement-collapse guard

`NO_TRADE` remains valid survival behavior. E6 therefore does not require the child to trade every battle or to preserve the parent's trade count.

However the default holdout contract rejects this pathological shortcut:

```text
parent has active cases
AND child has zero active cases in the entire holdout partition
 -> engagement_collapse
```

This prevents a child from passing generalization solely by refusing every holdout fight.

If a future mission explicitly wants complete abstention to be acceptable, the caller must set:

```text
require_child_activity_if_parent_active = false
```

That policy change is visible in evidence; it is never hidden in a score.

## 10. Final decision

Final E6 decision is deterministic:

```text
any holdout FAIL -> REJECT
Train REJECT -> REJECT
Train REVIEW and no holdout FAIL -> REVIEW
Train ACCEPT and every holdout PASS -> ACCEPT
```

An ACCEPT produces a `promotion_eligible=true` result and carries the child `EvolutionGeneration` created by the Train arena.

It still does **not** mutate the family head.

Head policy:

```text
PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION
```

This leaves append-only lineage/promotion authority to the explicit evolution-memory layer.

## 11. Determinism

Partitions are normalized in stable role order:

```text
TRAIN
VALIDATION
OOS
HARSH ordered by partition_id
```

Worker count and caller partition ordering may not change replay identities or `arena_hash`.

Each partition records:

```text
partition_id
role
metadata
case_ids
case_set_hash
parent profile/run hash
child profile/run hash
adjudication
partition_hash
```

Top-level evidence records deterministic `arena_hash`.

## 12. Regression coverage

`test_stage1_tactical_validation_arena.py` verifies:

- exact Train generation replay contract;
- Train ACCEPT can still be blocked by holdout `engagement_collapse`;
- an explicit contract may allow full abstention without introducing a hidden score;
- ACCEPT never changes the family head automatically;
- Train/Validation/OOS/HARSH roles are mandatory;
- HARSH requires `adverse_reason`;
- v1 partition BattleCases are globally disjoint;
- child E5 provenance mismatch fails closed;
- worker count and caller partition order do not change arena identity.

The existing Tactical P1 verifier discovers this file through `test_stage1_*.py`.

## 13. Mutation boundary

E6 adds no changes to:

```text
Parser
Semantic
Runtime
TA/indicator authority
Backtest accounting
BrokerEmulator
BattleCase provider semantics
family skill catalog
E3 parameter search semantics
E5 renderer semantics
```

It is orchestration/evidence infrastructure only.

## 14. Nonclaims

This tranche does **not** establish:

- that any real JMA child has passed Train/Validation/OOS/HARSH;
- that an accepted fixture child is profitable or production-ready;
- automatic family-head promotion;
- production-quality harsh-case universe construction;
- trained adaptive learner;
- parent-context DSL binding;
- live-trading readiness;
- repository-wide compliance PASS.

## 15. Next boundary

Do not begin E7 Evolution Memory / Evidence UI until this E6 executable boundary receives trusted Full validation at an exact repository SHA.
