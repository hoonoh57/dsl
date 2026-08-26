# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **E5_TRUSTED_FULL_PASS / E6_VALIDATION_HARSH_ARENA_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

## Trusted Full checkpoints

### Earlier E0 / initial foundation

```text
ac01525223f897f155de63f02529b0a6429a0882
[PASS] Tactical P1 verification completed: mode=Full.
```

### E1 Korean regular-session BattleCase contract

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

The initial E2 failure was classified as **test defect** because a 5m regression used a 1d synthetic fixture. Product timeframe fail-close behavior was preserved.

```text
620f741730b0ae821fc48affd22b5420f38a6cac
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3A causal TacticalObservation sidecar

Future-only market mutation may change full BattleCase provenance but cannot change an earlier observation's causal prefix identity or features.

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3 Multi-Battle Parameter Seeker

E3 tunes declared numeric DSL inputs over exactly one frozen BattleCase set. Structure stays fixed; execution settings are not tuned; all candidates remain on the same case/context contract; comparison uses metric leaderboards and Pareto evidence rather than a hidden universal score.

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

### E4 Causal Failure / Opportunity Characterizer

E4 separates signal-time causal observations from later realized labels through distinct `causal_dataset_hash` and `labeled_dataset_hash` identities.

The first E4 Full attempt failed at the external Chart SSOT stable-pane contract. Classification: **environment issue**. The local Chart repo was behind remote `main`; no E4 product source or assertion was weakened.

Verified dependency/checkpoint pair:

```text
DSL:
560526b7f5af19462a57fd1e5b433bcbe5596500

Chart SSOT:
7a43f0f52928045904d192deb7d8d532cb4c533e

[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E4 is trusted Full-green at the DSL SHA above with the verified Chart dependency.

### E5 Bounded Structural Skill Generator

E5 materializes only currently legal registered one-skill child structures through explicit family renderers. It preserves existing family/dependency/CapabilityBudget authority, exposes only catalog-declared numeric parameters, and never ranks or promotes children itself.

The operator synchronized `main`, confirmed exact checkout:

```text
c1351152d58e4219b9998f0b35b7636f340dc986
```

and ran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E5 is trusted Full-green at `c1351152d58e4219b9998f0b35b7636f340dc986`.**

Detailed checkpoint:

```text
E5_BOUNDED_STRUCTURAL_SKILL_GENERATOR_IMPLEMENTATION.md
```

## Stability architecture remains authoritative

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
```

Core remains deterministic and narrow. Parent/cascading intelligence remains preserved through Provider -> immutable Context -> future read-only binding. Arbitrary cross-symbol analysis stays in optional Add-ons. Learned/adaptive components remain sidecars and cannot bypass hard guards/common execution authority.

## E6 executable boundary now added

`core/tactical_validation_arena.py` implements the first **Train / Validation / OOS / Harsh Evolution Arena**.

The E6 flow is:

```text
fixed parent generation/candidate
 + fixed E5 one-skill child candidate
 + parent failure evidence
 + explicit frozen partitions
        ↓
TRAIN replay
VALIDATION replay
OOS replay
HARSH replay(s)
        ↓
Train -> existing EvolutionArena
Holdouts -> declared axis-by-axis contract
        ↓
ACCEPT / REJECT / REVIEW evidence
        ↓
explicit promotion elsewhere only
```

### Partition contract

E6 v1 requires:

```text
exactly 1 TRAIN
exactly 1 VALIDATION
exactly 1 OOS
at least 1 HARSH
```

HARSH partitions require explicit `metadata.adverse_reason`. The arena never guesses or synthesizes harsh cases. E6 v1 also requires BattleCase `case_id` to be globally disjoint across partitions.

### Fixed-child provenance

The child must preserve E5 evidence:

```text
family_id
parent_generation_hash
proposed_skill_id
mutation_policy = ONE_REGISTERED_SKILL_ONLY
failure_hash
```

E3 numeric search remains compatible because it preserves these metadata fields while changing only declared numeric DSL inputs.

### Exact Train lock

TRAIN parent replay must reproduce the parent generation exactly:

```text
run_hash
case_set_hash
context_policy_hash
```

The failure report must also belong to that exact parent generation.

### Train authority

Train adjudication reuses `EvolutionArena.evaluate_upgrade(...)` without changing its one-skill, failure-relevance, CapabilityBudget or survival rules.

### Holdout authority

Validation/OOS/HARSH use a declared `HoldoutContract` across explicit axes:

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

There is no weighted universal score.

Default holdout policy also blocks complete engagement collapse:

```text
parent active_cases > 0
AND child active_cases == 0
 -> engagement_collapse
```

`NO_TRADE` remains valid generally; full-partition abstention can be explicitly allowed only by changing the visible holdout contract.

### Final decision

```text
any holdout FAIL -> REJECT
Train REJECT -> REJECT
Train REVIEW + all holdouts PASS -> REVIEW
Train ACCEPT + all holdouts PASS -> ACCEPT
```

Even final ACCEPT does not change the family head automatically.

```text
PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION
```

### Regression coverage

`test_stage1_tactical_validation_arena.py` covers:

- exact Train generation replay identity;
- holdout blocking of a Train-accepted child that survives only by total abstention;
- explicit abstention-policy override with no hidden score;
- mandatory Train/Validation/OOS/HARSH structure;
- HARSH adverse-reason requirement;
- disjoint partition cases;
- child provenance fail-close behavior;
- partition-order and worker-count determinism;
- no automatic family-head mutation.

Detailed implementation checkpoint:

```text
E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md
```

This E6 executable boundary has **not yet received trusted Full validation**.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- E4 trusted Full PASS at `560526b7f5af19462a57fd1e5b433bcbe5596500` with Chart SSOT `7a43f0f52928045904d192deb7d8d532cb4c533e`;
- E5 trusted Full PASS at `c1351152d58e4219b9998f0b35b7636f340dc986`;
- E6 source/tests are implemented awaiting Full;
- Core DSL Freeze / sidecar/provider/Add-on boundaries remain authoritative.

Do not claim yet:

- trusted Full PASS for E6;
- that any real JMA child has passed generalization;
- a strongest/profitable generated child;
- automatic family-head promotion;
- production-quality harsh-case universe construction;
- E7 lineage UI implementation;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Immediate boundary

Do not begin E7 executable work before E6 is trusted green.

Run:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before editing.
