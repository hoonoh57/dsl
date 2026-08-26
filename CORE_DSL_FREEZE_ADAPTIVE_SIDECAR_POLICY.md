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
- execution semantics that can be reproduced by `BacktestEngine` / `BrokerEmulator`.

The Core DSL is **not** responsible for:

- online model training;
- tactical memory databases;
- arbitrary ML/RL inference calls;
- runtime self-modification;
- dynamic grammar generation;
- arbitrary lower-timeframe/tick requests;
- live switching of one DSL candidate's declared timeframe;
- self-created indicators or rules outside the Capability Manifest.

These are sidecar/orchestration concerns unless a future capability independently earns promotion into Core.

## 3. Three implementation classes

Every new request must first be classified.

### A. Core DSL capability

Examples:

- a deterministic causal indicator primitive;
- a state primitive with batch/streaming equivalence;
- a clearly defined order/execution primitive.

Core changes require the highest bar because they alter the language or trusted engine surface.

### B. Tactical infrastructure

Examples:

- `BattleCase` orchestration;
- tactic family/skill registry;
- Parameter Seeker;
- failure characterization;
- validation/OOS arena;
- immutable evidence storage.

These may use the DSL but should not change its language semantics.

### C. Experimental adaptive sidecar

Examples:

- `TacticalObservation`;
- TacticalMemory;
- local battlefield learner;
- learned engagement policy;
- validated resolution-mode selection;
- pattern learning.

These are optional research modules. They must connect through stable evidence/gate interfaces rather than becoming parser/runtime dependencies.

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
AND optional learned admissibility
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

Parser, Runtime, Indicator authority, Backtest accounting and Broker execution must not need to know whether an external gate came from a deterministic guard, a future learner, or a macro deployment policy.

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

Until then it remains Tactical Infrastructure or Adaptive Sidecar.

## 8. Mainline development order

Adaptive research must not block the main tactic-evolution loop.

Current mainline after E2 is:

```text
E3  Multi-Battle Parameter Seeker
E4  Causal Failure / Opportunity Characterizer
E5  Bounded Structural Skill Generator
E6  Train / Validation / OOS / Harsh Evolution Arena
E7  Evolution Evidence UI / lineage operations
E8  Macro Context Attribution / Deployment
```

`core/tactical_observation.py` is retained as an optional causal sidecar seam. TacticalMemory / LocalBattlefieldLearner / adaptive resolution selection are deferred until the main evolution loop demonstrates a concrete need and can consume them without changing Core DSL contracts.

## 9. Change-control rule

Before any future adaptive feature is implemented, ask:

```text
Can this be done outside Parser / Runtime / Backtest / Broker?
```

If yes, it must stay outside Core.

A new adaptive idea must not reorder or rewrite trusted core logic merely because it is theoretically useful.

## 10. Success criterion

The project succeeds if it can support both of these at the same time:

```text
CORE
  simple
  deterministic
  reproducible
  auditable
  stable

SIDECAR
  extensible
  experimental
  replaceable
  evidence-driven
```

The sidecar may become sophisticated. The DSL core should become increasingly boring and trustworthy.
