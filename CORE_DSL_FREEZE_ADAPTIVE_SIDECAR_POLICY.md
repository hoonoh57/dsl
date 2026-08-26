# Core DSL Freeze / Adaptive Sidecar Policy

Status: **AUTHORITATIVE STABILITY POLICY / 2026-08-26 KST**

## 1. Purpose

The project must preserve the value of the deterministic Quant DSL while still leaving room for future adaptive micro-warrior research.

The governing rule is:

> **Core DSL Freeze + Adaptive Sidecar.**

Adaptive intelligence may consume DSL/backtest evidence, but adaptive research must not become a reason to repeatedly redesign the DSL grammar, runtime, execution semantics or accounting boundary.

The product priority is therefore:

```text
stable DSL / execution authority
 -> reproducible tactic-family evolution
 -> multi-BattleCase numeric seeking
 -> causal characterization / one-skill evolution
 -> optional adaptive sidecar research
 -> later macro deployment intelligence
```

## 2. Core DSL responsibilities are intentionally narrow

The Instrument DSL remains responsible for:

- deterministic scalar/series calculations;
- registered indicators and state primitives;
- causal signal construction;
- one declared base timeframe per candidate;
- supported higher-timeframe completed-bar MTF reads;
- explicit order intent;
- execution semantics that can be reproduced by `BacktestEngine` / `BrokerEmulator`;
- future read-only consumption of explicitly registered parent-context features through a narrow binding contract.

The Core DSL is **not** responsible for:

- online model training;
- tactical memory databases;
- arbitrary ML/RL inference calls;
- runtime self-modification;
- dynamic grammar generation;
- arbitrary lower-timeframe/tick requests;
- live switching of one DSL candidate's declared timeframe;
- self-created indicators or rules outside the Capability Manifest;
- arbitrary peer-symbol reads, cross-symbol ranking, universe selection or portfolio allocation;
- calculating market-regime, sector, leader/follower or other parent features inside DSL execution;
- database/network/provider discovery during tactic evaluation.

These are sidecar/orchestration/provider concerns unless a future capability independently earns promotion into Core.

## 3. Three implementation classes

Every new request must first be classified.

### A. Core DSL capability

Examples:

- a deterministic causal indicator primitive;
- a state primitive with batch/streaming equivalence;
- a clearly defined order/execution primitive;
- a narrow read-only reference to a registered, already-frozen parent-context feature.

Core changes require the highest bar because they alter the language or trusted engine surface.

### B. Tactical infrastructure

Examples:

- `BattleCase` orchestration;
- tactic family/skill registry;
- Parameter Seeker;
- failure characterization;
- validation/OOS arena;
- immutable evidence storage;
- Parent Feature Provider / Context assembly infrastructure.

These may use the DSL but should not change its language semantics.

### C. Experimental adaptive / analysis sidecar

Examples:

- `TacticalObservation`;
- TacticalMemory;
- local battlefield learner;
- learned engagement policy;
- validated resolution-mode selection;
- pattern learning;
- optional multi-symbol comparison/ranking Add-ons.

These are optional research modules. They must connect through stable evidence/gate/provider interfaces rather than becoming parser/runtime dependencies.

## 4. Hard equipment first, learning second

A micro warrior may receive deterministic equipment and hard engagement rules that learning cannot override.

Example:

```text
JMS2 range detector
 -> slope below declared absolute threshold
 -> RANGE_GUARD = BLOCK
 -> no entry
```

A later learner may estimate opportunity only after hard guards pass.

The authority order is:

```text
source / data validity
AND hard safety / equipment guards
AND tactic trigger
AND optional learned/adaptive admissibility
AND common execution policy
 -> BrokerEmulator
```

A learned score can never bypass a hard guard or execution rule.

## 5. Adaptive timeframe remains outside Core DSL

A DSL candidate has one declared base timeframe.

If a family later owns independently validated modes such as:

```text
JMA_TCR_5M
JMA_TCR_3M
JMA_TCR_1M
```

an external tactical orchestrator may select among those validated modes. This is not in-place mutation of `timeframe` inside one running DSL.

Tick mode remains unavailable until authoritative tick data, deterministic aggregation, cutoff alignment and execution semantics are separately implemented and validated.

## 6. Stable extension seams

Adaptive or future macro modules should integrate through existing stable contracts such as:

- immutable `BattleCase` / `TacticalProfile` evidence;
- tactic-family identity / generation identity;
- optional point-in-time `BattlefieldContext`;
- explicit admissibility / `entry_gate` style decisions;
- separately validated candidate or resolution-mode selection.

