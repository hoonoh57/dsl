# Quant DSL Current State

Status: **E3_MULTI_BATTLE_PARAMETER_SEEKER_TRUSTED_FULL_PASS / E4_CAUSAL_CHARACTERIZER_NEXT / REMEDIATION_REQUIRED**  
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
8. `E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md` — trusted E3 executable contract/checkpoint.
9. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — discovery/competition checkpoint.
10. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
11. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and Stage 1 kernel plan.
12. `STAGE1_EXECUTION_POLICY.md` — implementation/verification policy.
13. `QUANT_DSL_PLAYBOOK.md` — generated-DSL language contract.
14. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
15. `PROGRESS_CHECKPOINT_2026-08-26.md` — trusted Full PASS checkpoints.

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

Current mainline research remains micro-first:

```text
minimal tactic family
 -> frozen BattleCases
 -> deterministic failure evidence
 -> capability gap
 -> one-skill child structure
 -> Multi-Battle numeric Parameter Seeker
 -> causal failure/opportunity characterization
 -> bounded one-skill generation
 -> Validation / OOS / harsh replay
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

Cascading feature inheritance remains preserved:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

Existing `core/battlefield_context.py` already provides `ContextLayerSnapshot`, `BattlefieldContext`, cutoff validation, context hashes, `NEUTRAL/OBSERVED/DEPLOYMENT` and `DeploymentDecision`.

Still not implemented: general Parent Feature Provider framework, Feature Manifest registry, DSL `ctx.*` grammar/type binding, Runtime Context Binder and production market/sector/group Providers.

## Multi-symbol Add-on seam

The Instrument DSL remains the direct single-instrument tactical authority. Multi-symbol chart display does not create cross-symbol DSL authority.

Future comparative analysis stays behind an optional read-only Add-on and may publish only registered point-in-time parent features or explicit deployment evidence. It cannot mutate DSL/runtime state, guess its universe, use future winner information or place Broker orders directly.

No executable multi-symbol deployment Add-on or DSL parent-context binding exists yet.

## Trusted foundations

### DSL / execution kernel

Typed Parser/Semantic/Runtime, indicator authority, `BacktestEngine`, `BrokerEmulator`, common execution policy, Stage 1 app and Chart SSOT boundary remain lower-level trust authorities. Tactical/provider/sidecar layers may not bypass them.

### Micro discovery / competition

`core/tactical_discovery.py` provides immutable `BattleCase` identity, one tactic across a frozen multi-symbol/multi-date set, deterministic bounded parallelism, neutral context/uniform execution baseline, fail-closed malformed cases and complete per-case evidence.

`core/tactical_competition.py` requires the same `case_set_hash` and context policy and exposes metric leaderboards plus a conservative Pareto frontier without a hidden universal score.

### E0 evolving micro-warrior

Trusted contracts include deterministic failure analysis, `SkillSpec`, `CapabilityBudget`, immutable `EvolutionGeneration`, exactly one new skill per child, conservative ACCEPT/REJECT/REVIEW and append-only evolution evidence.

`NO_TRADE` is abstention by default. Entered unresolved positions remain active failure evidence.

### E1 authoritative Korean regular-session BattleCase Provider

Trusted Full checkpoint:

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

### E3A trusted causal observation sidecar

`core/tactical_observation.py` freezes point-in-time JMA/trend/time/volatility/primitive price-geometry evidence from the market prefix only. Future-only market mutations cannot alter the earlier causal `market_prefix_hash`, feature values or `observation_hash`.

Trusted Full checkpoint:

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3 trusted Multi-Battle Parameter Seeker

`core/tactical_parameter_seeker.py` searches declared numeric DSL inputs over one frozen BattleCase set.

Contract:

```text
fixed candidate structure
 + declared numeric DSL inputs
 + frozen BattleCases
 -> deterministic grid/random plan
 -> TacticalDiscoveryEngine per candidate
 -> same case_set_hash/context policy
 -> TacticalCompetitionEngine
 -> metric leaderboards + Pareto frontier
```

Restrictions:

- only DSL `input` parameters are tunable in E3 v1;
- execution-setting tuning is rejected;
- no arbitrary expression/structure mutation;
- no hidden universal score;
- no automatic family-head promotion;
- worker count may not alter seek identity or comparison evidence.

The operator reported Full PASS and exact local checkout:

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E3 is trusted Full-green at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`.**

## E4 next executable tranche: causal Failure / Opportunity Characterizer

E4 may now begin.

The first E4 tranche must remain descriptive and evidence-only. The intended join is:

```text
actual trade signal_time
 -> causal TacticalObservation built only from information known at that timestamp
 -> future realized outcome stored separately as label/evidence
 -> deterministic strata showing where failures/opportunities repeat
```

Required boundary:

```text
causal_features
!=
future_outcome_labels
```

Future return/MFE/MAE/giveback/exit outcome may be used only after the event as a research label. They must never appear inside the causal feature map or be used to reconstruct the earlier observation.

Initial E4 should prefer a compact, explicit feature set covering time position, trend/range geometry, volatility, volume/liquidity proxy, overextension and primitive structure. It must not create a learner, hidden score, live gate or new skill automatically.

## Validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- Core Freeze / parent-context / multi-symbol Add-on design boundaries are authoritative.

Do **not** claim yet:

- E4 implementation or trusted Full PASS;
- strongest/profitable parameter set or generalization;
- automatic parameter/skill promotion;
- TacticalMemory or trained LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- functioning parent-context DSL binding or multi-symbol deployment selector;
- live-trading readiness;
- completed macro deployment policy;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Next sequence

1. **E4 Causal Failure / Opportunity Characterizer**;
2. **E5 Bounded Structural Skill Generator**;
3. **E6 Train / Validation / OOS / Harsh Evolution Arena**;
4. **E7 Evolution Memory / Evidence UI**;
5. **E8 Macro Context Attribution / Deployment**.

Optional adaptive learning, Parent Feature Provider/`ctx.*` binding and Multi-Symbol Add-on execution remain deferred until a concrete mainline need exists.
