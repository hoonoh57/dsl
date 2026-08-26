# Micro-First / Macro-Ready Tactical Research Architecture

Status: **AUTHORITATIVE EXECUTION-ORDER ADDENDUM / 2026-08-26 KST**

This addendum refines implementation order without weakening the existing multi-layer product architecture.

## 1. Two different orders must not be confused

### Runtime / deployment order

The final trading system executes top-down:

```text
Battlefield Context
  -> Market / Regime
  -> Sector / Group / Narrative
  -> eligible Tactical Unit
  -> symbol selection / ranking
  -> validated micro tactic
  -> common execution policy
  -> BrokerEmulator
```

### Research / development order

The research system develops bottom-up:

```text
Micro tactic discovery
  -> multi-symbol / multi-date robustness
  -> tactic characterization
  -> tactic competition
  -> context attribution
  -> market/sector/group deployment rules
  -> portfolio command
```

The runtime order is macro-to-micro, while the R&D order is micro-to-macro.

The product must support both from the same contracts. A later market-regime or leading-sector layer must be attachable without rewriting the DSL parser/runtime, BrokerEmulator, backtest evidence, or the tactical-discovery data model.

## 2. Current priority: win individual battles first

The current priority is to discover the minimum and strongest repeatable intraday tactics for the Korean regular session.

Examples include JMA trend-resume/crossover, VWAP reclaim, opening-range breakout, pullback/re-breakout, volatility contraction-expansion, trading-value confirmation, and other DSL-expressible tactics.

The research question is not "which macro regime explains the market?" yet. It is:

> **Which minimal tactic produces repeatable edge across many independent symbol/date battles, and under what observable conditions does that edge strengthen or disappear?**

A tactic that only works after many filters are added is less valuable than a simpler tactic with comparable robustness. Complexity therefore becomes explicit evidence rather than an implicit preference.

## 3. Macro-ready seam that must exist now

Every micro experiment carries an optional immutable `BattlefieldContext` reference from day one.

During the current micro-first phase it is normally `NEUTRAL`: no market/sector/theme filter is allowed to influence entry authorization.

Later the same experiment contract can carry point-in-time snapshots for:

- market / index regime;
- breadth / volatility regime;
- sector leadership;
- tactical-group structure;
- high-beta state;
- theme / policy / narrative context;
- leader/follower and relative-strength state.

This context is evidence and command input. It is not allowed to mutate indicator calculations, DSL source, historical OHLCV, BrokerEmulator accounting, or previously recorded micro results.

## 4. Stable domain contracts

### `ContextLayerSnapshot`

```text
layer
context_id
as_of
source
features
```

A layer snapshot is point-in-time evidence. Its `as_of` must not be later than the battle knowledge cutoff.

### `BattlefieldContext`

```text
mode = NEUTRAL | OBSERVED | DEPLOYMENT
as_of
layers[]
context_hash
```

`NEUTRAL` means the tactic is being evaluated without macro assistance. This is the required default for current micro discovery.

### `DeploymentDecision`

```text
allowed
priority
eligible_tactics[]
blocked_tactics[]
reasons[]
context_hash
```

This belongs to the future command layer. It may allow/block/rank a previously validated tactic but may not alter the tactic itself.

### `BattleCase`

```text
case_id
symbol
session_date
market snapshot
settings
knowledge_cutoff
BattlefieldContext
metadata
```

A BattleCase is the atomic research battle. The same stock may appear on many dates because identity is `case_id`, not symbol alone.

### `TacticCandidate`

```text
candidate_id
DSL
settings
complexity_units
metadata
```

`complexity_units` is explicit provenance supplied by the tactic author/generator. The engine does not invent a hidden formula from source-code length.

### `TacticalProfile`

```text
candidate identity/hash
case count
profitable/no-trade counts
return distribution
MDD / PF / costs / MFE / MAE
trade-frequency evidence
context strata
per-case evidence
run hash
```

The profile is the artifact promoted into later context analysis.

## 5. No macro leakage during micro discovery

The micro phase has a strict neutral-context contract:

```text
market context supplied for evidence = allowed
market context used to block/filter/rank cases = prohibited unless the experiment is explicitly a context-attribution experiment
```

Therefore the baseline discovery sequence is:

```text
same tactic
  x many symbol/date cases
  x same execution contract
  x NEUTRAL BattlefieldContext
  -> robust tactical profile
```

Only after a tactic shows evidence is it stratified by context:

```text
validated tactic profile
  -> compare performance by market regime
  -> compare by sector/group leadership
  -> compare by volatility/breadth/theme state
  -> derive deployment rule
```

This preserves causal attribution: we can tell whether the edge came from the tactic or from the later filter.

## 6. Macro layers are additive command layers

Future macro functionality must connect through three extension points only:

1. **Context Providers** create point-in-time `ContextLayerSnapshot` objects.
2. **Context Attribution** groups already-frozen tactical results by context without rewriting results.
3. **Deployment Policy** produces an allow/block/priority decision for a tactic/unit.

The macro subsystem must not call private DSL-runtime internals and must not duplicate broker logic.

## 7. Tactical discovery implementation priority

### T0 — Discovery kernel

- execute one tactic across many independent BattleCases;
- bounded parallel execution;
- deterministic order and hashes independent of worker count;
- fail whole run if one case is malformed;
- preserve exact backtest evidence.

### T1 — Robustness

- multi-symbol and multi-date batches;
- chronological event/date partitions;
- minimum sample/trade coverage;
- costs and execution policy fixed;
- winner concentration checks.

### T2 — Characterization

- time-of-day slices;
- volatility/liquidity slices;
- signal-count / trade-count slices;
- MFE-to-realized capture and giveback;
- failure / near-miss Evidence Viewer.

