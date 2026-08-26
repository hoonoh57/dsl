# Quant DSL Current State

Status: **E3A_SIDECAR_OBSERVATION_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `EVOLVING_MICRO_WARRIOR_PLAN.md` — one-skill evolution doctrine, capability-budget and immutable-generation contract.
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` — Core DSL stability, sidecar isolation and promotion rules.
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md` — parent feature calculation outside DSL and future read-only context inheritance contract.
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md` — single-instrument Core boundary and safe optional cross-symbol Add-on contract.
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` — optional future local-learning design, subordinate to the Core DSL freeze policy.
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — micro-first research order and macro-ready extension seam.
7. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final macro-to-micro runtime/deployment architecture.
8. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — micro discovery/competition implementation checkpoint.
9. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
10. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and Stage 1 kernel plan.
11. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification policy.
12. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
13. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
14. `PROGRESS_CHECKPOINT_2026-08-26.md` — trusted local Full PASS evidence checkpoints.

## Product direction

Final runtime/deployment remains top-down:

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

The main research/development path remains deliberately simple:

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
 -> later optional parent-context / Add-on / macro attribution and deployment
```

Adaptive learning, parent-context deployment and cross-symbol analysis are not mandatory steps in this critical path. They remain reserved sidecar/provider/Add-on seams that may consume immutable evidence without changing Core DSL calculation authority.

## Core DSL freeze policy

The project follows:

> **Core DSL Freeze + Adaptive/Analysis Sidecar.**

Core responsibilities remain intentionally narrow:

- deterministic scalar/series computation;
- registered indicators and state primitives;
- causal signals;
- one declared base timeframe per candidate;
- supported completed higher-timeframe MTF reads;
- explicit order intent;
- reproducible Backtest/Broker execution semantics;
- one instrument tactical execution context at a time;
- future read-only consumption of explicitly registered parent-context values through a narrow binding contract.

The Core DSL must not absorb online model training, memory databases, arbitrary ML/RL calls, runtime self-modification, dynamic lower-timeframe/tick requests, live self-switching of the declared timeframe, arbitrary peer-symbol reads, cross-symbol ranking, universe selection, portfolio allocation, market-regime calculation, sector discovery or leader/follower analysis merely because those capabilities may be useful later.

New requirements are classified first as:

```text
A. Core DSL capability
B. Tactical infrastructure / Provider
C. Experimental adaptive / analysis sidecar
```

If a calculation can be implemented outside Parser / Runtime / Backtest / Broker, it stays outside Core. Only a narrowly typed, deterministic read-only reference to an already-frozen parent value may later qualify as a Core-facing capability.

## Parent-context inheritance policy

Cascading parent intelligence is explicitly preserved.

The Instrument DSL is a single-instrument **calculation authority**, but it may later consume verified parent battlefield features without knowing or executing their calculation logic.

The reserved seam is:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

Conceptual future references may include:

```text
ctx.market.kospi_slope
ctx.market.regime_strength
ctx.sector.strength
ctx.sector.leader_strength
ctx.group.follower_alignment
```

Important boundary:

```text
DSL may read a registered parent value
!=
DSL may query or calculate the parent world
```

Therefore DSL execution must not perform database/network calls, symbol discovery, peer scans, sector ranking or Provider function execution. Parent calculations belong to Provider/Add-on modules.

Existing `core/battlefield_context.py` already supplies the immutable envelope primitives:

- `ContextLayerSnapshot`;
- `BattlefieldContext`;
- point-in-time `as_of <= knowledge_cutoff` validation;
- context/snapshot hashes;
- `NEUTRAL / OBSERVED / DEPLOYMENT` modes;
- `DeploymentDecision`.

Not implemented yet:

- general Parent Feature Provider framework;
- Parent Feature Manifest registry;
- Instrument DSL `ctx.*` grammar/type binding;
- runtime Context Binder;
- concrete production market/sector/group Providers.

These are reserved future seams, not current executable claims. The detailed authority is `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`.

## Multi-symbol Add-on policy

The Instrument DSL remains a **single-instrument tactical authority** for direct market-series access.

```text
multi-symbol chart display
!=
multi-symbol Instrument DSL authority
```

A future cross-symbol analyzer may be added safely only as an optional Add-on. The intended seam is:

```text
single-instrument DSL / tactic evaluation
 -> immutable point-in-time InstrumentSignalSnapshot per symbol
 -> optional read-only Multi-Symbol Add-on
 -> explicit ALLOW / BLOCK / PRIORITY evidence
 -> DeploymentDecision / entry_gate style orchestration
 -> common execution policy
 -> BrokerEmulator
