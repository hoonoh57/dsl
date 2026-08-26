# Quant DSL Current State

Status: **E6_VALIDATION_HARSH_ARENA_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-27 KST

## Authority

Read in this order:

1. `EVOLVING_MICRO_WARRIOR_PLAN.md` — one-skill evolution doctrine, capability budget and immutable-generation contract.
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` — Core DSL stability, sidecar isolation and promotion rules.
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md` — parent-feature calculation outside DSL and future read-only context inheritance.
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md` — single-instrument Core boundary and safe optional cross-symbol Add-on contract.
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` — optional future local-learning design, subordinate to Core Freeze.
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — micro-first research order and macro-ready seam.
7. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final macro-to-micro runtime/deployment architecture.
8. `E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md` — trusted E3 executable contract.
9. `E4_CAUSAL_FAILURE_OPPORTUNITY_CHARACTERIZER_IMPLEMENTATION.md` — trusted E4 executable contract.
10. `E5_BOUNDED_STRUCTURAL_SKILL_GENERATOR_IMPLEMENTATION.md` — trusted E5 executable contract.
11. `E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md` — current E6 executable contract/checkpoint.
12. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — discovery/competition checkpoint.
13. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
14. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and Stage 1 kernel plan.
15. `STAGE1_EXECUTION_POLICY.md` — implementation/verification policy.
16. `QUANT_DSL_PLAYBOOK.md` — generated-DSL language contract.
17. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
18. `PROGRESS_CHECKPOINT_2026-08-26.md` — exact trusted Full checkpoints.

## Product direction

Final deployment remains layered:

```text
Parent battlefield feature providers
 -> BattlefieldContext
 -> Market / Regime
 -> Sector / Group / Narrative
 -> eligible Tactical Unit
 -> optional multi-symbol selection / ranking Add-on
 -> validated evolving micro tactic
 -> common execution policy
 -> BrokerEmulator
```

Current mainline research is:

```text
minimal tactic family
 -> frozen BattleCases
 -> deterministic failure evidence
 -> causal failure/opportunity characterization
 -> one legal structural skill child
 -> Multi-Battle numeric Parameter Seeker where parameters exist
 -> Train / Validation / OOS / harsh replay
 -> ACCEPT / REJECT / REVIEW
 -> immutable generation memory
 -> repeat
 -> later parent-context / Add-on / macro attribution
```

Adaptive learning, parent-context deployment and cross-symbol analysis remain optional seams rather than mandatory Core DSL responsibilities.

## Core DSL freeze

The governing rule remains:

> **Core DSL Freeze + Adaptive/Analysis Sidecar.**

Core owns deterministic scalar/series calculations, registered indicators/state primitives, causal signals, one declared base timeframe, supported completed higher-timeframe MTF, explicit order intent and reproducible Backtest/Broker semantics.

Core does **not** own online learning, arbitrary peer-symbol reads, cross-symbol ranking, market-regime calculation, sector discovery, leader/follower scans, dynamic lower-timeframe/tick requests, external DB/network calls or portfolio selection logic.

A future narrow read-only parent-context binding may be Core-facing, but the calculation that produces the parent value remains outside DSL Runtime.

## Cascading parent-context seam

Cascading feature inheritance remains reserved and authoritative:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

Existing `core/battlefield_context.py` provides the immutable point-in-time envelope. Still not implemented: general Parent Feature Provider framework, Feature Manifest registry, DSL `ctx.*` grammar/type binding, Runtime Context Binder and production market/sector/group Providers.

## Multi-symbol Add-on seam

The Instrument DSL remains the direct single-instrument tactical authority. Future comparative analysis stays behind an optional read-only Add-on and may publish only registered point-in-time parent features or explicit deployment evidence. It cannot mutate DSL/runtime state, guess its universe, use future winner information or place Broker orders directly.

No executable multi-symbol deployment Add-on or DSL parent-context binding exists yet.

## Trusted foundations and checkpoints

### E1 authoritative Korean regular-session BattleCase Provider

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

Current family:

```text
JMA_TREND_CROSS_RESUME_V1
```

Legal bounded skills:

```text
JMA_RANGE_COOLDOWN
JMA_ADX_ENTRY_QUALITY
JMA_CONFIRM_AFTER_RANGE
JMA_FAST_PROFIT_PROTECTION
```

Trusted Full checkpoint:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3A causal TacticalObservation sidecar

Future-only market mutations cannot alter an earlier observation's causal `market_prefix_hash`, feature values or `observation_hash`.

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3 Multi-Battle Parameter Seeker

`core/tactical_parameter_seeker.py` searches declared numeric DSL inputs over one frozen BattleCase set. Execution-setting tuning is rejected; candidate structure is fixed; comparison is metric/Pareto evidence with no hidden universal score or automatic promotion.

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E3 is trusted Full-green** at that SHA.

### E4 Causal Failure / Opportunity Characterizer

`core/tactical_characterization.py` joins actual trade `signal_time` to causal `TacticalObservation`, then attaches later realized return/MFE/MAE/giveback/exit evidence as physically separate future labels.

Key identity split:

```text
causal_dataset_hash
labeled_dataset_hash
```

