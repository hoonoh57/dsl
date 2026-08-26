# Quant DSL Current State

Status: **E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
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
11. `E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md` — trusted E6 executable contract.
12. `E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTATION.md` — current E7 executable/UI contract.
13. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — discovery/competition checkpoint.
14. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
15. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and Stage 1 kernel plan.
16. `STAGE1_EXECUTION_POLICY.md` — implementation/verification policy.
17. `QUANT_DSL_PLAYBOOK.md` — generated-DSL language contract.
18. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
19. `PROGRESS_CHECKPOINT_2026-08-26.md` — exact trusted Full checkpoints.

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
 -> ACCEPT / REJECT / REVIEW evidence
 -> append-only evolution memory / explicit head
 -> read-only lineage/evidence UI
 -> later macro attribution/deployment
```

Adaptive learning, parent-context deployment and cross-symbol analysis remain optional seams rather than mandatory Core DSL responsibilities.

## Core DSL freeze and cascading context seam

The governing rule remains:

> **Core DSL Freeze + Adaptive/Analysis Sidecar.**

Core owns deterministic scalar/series calculations, registered indicators/state primitives, causal signals, one declared base timeframe, supported completed higher-timeframe MTF, explicit order intent and reproducible Backtest/Broker semantics.

Core does **not** own online learning, arbitrary peer-symbol reads, cross-symbol ranking, market-regime calculation, sector discovery, leader/follower scans, dynamic lower-timeframe/tick requests, external DB/network calls or portfolio selection logic.

Cascading parent inheritance remains reserved through:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

Still not implemented: general Parent Feature Provider framework, Feature Manifest registry, DSL `ctx.*` grammar/type binding, Runtime Context Binder and production market/sector/group Providers.

Future multi-symbol comparative analysis remains an optional read-only Add-on. No executable multi-symbol deployment selector or DSL parent-context binding exists yet.

## Trusted checkpoints

### E1 Korean regular-session BattleCase Provider

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

Future-only market mutation cannot change an earlier observation's causal prefix identity/features.

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3 Multi-Battle Parameter Seeker

Declared numeric DSL inputs only; frozen BattleCases/context; metric/Pareto evidence; no hidden universal score or automatic promotion.

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

### E4 Causal Failure / Opportunity Characterizer

Causal observation features and later outcome labels remain separately hashed. The first E4 Full failure was classified **environment issue** because the local external Chart SSOT checkout was stale. After Chart fast-forward, the same E4 DSL SHA passed Full without weakening product/tests.

```text
DSL:
560526b7f5af19462a57fd1e5b433bcbe5596500

Chart SSOT:
7a43f0f52928045904d192deb7d8d532cb4c533e

[PASS] Tactical P1 verification completed: mode=Full.
```

### E5 Bounded Structural Skill Generator

Only legal registered one-skill child structures are proposed. No free-form engine mutation, hidden ranking or automatic promotion.

```text
c1351152d58e4219b9998f0b35b7636f340dc986
[PASS] Tactical P1 verification completed: mode=Full.
```

### E6 Validation / Harsh Arena

One fixed parent/child pair is replayed through explicit TRAIN / VALIDATION / OOS / HARSH partitions. TRAIN uses the existing `EvolutionArena`; holdouts use explicit axis tolerances. Default `engagement_collapse` prevents apparent robustness by total holdout abstention when the parent was active. Final ACCEPT remains promotion-eligible evidence only.

Trusted Full checkpoint:

```text
ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E6 is trusted Full-green at `ad87a68a1f8d0595f51a3c02bde022a63ea22cc6`.**

## E7 current executable/UI tranche: Evolution Memory / Evidence UI

Existing `core/tactical_evolution_store.py` remains the append-only authority for:

```text
profiles
failures
generations
Train evolution decisions
explicit family head
```

New `core/tactical_evolution_lineage.py` adds E6 validation evidence preservation plus a deterministic read-only lineage projection.

Projection schema:

```text
tactical_evolution_lineage/v1
```

### E6 validation evidence memory

E7 adds append-only validation evidence keyed by immutable `arena_hash`:

```text
family_id
parent_generation_hash
child_candidate_hash
skill_id
ACCEPT / REJECT / REVIEW
full tactical_validation_arena/v1 payload
```

The same arena hash with different payload fails closed. Recording validation evidence never promotes a family head.

### Accepted lineage contract

The projection validates:

```text
G0 has no parent and no skills
each later generation points to the immediately previous generation
parent acquired_skills remain an exact prefix
exactly one new skill is added per accepted generation
stored generation candidate matches stored profile candidate
explicit head points to a stored generation
```

Malformed stored lineage fails closed rather than being rendered as a plausible tree.

### Evidence shown per generation

```text
new skill
failure_hash / failure tags
Train decision hash
improvements / survival violations
E6 validation arena hash
Validation / OOS / HARSH statuses
compact generation profile metrics
explicit is_head state
```

Rejected/reviewed attempts remain separate from accepted generation nodes.

Projection policy:

```text
READ_ONLY_APPEND_ONLY_EVIDENCE_NO_AUTOMATIC_PROMOTION
```

### Read-only Tactical API/UI

`tactical_main.py` now exposes only:

```text
GET /api/stage1/tactical/evolution/{family_id}
```

No evolution promotion write route was added. The reader is lazy-loaded so importing the Tactical app does not eagerly initialize evolution memory.

The Tactical page now contains a read-only Evolution Skill Tree / Evidence panel showing accepted generations, current explicit head, failure reasons, Train/Validation/OOS/HARSH status and rejected/reviewed attempts.

Browser UI contains no `/promote` operation. Chart SSOT source and chart-document semantics were not changed by E7.

Regression files:

```text
test_stage1_tactical_evolution_lineage.py
test_stage1_tactical_evolution_ui.py
```

Detailed authority:

```text
E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTATION.md
```

This E7 boundary has **not yet received trusted Full validation**.

## Validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- E4 trusted Full PASS at `560526b7f5af19462a57fd1e5b433bcbe5596500` with Chart SSOT `7a43f0f52928045904d192deb7d8d532cb4c533e`;
- E5 trusted Full PASS at `c1351152d58e4219b9998f0b35b7636f340dc986`;
- E6 trusted Full PASS at `ad87a68a1f8d0595f51a3c02bde022a63ea22cc6`;
- E7 source/tests/read-only Tactical UI are implemented awaiting Full;
- Core Freeze / parent-context / multi-symbol Add-on boundaries remain authoritative.

Do **not** claim yet:

- trusted Full PASS for E7;
- that any real JMA generation has passed E6 or been promoted;
- autonomous family-head promotion;
- profitability/generalization/live readiness;
- production-quality harsh universe construction;
- TacticalMemory or trained LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- functioning parent-context DSL binding or multi-symbol deployment selector;
- completed macro attribution/deployment;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Next sequence

After E7 is trusted green:

1. **E8 Macro Context Attribution / Deployment**.

Optional adaptive learning and broader Parent Feature Provider/`ctx.*` binding or Multi-Symbol Add-on execution remain separately gated by concrete need and their own validation.

Do not begin E8 executable work before the E7 Full boundary is trusted green.

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