```

A Multi-Symbol Add-on may also act as a Parent Feature Provider and publish only registered outputs such as sector breadth, leader strength or follower alignment into `ContextLayerSnapshot`. That does not grant direct peer-symbol DSL syntax.

Required safety rules:

- Add-on disabled by default in neutral micro discovery;
- explicit universe and source authority; no universe guessing;
- all snapshots aligned to the same declared `as_of` / knowledge cutoff;
- future/end-of-day winner information prohibited;
- missing/stale/mismatched snapshots handled explicitly and fail closed;
- deterministic ranking fields and tie-breaks;
- Add-on is read-only with respect to DSL/runtime state;
- Add-on cannot place Broker orders directly;
- Add-on cannot bypass local hard guards or common execution policy;
- removing/replacing the Add-on must not change Instrument DSL syntax, Parser/Runtime, Backtest accounting or historical single-instrument TacticalProfiles.

The detailed authority is `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`.

No multi-symbol Add-on executable or parent-context DSL binding has been introduced in the current tranche; only extension boundaries are documented.

## Trusted foundations

### DSL / execution kernel

The typed DSL parser/runtime, indicator implementation, `BacktestEngine`, `BrokerEmulator`, common execution policy, Stage 1 app and Chart SSOT boundary remain trusted lower-level authorities. Tactical, adaptive, parent-context or multi-symbol layers may not bypass or self-modify them.

### Micro discovery / competition

`core/tactical_discovery.py`

- `BattleCase` identity separates symbol/date/case;
- one tactic executes over frozen multi-symbol/multi-date cases;
- bounded workers preserve deterministic order/hashes;
- neutral-context baseline and uniform execution settings are enforced;
- malformed cases fail the run;
- complete per-case Backtest evidence remains immutable.

`core/tactical_competition.py`

- only tactics with the same frozen `case_set_hash` and context policy compete;
- no hidden universal score;
- per-metric leaderboards and conservative Pareto evidence remain authoritative.

### E0 evolving micro-warrior contracts

Implemented and previously trusted:

- deterministic failure analysis;
- `SkillSpec` and `CapabilityBudget`;
- immutable `EvolutionGeneration`;
- one-skill `EvolutionArena`;
- conservative ACCEPT / REJECT / REVIEW;
- append-only evolution evidence store with explicit family-head promotion.

Current failure evidence includes:

```text
LOSS
SEVERE_LOSS
DRAWDOWN
ADVERSE_EXCURSION
WHIPSAW
MFE_GIVEBACK
UNRESOLVED_POSITION
```

`NO_TRADE` is abstention by default. An entered but unresolved position is active failure evidence.

### E1 Korean regular-session BattleCase authority

`core/battlecase_provider.py` provides explicit source authority, exact symbol/date requests, Korean regular-session validation, warm-up/current-session coverage and immutable source/session-policy identity.

Trusted Full checkpoint:

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

`core/tactic_family.py` enforces failure relevance, `CapabilityBudget`, prerequisites/exclusions and cycle-safe legal skill trees.

`core/tactic_family_catalog.py` currently contains only:

```text
JMA_TREND_CROSS_RESUME_V1
```

with bounded skills:

```text
JMA_RANGE_COOLDOWN
JMA_ADX_ENTRY_QUALITY
JMA_CONFIRM_AFTER_RANGE
JMA_FAST_PROFIT_PROTECTION
```

The first E2 Full failure was classified as a **test defect** because a 5m DSL regression test used the default 1d synthetic fixture. Product timeframe validation was not weakened. After remediation, the operator reported:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E2 is trusted Full-validated at:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
```

## E3A optional sidecar seam: causal TacticalObservation

`core/tactical_observation.py` is retained as Tactical Infrastructure / Adaptive Sidecar, not as a new DSL-language responsibility.

It can freeze causal point-in-time features such as:

- JMA geometry / slope / spread / crossover state;
- SMA60 slope and price distance;
- ATR/range/volume/gap proxies;
- recent return / session position;
- higher-high / higher-low and swing geometry;
- session time position.

The builder uses only the market prefix ending at the requested timestamp. Future bars are not inputs.

`test_stage1_tactical_observation.py` verifies feature exposure, rising high/low geometry, future-bar isolation, timeframe fail-closed behavior and warm-up coverage.

This sidecar is useful future evidence, but TacticalMemory, LocalBattlefieldLearner and adaptive resolution selection are **deferred**. They do not block the main evolution path and must not drive Core DSL changes.

### Hard equipment before learning

Deterministic equipment such as a future `JMS2_RANGE_GUARD` may produce a hard BLOCK before any learned admissibility is consulted. A learned score, parent context or multi-symbol Add-on may never override hard source/safety/equipment or common execution rules unless an explicit future authority defines that particular gate ordering.

### Adaptive timeframe

If later required, 5m/3m/1m are separately validated tactic-family modes selected by orchestration. A running DSL does not mutate its own `timeframe`. Tick mode remains unavailable until authoritative tick data and exact execution semantics exist.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- Core DSL Freeze / Adaptive Sidecar is authoritative;
- parent-context Provider / read-only inheritance seam is authoritative as design;
- single-instrument Core / optional multi-symbol Add-on boundary is authoritative;
- E3A causal observation sidecar source/tests are implemented.

Do **not** claim yet:

- trusted Full PASS for the E3A executable changes;
- an implemented Parent Feature Provider framework or DSL `ctx.*` binding;
- a functioning multi-symbol Add-on or deployment selector;
- TacticalMemory or a trained LocalBattlefieldLearner;
- automatic adaptive 5m/3m/1m/tick deployment;
- learned profitability/generalization;
- live-trading readiness;
- completed macro deployment policy;
- concrete production sector or general 1516 minute authority unless explicitly configured;
- donor repository-wide Chart compliance;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Mainline next sequence

After the current E3A sidecar boundary is trusted green, return to the original evolution mainline:

1. **E3 Multi-Battle Parameter Seeker** — tune numeric parameters on one frozen BattleCase set while DSL structure remains fixed;
2. **E4 Causal Failure / Opportunity Characterizer** — time/range/volatility/liquidity/signal-density/latency/overextension evidence without requiring an ML learner;
3. **E5 Bounded Structural Skill Generator** — propose exactly one legal child capability from observed gaps;
4. **E6 Train / Validation / OOS / Harsh Evolution Arena**;
5. **E7 Evolution Memory / Evidence UI**;
6. **E8 Macro Context Attribution / Deployment**.

Optional adaptive TacticalMemory / Learner / resolution-mode research, Parent Feature Provider implementations / DSL context binding, and multi-symbol Add-on analysis may resume later only when a concrete mainline need is demonstrated and each remains behind stable sidecar/provider/Add-on interfaces.

Do not add another executable tranche before the current E3A consolidated boundary is green.

## Next automated boundary

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as `test defect / product defect / authority drift / environment issue / unknown` before changing code.
