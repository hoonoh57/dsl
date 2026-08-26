# Quant DSL Current State

Status: **E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `EVOLVING_MICRO_WARRIOR_PLAN.md` — one-skill evolution doctrine, capability budget and immutable-generation contract.
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` — Core DSL stability, sidecar isolation and promotion rules.
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md` — parent-feature calculation outside DSL and future read-only context inheritance.
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md` — single-instrument Core boundary and safe optional cross-symbol Add-on contract.
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` — optional future local-learning design, subordinate to Core Freeze.
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — micro-first research order and macro-ready seam.
7. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final macro-to-micro runtime/deployment architecture.
8. `E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md` — current E3 executable contract/checkpoint.
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

Current mainline research remains micro-first and deliberately simple:

```text
minimal tactic family
 -> frozen BattleCases
 -> deterministic failure evidence
 -> capability gap
 -> one-skill child structure
 -> Multi-Battle numeric Parameter Seeker
 -> replay / Validation / OOS / harsh cases
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

Cascading feature inheritance is preserved:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

The DSL may eventually consume registered values such as:

```text
ctx.market.kospi_slope
ctx.market.regime_strength
ctx.sector.strength
ctx.sector.leader_strength
ctx.group.follower_alignment
```

but may not calculate/query the parent world itself.

Existing `core/battlefield_context.py` already provides `ContextLayerSnapshot`, `BattlefieldContext`, point-in-time cutoff validation, context hashes, `NEUTRAL/OBSERVED/DEPLOYMENT` and `DeploymentDecision`.

Still not implemented: general Parent Feature Provider framework, Feature Manifest registry, DSL `ctx.*` grammar/type binding, Runtime Context Binder and production market/sector/group Providers.

## Multi-symbol Add-on seam

The Instrument DSL remains the direct single-instrument tactical authority. Multi-symbol chart display does not create cross-symbol DSL authority.

Future comparative analysis stays behind an optional read-only Add-on:

```text
per-symbol immutable snapshots
 -> optional Multi-Symbol Add-on
 -> ALLOW / BLOCK / PRIORITY evidence
 -> DeploymentDecision / entry_gate style orchestration
 -> common execution policy
 -> BrokerEmulator
```

The Add-on may also act as a Parent Feature Provider and publish only registered point-in-time outputs. It cannot mutate DSL/runtime state, guess its universe, use future winner information or place Broker orders directly.

No executable multi-symbol deployment Add-on or DSL parent-context binding exists yet.

## Trusted foundations

### DSL / execution kernel

Typed Parser/Semantic/Runtime, indicator authority, `BacktestEngine`, `BrokerEmulator`, common execution policy, Stage 1 app and Chart SSOT boundary remain lower-level trust authorities. Tactical/provider/sidecar layers may not bypass them.

### Micro discovery / competition

`core/tactical_discovery.py`:

- immutable `BattleCase` identity by symbol/date/case;
- one tactic across a frozen multi-symbol/multi-date set;
- deterministic bounded parallelism;
- neutral context/uniform execution baseline;
- malformed cases fail the run;
- complete per-case evidence and aggregate survival/opportunity metrics.

`core/tactical_competition.py`:

- same `case_set_hash` and context policy required;
- no hidden universal score;
- metric leaderboards and conservative Pareto frontier.

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

The initial E2 failure was classified as **test defect** because a 5m DSL regression used a 1d synthetic fixture. Product timeframe fail-close behavior was preserved.

Trusted Full checkpoint:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
[PASS] Tactical P1 verification completed: mode=Full.
```

## E3A trusted sidecar checkpoint

`core/tactical_observation.py` is an optional causal observation sidecar, not a new DSL-language responsibility.

It freezes point-in-time JMA/trend/time/volatility/primitive price-geometry evidence from the market prefix only. The final E3A hardening separated full BattleCase provenance from causal observation identity: future-only market mutation may change full `case_hash`, but must not change the earlier `market_prefix_hash`, feature values or `observation_hash`.

The operator verified exact checkout:

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E3A is trusted Full-green at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`.**

## E3 current executable tranche: Multi-Battle Parameter Seeker

`core/tactical_parameter_seeker.py` now implements numeric parameter search over one frozen BattleCase set.

Core contract:

```text
base TacticCandidate
 + declared numeric DSL inputs
 + frozen BattleCases
        ↓
grid/random deterministic plan
        ↓
replace declared DSL input values only
        ↓
TacticalDiscoveryEngine per candidate
        ↓
same case_set_hash / context policy
        ↓
TacticalCompetitionEngine
        ↓
metric leaderboards + Pareto frontier
```

Important restrictions:

- E3 v1 accepts only `ParameterSpec(target="dsl")`;
- execution-setting parameters are rejected because they would change the frozen comparison contract;
- no arbitrary expression/structure mutation;
- no hidden `MAX_RETURN`/`ROBUST_SCORE` promotion authority;
- no automatic family-head promotion;
- worker count must not alter seek identity or comparison evidence.

`test_stage1_tactical_parameter_seeker.py` verifies frozen-case identity, Pareto/no-score behavior, worker invariance, deterministic seeded random plans and rejection of execution-setting tuning.

This E3 executable boundary has **not yet received trusted Full validation**.

## Validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- Core Freeze / parent-context / multi-symbol Add-on design boundaries are authoritative;
- E3 Multi-Battle Parameter Seeker source/tests are implemented.

Do **not** claim yet:

- trusted Full PASS for E3;
- strongest/profitable parameter set or generalization;
- automatic parameter promotion;
- E4 Failure Characterizer implementation;
- TacticalMemory or trained LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- functioning parent-context DSL binding or multi-symbol deployment selector;
- live-trading readiness;
- completed macro deployment policy;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Next sequence

After E3 is trusted green:

1. **E4 Causal Failure / Opportunity Characterizer**;
2. **E5 Bounded Structural Skill Generator**;
3. **E6 Train / Validation / OOS / Harsh Evolution Arena**;
4. **E7 Evolution Memory / Evidence UI**;
5. **E8 Macro Context Attribution / Deployment**.

Optional adaptive learning, Parent Feature Provider/`ctx.*` binding and Multi-Symbol Add-on execution remain deferred until a concrete mainline need exists.

Do not begin E4 executable work before the E3 Full boundary is trusted green.

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