Parser, Runtime, Indicator authority, Backtest accounting and Broker execution must not need to know whether an external gate came from a deterministic guard, a future learner, a multi-symbol Add-on or a macro deployment policy.

## 6A. Single-instrument Core / multi-symbol Add-on boundary

The Instrument DSL is a **single-instrument tactical authority**.

Multi-symbol chart display does not create cross-symbol strategy authority.

Cross-symbol analysis, ranking, capital competition and deployment selection remain outside Instrument DSL and may be added only through an optional Add-on seam.

The safe pattern is:

```text
single-instrument DSLs
 -> immutable point-in-time per-symbol snapshots
 -> optional read-only multi-symbol Add-on
 -> explicit ALLOW / BLOCK / PRIORITY evidence
 -> common execution policy
 -> BrokerEmulator
```

A multi-symbol Add-on is disabled by default, may not mutate DSL/runtime state, may not issue Broker orders directly, may not guess its universe or use future information, and must use deterministic time alignment and tie-breaking.

Its detailed contract is defined in `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`.

## 6B. Parent-context inheritance is preserved

Single-instrument authority does **not** mean that an Instrument DSL must be blind to verified parent battlefield intelligence.

The allowed seam is:

```text
Parent Feature Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> narrow read-only Context Binder
 -> registered ctx.* value consumed by Instrument DSL
```

The DSL may consume a parent feature without knowing how it was calculated. It must not call the provider or perform cross-market/cross-symbol discovery itself.

Therefore a future tactic may conceptually consume registered values such as:

```text
ctx.market.kospi_slope
ctx.sector.strength
ctx.group.leader_strength
ctx.group.follower_alignment
```

while the market/sector/group calculation logic remains outside Parser/Runtime/Backtest/Broker.

Parent context must be immutable, source-identified, versioned and valid at or before the battle knowledge cutoff. Missing/stale/future context is never guessed.

The detailed authority is `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`.

## 7. Promotion into Core is exceptional

An experimental capability may be considered for Core only if all are true:

1. it is required repeatedly across multiple tactic families;
2. current supported primitives cannot express it cleanly;
3. causal/no-lookahead semantics are unambiguous;
4. batch and streaming behavior can be made deterministic;
5. Backtest and live execution semantics can be stated exactly;
6. the capability does not require hidden external model/network/file behavior;
7. repo-level regression coverage can enforce the boundary;
8. the benefit justifies the permanent language complexity.

Until then it remains Tactical Infrastructure or Adaptive/Analysis Sidecar.

## 8. Mainline development order

Adaptive and cross-symbol research must not block the main tactic-evolution loop.

Current mainline after E2 is:

```text
E3  Multi-Battle Parameter Seeker
E4  Causal Failure / Opportunity Characterizer
E5  Bounded Structural Skill Generator
E6  Train / Validation / OOS / Harsh Evolution Arena
E7  Evolution Evidence UI / lineage operations
E8  Macro Context Attribution / Deployment
```

`core/tactical_observation.py` is retained as an optional causal sidecar seam. TacticalMemory / LocalBattlefieldLearner / adaptive resolution selection and multi-symbol Add-on execution are deferred until the main evolution loop demonstrates a concrete need and can consume them without changing Core DSL contracts.

The parent-context Provider/Binding seam remains architecturally reserved so cascading market/sector/group features can later be consumed without redesigning the language, but no executable `ctx.*` grammar or Provider framework is added before its own validated tranche.

## 9. Change-control rule

Before any future adaptive or cross-symbol feature is implemented, ask:

```text
Can this be done outside Parser / Runtime / Backtest / Broker?
```

If yes, it must stay outside Core.

For cross-symbol requirements, ask additionally:

```text
Can this be done as read-only analysis of immutable per-symbol snapshots?
```

If yes, it must remain an Add-on.

For parent context, the only Core-facing question is:

```text
Can the DSL consume an already-frozen registered value instead of executing the parent calculation?
```

If yes, only the read-only binding may enter Core; the calculation remains in a Provider/Add-on.

A new adaptive, multi-symbol or context idea must not reorder or rewrite trusted core logic merely because it is theoretically useful.

## 10. Success criterion

The project succeeds if it can support both of these at the same time:

```text
CORE
  simple
  deterministic
  reproducible
  auditable
  stable
  single-instrument tactical authority
  able to read registered parent context without calculating it

SIDECAR / ADD-ON / PROVIDER
  extensible
  optional
  replaceable
  evidence-driven
  safe for future adaptive, multi-symbol and parent-context analysis
```

The sidecar may become sophisticated. The DSL core should become increasingly boring and trustworthy.