Changing only future outcome labels must not change `causal_dataset_hash`. E4 is descriptive only: no learner, live gate, hidden score or automatic skill generation.

The first E4 Full attempt failed in the external Chart SSOT stable-pane test. Classification: **environment issue**. The local `cascading-feature-solution` checkout was behind remote `main`; DSL/E4 source and assertions were not modified. After fast-forwarding Chart SSOT, the exact same DSL E4 SHA passed Full.

Trusted dependency/checkpoint pair:

```text
DSL:
560526b7f5af19462a57fd1e5b433bcbe5596500

Chart SSOT:
7a43f0f52928045904d192deb7d8d532cb4c533e

[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E4 is trusted Full-green at `560526b7f5af19462a57fd1e5b433bcbe5596500`** with the verified Chart dependency above.

### E5 Bounded Structural Skill Generator

`core/tactical_skill_generator.py` creates proposal-only one-skill structural children from the registered legal skill tree. Failure relevance, prerequisites/exclusions and CapabilityBudget remain authoritative. The renderer cannot invent DSL capabilities, and E5 cannot rank/promote a child.

Trusted Full checkpoint:

```text
c1351152d58e4219b9998f0b35b7636f340dc986
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E5 is trusted Full-green at `c1351152d58e4219b9998f0b35b7636f340dc986`.**

## E6 current executable tranche: Validation / Harsh Arena

`core/tactical_validation_arena.py` replays one fixed parent/child pair across explicit frozen partitions.

Required partition structure:

```text
TRAIN        exactly 1
VALIDATION   exactly 1
OOS          exactly 1
HARSH        at least 1
```

HARSH partitions must carry explicit `metadata.adverse_reason`. E6 v1 does not guess/synthesize hostile battles and requires partition `case_id` values to be globally disjoint.

### Fixed-child provenance

The child must carry E5 one-skill identity:

```text
family_id
parent_generation_hash
proposed_skill_id
mutation_policy = ONE_REGISTERED_SKILL_ONLY
failure_hash
```

This remains compatible with E3 numeric tuning because E3 preserves those metadata fields while changing only declared numeric DSL inputs.

### Exact Train identity

TRAIN parent replay must reproduce the immutable parent generation:

```text
run_hash == parent_generation.profile_run_hash
case_set_hash == parent_generation.case_set_hash
context_policy_hash == parent_generation.context_policy_hash
```

Mismatch fails closed. Parent failure evidence must also match that exact generation.

### Train adjudication

TRAIN uses the existing `EvolutionArena.evaluate_upgrade(...)` unchanged, preserving one-skill relevance, CapabilityBudget and ACCEPT/REJECT/REVIEW authority.

### Validation / OOS / HARSH adjudication

Non-Train partitions use explicit axis-by-axis `HoldoutContract` tolerances for:

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

No weighted or opaque score exists.

Default contract also prevents a child from manufacturing apparent robustness by never engaging at all:

```text
parent active_cases > 0
AND child active_cases == 0
 -> engagement_collapse
```

This does not redefine `NO_TRADE` as failure. Partial or justified abstention remains valid. Full-partition abstention can be allowed only through an explicit visible contract change.

### Final decision

```text
any holdout FAIL -> REJECT
Train REJECT -> REJECT
Train REVIEW + all holdouts PASS -> REVIEW
Train ACCEPT + all holdouts PASS -> ACCEPT
```

Even final ACCEPT only sets `promotion_eligible=true`; this module does not mutate the family head.

```text
PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION
```

`test_stage1_tactical_validation_arena.py` verifies the partition contract, exact Train identity, E5 child provenance, engagement-collapse protection, explicit abstention-policy override, no hidden score, no automatic head mutation, and deterministic worker/order behavior.

Detailed authority:

```text
E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md
```

This E6 executable boundary has **not yet received trusted Full validation**.

## Validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- E4 trusted Full PASS at `560526b7f5af19462a57fd1e5b433bcbe5596500` with Chart SSOT `7a43f0f52928045904d192deb7d8d532cb4c533e`;
- E5 trusted Full PASS at `c1351152d58e4219b9998f0b35b7636f340dc986`;
- E6 source/tests are implemented awaiting Full;
- Core Freeze / parent-context / multi-symbol Add-on design boundaries remain authoritative.

Do **not** claim yet:

- trusted Full PASS for E6;
- that any real JMA child is stronger, profitable or generalized;
- automatic family-head promotion;
- production-quality harsh-case universe construction;
- E7 Evolution Memory / Evidence UI implementation;
- TacticalMemory or trained LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- functioning parent-context DSL binding or multi-symbol deployment selector;
- live-trading readiness;
- completed macro deployment policy;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Next sequence

After E6 is trusted green:

1. **E7 Evolution Memory / Evidence UI**;
2. **E8 Macro Context Attribution / Deployment**.

Optional adaptive learning, Parent Feature Provider/`ctx.*` binding and Multi-Symbol Add-on execution remain deferred until a concrete mainline need exists.

Do not begin E7 executable work before the E6 Full boundary is trusted green.

## Next automated boundary

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

before changing code.
