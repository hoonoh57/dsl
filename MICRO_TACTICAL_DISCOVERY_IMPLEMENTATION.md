# Micro Tactical Discovery Implementation

Status: **IMPLEMENTED_AWAITING_TRUSTED_WINDOWS VALIDATION / REMEDIATION_REQUIRED**
Updated: 2026-08-26 KST

## Purpose

This tranche implements the current research priority: discover and compare the minimum/strongest individual-stock tactics first, while preserving a stable extension seam for later market-regime, leading-sector, high-beta, theme/policy and other battlefield context.

It does not claim that any indicator/tactic is profitable or strongest yet.

## Architecture decision

See `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md`.

The key distinction is:

```text
runtime/deployment: macro -> unit -> symbol -> tactic
research/development: tactic -> robustness -> characterization -> macro attribution
```

The DSL/Backtest/Broker kernel therefore remains micro-focused, while every battle result can carry optional immutable context provenance.

## New context contract

`core/battlefield_context.py`

- `ContextLayerSnapshot`
- `BattlefieldContext`
- `DeploymentDecision`

Current baseline research uses `BattlefieldContext(mode="NEUTRAL")`.

`OBSERVED` context may be attached later for attribution, and `DEPLOYMENT` context is reserved for an explicit command decision. A context timestamp later than the battle knowledge cutoff fails closed.

Macro context is not permitted to mutate DSL code, indicator input data or BrokerEmulator accounting.

## New micro discovery engine

`core/tactical_discovery.py`

### Atomic unit: `BattleCase`

A battle is identified by `case_id`, not symbol alone. Therefore the same stock can appear on many different dates without collapsing into one instrument identity.

Each case records:

- symbol;
- session date;
- canonical OHLCV snapshot;
- fixed execution settings;
- knowledge cutoff;
- optional point-in-time BattlefieldContext;
- optional explicit entry gate;
- immutable case hash.

### Tactic: `TacticCandidate`

A candidate records:

- candidate id;
- DSL source;
- explicit complexity units;
- metadata;
- candidate hash.

Complexity is explicit provenance. The engine does not invent a hidden complexity score from source length.

### `TacticalDiscoveryEngine.evaluate()`

One tactic is executed across the frozen BattleCase set through bounded worker threads.

Default micro-baseline invariants:

- all cases use `NEUTRAL` BattlefieldContext;
- all cases use the same execution settings;
- any malformed case fails the whole run;
- input case ordering is preserved;
- worker count must not change `case_set_hash`, aggregate evidence or `run_hash`;
- BacktestEngine/BrokerEmulator remain execution authority.

Aggregate evidence includes:

- profitable / losing / no-trade case counts;
- average / median / best / worst case return;
- average / worst MDD;
- total and average trade count;
- total costs;
- MFE / MAE / MFE giveback;
- finite PF median and infinite-PF case count;
- top-1 / top-3 winner concentration;
- explicit tactic complexity.

The engine preserves complete per-case Backtest evidence for later chart audit and failure analysis.

## Tactical competition

`core/tactical_competition.py`

Different tactics may only compete when they share the exact same `case_set_hash` and context policy.

The comparison engine does **not** use one hidden universal score. It publishes:

- per-metric leaderboards;
- a conservative Pareto frontier;
- explicit dominated-by relations;
- immutable comparison hash.

Primary Pareto axes currently are:

```text
maximize: average return, profitable-case rate
minimize: worst drawdown risk, cost/case, complexity
```

Other evidence such as median return, PF and trade frequency remains visible in leaderboards and may become explicit objectives only under a declared research contract.

## Regression / stress coverage

New Stage1-discovered tests:

- `test_stage1_battlefield_context.py`
- `test_stage1_tactical_discovery.py`
- `test_stage1_tactical_competition.py`

The tactical stress harness now also runs the same micro candidate over a larger frozen case set at worker count 1 vs bounded parallel workers and requires identical case-set/run hashes and result order.

## Next micro-strengthening work

After this boundary passes trusted Windows verification, continue in this order:

1. **BattleCase Provider** for an authoritative Korean regular-session research universe; do not invent or use dummy production data.
2. **Tactic Family Registry** for JMA/VWAP/opening-range/pullback/breakout/volatility/trading-value families with lineage.
3. **Parameter Seeker adapter** that optimizes numeric parameters on a frozen BattleCase set rather than one stock.
4. **Tactical Characterizer** for time-of-day, liquidity, volatility, MFE capture/giveback, winner concentration and failure slices.
5. **Tactical Evidence UI** for winner/loser/near-miss chart audit across cases.
6. **Context Attribution** only after a tactic has a neutral robust profile; attach market/sector/group snapshots and measure incremental edge.

## Validation status

These mutations have not yet received a trusted local Windows Full verifier PASS.

Therefore the authoritative state remains `REMEDIATION_REQUIRED`. Do not claim micro tactical superiority, profitability, production readiness or macro deployment validity from this implementation alone.