### T3 — Tactical competition

Compare candidate tactics under the same frozen BattleCase set. Do not silently compare tactics on different opportunity sets.

Prefer Pareto evidence over a hidden universal score:

- maximize robust return / PF / profitable-case ratio / MFE capture;
- minimize MDD / cost / excessive trade count / complexity;
- preserve no-trade as a valid outcome.

### T4 — Context attribution

Attach market, sector, group and narrative snapshots and measure incremental edge.

### T5 — Deployment command

Use validated context evidence to decide which tactic to deploy, where, and when.

## 8. Architecture invariants preventing a future rewrite

- Instrument DSL remains the tactical-language SSOT.
- `BacktestEngine` and `BrokerEmulator` remain the execution/accounting authority.
- Multi-symbol and multi-case layers are orchestration/evidence layers only.
- Symbol identity and battle-case identity are separate.
- Macro context is optional, immutable and point-in-time.
- Neutral micro experiments remain valid after macro functionality is added.
- Macro features can be added as new context providers without changing old TacticalProfiles.
- Deployment decisions can block or prioritize a tactic but cannot rewrite its historical evidence.
- A tactic's parameters are scoped to its tactic family / Tactical Unit and are not globally generalized.
- All comparisons must state the frozen opportunity set and context mode.

## 9. Architecture verification conclusion

The existing project already has the critical lower-level separations required for this direction: typed DSL execution, BrokerEmulator authority, common entry gates, multi-symbol orchestration, immutable Tactical Scenario storage, point-in-time cohorts and Chart Document evidence.

The missing seam was an explicit distinction between **micro discovery evidence** and **future battlefield command context**. This addendum makes that seam first-class.

With `BattlefieldContext` optional and immutable, micro research can now be strengthened aggressively without coupling every tactic to KOSPI/KOSDAQ, sector, beta or narrative logic. Later macro modules attach through context providers and deployment policy instead of forcing a rewrite of the tactical kernel.

## 10. Autonomous evolving micro-warrior doctrine

The micro layer is not a blindly obedient entry trigger. Its objective is to create a **survivable, mission-capable and continuously improvable tactical agent** that can operate before macro assistance is available.

### 10.1 Mission command, not forced entry

A future `DeploymentDecision.allowed = true` is permission to operate, not an order to enter.

Actual entry authority is conjunctive:

```text
higher-layer permission
AND local survival/admissibility decision
AND tactic trigger
AND common execution/risk policy
```

Therefore a micro tactic retains an autonomous `NO_TRADE` outcome when local evidence is poor. No macro layer may force a DSL signal or bypass the tactic's local safety/admissibility logic.

### 10.2 Survival across environments is a first-class objective

Neutral discovery must deliberately include favorable, ordinary and adverse symbol/date battles instead of filtering away difficult cases.

A strong micro warrior is not defined only by average return. Its profile must expose at least:

- profitable / losing / no-trade case rates;
- worst and tail drawdown evidence;
- maximum loss concentration / winner concentration;
- trade frequency and cost burden;
- MFE capture and giveback;
- behavior in adverse volatility/liquidity/time-of-day slices;
- recovery / repeated-loss behavior when the execution model supports it.

The system should reward tactics that remain functional or intelligently abstain under hostile local conditions rather than tactics that require a favorable macro filter to avoid collapse.

### 10.3 Personal arsenal / capability budget

The strongest tactic is not the tactic with the largest number of indicators or branches.

Each evolving tactic family must eventually declare a bounded `CapabilityBudget`, such as:

```text
allowed indicator / signal primitives
maximum independent state variables
maximum tunable parameters
maximum decision branches
maximum concurrent setup variants
```

The exact budget is a declared research contract, not a hidden formula. Tactics exceeding the budget are a different class and cannot be compared as if they were equally operable.

This formalizes the principle that a micro warrior should receive weapons it can actually operate reliably; adding a heavy, complex mechanism that increases fragility is not automatically an upgrade.

### 10.4 Evolution is evidence-gated, not self-modifying production code

The warrior evolves through immutable generations rather than rewriting the trusted engine.

```text
Generation N
 -> observe battle evidence
 -> diagnose failure / missed opportunity
 -> propose bounded structural mutation
 -> Seeker re-optimizes numeric parameters
 -> re-run on the same frozen training contract
 -> validation / OOS / harsh cases
 -> compare against parent
 -> ACCEPT or REJECT
 -> Generation N+1 only after explicit promotion
```

Permitted evolution targets are DSL structure, tactic-family parameters and declared tactic metadata/policy. Parser, Runtime, Indicator implementations, Backtest accounting, BrokerEmulator and validation assertions are outside the mutation boundary.

### 10.5 Parent survival must be preserved

A child generation is not promoted merely because peak return is higher.

Promotion evidence must show the declared mission improvement without unacceptable regression in survival axes such as drawdown, tail cases, cost, concentration, complexity and no-trade discipline.

Where objectives conflict, retain the parent and child on a Pareto frontier until a declared mission contract chooses between them. Do not hide trade-offs in one opaque universal score.

### 10.6 Macro intelligence is an amplifier, not life support

Market regime, leading sector, high-beta, theme/policy and leader/follower intelligence are later battlefield reconnaissance layers.

They should improve deployment by:

- avoiding known unfavorable battlefields;
- prioritizing environments where a validated warrior historically performs best;
- choosing the appropriate tactic family for the current battlefield;
- reducing unnecessary exposure and capital competition.

But a micro tactic that only survives because macro filters remove all difficult battles has not yet earned the status of a strong autonomous warrior.

The development target is therefore:

> **First breed a compact, independently survivable and evidence-driven evolving micro warrior. Then give that warrior superior battlefield intelligence so it fights less often, but on increasingly favorable ground.**
