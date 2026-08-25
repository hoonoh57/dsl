# Multi-Layer DSL Tactical Strategy Architecture

Status: **AUTHORITATIVE PRODUCT ARCHITECTURE ADDENDUM / 2026-08-26 KST**

## 0. Authority and product correction

This document records the product requirement clarified during the consolidated Stage 1 UI review.

Where the older `PRODUCT_IMPLEMENTATION_PLAN.md` describes a strictly sequential path of `Single-Symbol -> Multi-Symbol -> Cross-Sectional -> Market/Sector`, this document **supersedes that sequencing assumption**.  The validated single-symbol engine remains the tactical execution kernel, but the product is not defined as a random single-symbol strategy finder.

The product goal is:

> **A verifiable tactical strategy laboratory that understands market structure through multiple layers, decides where to fight, which tactical unit to deploy, which symbols are superior inside that unit, and only then applies the unit-specific DSL strategy and common execution policy.**

The existing typed DSL remains the per-instrument execution SSOT.  Multi-symbol/regime/group analysis is added as an orchestration and evidence layer around it rather than duplicating or bypassing Parser/Semantic/Runtime/Backtest/Broker.

---

# 1. What is already strong and must be preserved

The current engine already provides a valuable deterministic kernel:

- fail-closed Parser / Semantic analysis;
- canonical function/capability registry;
- deterministic DSL Runtime;
- confirmed-only MTF and persistent state;
- MARKET/LIMIT/STOP/STOP_LIMIT semantics;
- authoritative `BrokerEmulator` lifecycle;
- bar-close / next-open execution policy;
- fees, tax, slippage, stop/take-profit/trailing accounting;
- MFE/MAE and trade-level evidence;
- immutable data snapshots and Experiment lineage;
- deterministic Grid/Random Parameter Seeker;
- resumable search and parameter sensitivity;
- rule-based Result Analyzer;
- evidence-driven LLM structural improvement loop;
- explicit promote/reject lineage;
- Chart Document evidence through the shared Chart SSOT;
- trusted Stage 1 Full system-verifier PASS.

These components are **not rewritten** for multi-symbol work.  They become the instrument-level tactical kernel used by many concurrent contexts.

---

# 2. Three-layer product requirement

## Layer 1 — Market Regime / Opportunity Window

Question: **Where should we fight?**

Inputs may include:

- KOSPI/KOSDAQ or other market indices;
- breadth / risk-on-risk-off state;
- volatility expansion/contraction;
- macro or policy regime features;
- previously validated market-entry windows;
- high-beta-favorable windows;
- sector-rotation windows.

Output is not a stock buy order.  It is an immutable higher-layer decision such as:

```text
Regime: RISK_ON
Opportunity Window: 2026-05-14 ~ 2026-06-03
Eligible Tactical Units: HIGH_BETA, LEADING_SECTOR
Blocked Units: REVERSAL
```

**Invariant:** if Layer 1 blocks a unit, no lower-layer DSL signal may create an entry.  Warm-up bars remain available for indicators; only entry authorization is gated.

## Layer 2 — Tactical Unit / Multi-Symbol Comparative Analysis

Question: **Which unit and which symbols should fight?**

A Tactical Unit is a cohort with its own mission, features and strategy family. Examples:

- `1516 @ 09:05` condition-search cohort;
- High-Beta cohort;
- Leading-Sector cohort;
- Theme / Policy cohort;
- future custom Kiwoom condition-search cohorts.

The layer must compare multiple symbols simultaneously and preserve point-in-time evidence.

Core comparative features:

- benchmark-relative return / Relative Strength;
- beta;
- correlation;
- lead / coincide / lag relationship to the benchmark;
- group leader/follower relation;
- trading value / liquidity;
- volatility;
- sector/theme membership;
- condition-search capture time;
- post-capture MFE/MAE label where the mission requires it.

The `1516 @ 09:05` mission is a canonical example:

```text
09:05 captured cohort is fixed first
 -> post-capture same-day MFE is measured afterward
 -> MFE >= 10% is an outcome label, not an input feature
 -> strategy quality measures how well profitable moves are retained
    while weak candidates, cost and drawdown are reduced
```

High-Beta is a different unit and must be allowed to own different feature logic and different tactics.

**Invariant:** a successful tactic for one Tactical Unit is not automatically propagated to another unit.

## Layer 3 — Common Tactical / Execution Policy

Question: **How do we fight?**

The common execution layer supplies reusable policy that should not require every strategy author to hand-code the same constraints repeatedly.

Initial common controls:

- entry start time;
- entry end time;
- maximum entries per day;
- stop/take-profit/trailing;
- fees/tax/slippage;
- bar-close / next-open;
- higher-layer opportunity gate;
- later: portfolio-level max positions / capital competition.

The DSL still owns unit-specific tactical semantics such as:

- JMA crossover / pullback / trend-resume;
- breakout / retest;
- volume/trading-value confirmation;
- unit-specific state and re-entry logic.

**Invariant:** common policy may restrict an entry, but it may not silently change the DSL calculation, broker accounting, or indicator values.

---

# 3. Target execution topology

```text
Market / Macro / Index data
        ↓
Layer 1 Regime Engine
        ↓
OpportunityWindow[]
        ↓
Eligible Tactical Units
        ↓
Layer 2 Multi-Symbol Analysis
        ├─ exact timestamp alignment
        ├─ benchmark beta / correlation
        ├─ lead-lag
        ├─ relative strength
        ├─ cohort outcome labels
        └─ cross-sectional ranking
        ↓
Symbol candidates / leader-follower evidence
        ↓
Layer 3 Common Policy Gate
        ↓
Instrument DSL task(s)
        ↓
Parallel workers
        ├─ Parser / Semantic
        ├─ Runtime
        ├─ Backtest
        └─ BrokerEmulator
        ↓
Per-symbol Evidence
        ↓
Cohort / Scenario Evidence
        ↓
Train / Validation / OOS by scenario/window/date
        ↓
Promote / Reject / Remember
```

Parallelism must not change result ordering, hashes or numeric results.

---

# 4. Data objects

## `OpportunityWindow`

```text
start
end
label
```

Represents the time region in which a tactical unit is authorized to enter.  It is deliberately separate from indicator warm-up history.

## `RegimeContext`

```text
regime_id
state
active
eligible_units[]
windows[]
evidence
```

## `TacticalUnitSpec`

```text
unit_id
unit_type
symbols[]
capture_times{symbol -> timestamp}
reference_symbol
rank_by
metadata
```

## `MissionSpec`

```text
mission name
MFE threshold when relevant
capture price field
include/exclude capture bar
```

For capture-based missions, exact timestamp matching is required.  No nearest-time substitution is allowed.

## `InstrumentTask`

```text
symbol
DSL
market OHLCV
execution settings
metadata
```

Different Tactical Units may use different DSLs.  Multiple symbols inside one unit may share one DSL or, when explicitly required, have distinct validated DSL artifacts.

## `Scenario Result`

```text
scenario_hash
run_hash
regime decision
unit definition
mission definition
per-symbol backtest evidence
relative metrics
capture outcome labels
cross-sectional ranking
cohort summary
```

---

# 5. OOS / validation correction

The old single-symbol chronological holdout remains useful as an engine-level research tool, but it is **not the final product methodology for tactical units**.

The final validation unit is the scenario/cohort/window.

Examples:

### 1516 @ 09:05

```text
Train: earlier dates' complete 09:05 captured cohorts
Validation: later unused captured cohorts
Final OOS: unseen dates' complete 09:05 captured cohorts
```

All captured symbols for a date must remain in the cohort.  `MFE >= 10%` is measured after capture as the mission outcome label.

### High Beta

```text
Train: earlier validated High-Beta opportunity windows
Validation: later unused opportunity windows
Final OOS: unseen market windows and their point-in-time High-Beta cohorts
```

The system must compare:

```text
Market/Unit baseline
vs
Unit selection logic
vs
Unit selection + tactical DSL
vs
Unit selection + tactical DSL + common policy
```

This separates where the edge came from.

---

# 6. Warm-up and session semantics

Indicator history and trading authorization are different concepts.

For intraday tactics:

- `_AL` integrated symbol data may be required to include the intended pre-open/NXT history;
- enough earlier bars must be retained for JMA/SMA/ATR warm-up;
- a 52-bar JMA must not be treated as fully contextualized merely because 08:00 was loaded if the timeframe does not provide 52 prior bars;
- Layer 1/3 entry gates may begin at 09:00/09:05 while earlier bars remain visible to the runtime;
- capture-time missions may start trading only at or after their actual capture time.

No future bars may enter strategy inputs.

---

# 7. Multi-symbol comparison contract

Initial deterministic comparative metrics:

- exact-overlap cumulative relative strength;
- beta on exact-overlap bar returns;
- same-bar correlation;
- bounded lead/lag correlation;
- strategy return / MDD / PF / trade count / cost;
- post-capture MFE/MAE and mission-success label;
- rank by an explicitly chosen metric.

Lead/lag convention in v1:

```text
positive lag  -> symbol leads benchmark by N bars
zero          -> coincident
negative lag  -> symbol lags benchmark by N bars
```

The engine must not invent missing bars or use nearest timestamps.

---

# 8. Priority implementation plan

## P0 — Foundation required now

### P0.1 Preserve the DSL kernel

Do not add ad-hoc cross-symbol syntax to Parser/Runtime merely to make the UI look multi-symbol.  Multi-symbol orchestration first reuses the existing validated instrument engine.

### P0.2 Higher-layer entry gate

Backtest accepts an external per-bar authorization gate.  Indicators still receive complete warm-up data; unauthorized bars cannot create entries.

### P0.3 Common execution controls

Add reusable execution settings:

```text
entry_start_time
entry_end_time
max_entries_per_day
```

They apply to actual fills without changing DSL indicator calculations.

### P0.4 Multi-symbol parallel engine

Run independent instrument DSL tasks through bounded parallel workers while preserving input-order result determinism and fail-closed behavior.

### P0.5 Regime + Tactical Unit contracts

Represent opportunity windows, eligible units, capture cohorts and mission labels as first-class data.

### P0.6 Relative / lead-lag analysis

Add benchmark-relative comparison and cross-sectional ranking.

### P0.7 API vertical slice

Expose the complete `Regime -> Tactical Unit -> Parallel DSL -> Cohort Evidence` path through one API contract before building a large UI around it.

## P1 — Productization immediately after P0 verification

### P1.1 Tactical Scenario Store

Persist immutable Scenario definitions/results and lineage, analogous to Experiment snapshots.

### P1.2 Cohort providers

Adapters for:

- 1516/performance-result capture cohorts;
- High-Beta cohort snapshots;
- Leading-Sector/leader-follower cohorts;
- user-defined condition-search cohorts.

Each provider must preserve point-in-time membership.

### P1.3 `_AL`/session-aware market provider

Request enough history for indicator warm-up, support integrated-session symbol suffixes, continuation/pagination, and explicit data coverage evidence.

### P1.4 Multi-symbol Evidence UI

Reuse shared Chart SSOT to show:

- benchmark + selected symbols;
- regime opportunity shading;
- selected + near-miss/control symbols;
- relative metrics;
- exact per-symbol entry/exit evidence.

### P1.5 Scenario OOS

Split by date/cohort/opportunity-window, not by arbitrary final bars of one stock.

## P2 — Competitive differentiation

- sector/group causal cascade;
- leader/follower propagation;
- narrative/theme/policy point-in-time context;
- multiple Tactical Unit competition under one Regime;
- portfolio capital competition;
- scenario-level Seeker and structural LLM improvement;
- process-pool/distributed worker backend if profiling proves thread workers insufficient.

---

# 9. Current implementation delivered with this architecture checkpoint

The first P0 vertical slice is implemented without replacing the existing engine:

- `core/backtest.py`
  - higher-layer `entry_gate`;
  - `entry_start_time`;
  - `entry_end_time`;
  - `max_entries_per_day`;
  - explicit rejection diagnostics for each gate.

- `core/multi_symbol.py`
  - `OpportunityWindow`;
  - `RegimeContext`;
  - `MissionSpec`;
  - `TacticalUnitSpec`;
  - `InstrumentTask`;
  - bounded `ThreadPoolExecutor` parallel execution;
  - exact timestamp relative analysis;
  - beta/correlation/lead-lag;
  - capture-time MFE/MAE mission labeling;
  - deterministic ranking;
  - scenario/run hashes;
  - regime-blocked no-trade outcome.

- `stage1_main.py`
  - `/api/stage1/multi-symbol/analyze` vertical-slice API;
  - health advertises `multi_symbol_tactical/v1`.

- `test_stage1_multilayer.py`
  - common time/count gate contract;
  - opportunity-window warm-up preservation;
  - regime blocking;
  - deterministic parallel result/hash behavior;
  - benchmark-relative ranking;
  - post-capture mission labeling;
  - exact-time fail-closed behavior.

This P0 slice is an architectural base, not a claim of complete High-Beta/1516/sector production integration or profitability.

---

# 10. Utilization patterns

## 1516 tactical unit

```text
Regime: opening-market environment if one is required
Unit: 1516_0905
Cohort: actual 09:05 captured symbols for that date
Mission label: same-day MFE >= 10%
Relative evidence: optional KOSDAQ/KOSPI, group breadth
Common policy: entry >= capture time, cutoff sweep, max entries/day
DSL family: opening momentum / pullback / re-breakout
Validation: full captured cohorts by date
```

## High-Beta tactical unit

```text
Regime: High-Beta-favorable opportunity windows
Unit: point-in-time High-Beta cohort
Reference: market index
Relative evidence: beta, correlation, lead/lag, RS
Additional context: theme/policy/sector when available
Common policy: window gate + risk/entry-count rules
DSL family: trend continuation / contraction-expansion / re-entry
Validation: unseen opportunity windows
```

## Leading-Sector tactical unit

```text
Regime: sector-rotation / risk-on state
Unit: current leading sector members
Relative evidence: sector RS, leader/follower, breadth
Common policy: sector exposure and intraday entry limits
DSL family: leader pullback / follower catch-up
Validation: unseen sector leadership episodes
```

---

# 11. Performance policy

The term “multi-threaded DSL” means **parallel execution of validated instrument contexts**, not shared mutable DSL state.

Initial worker policy:

- bounded thread pool;
- each task receives its own market/context/result;
- deterministic result order follows Tactical Unit symbol order;
- any task failure fails the scenario instead of silently dropping a symbol;
- worker count is recorded in evidence;
- scenario/run hashes must not depend on worker count.

A process-pool or distributed backend is P2 and must be chosen from profiling evidence.  Python thread count alone is not treated as a performance claim.

---

# 12. Non-negotiable rules

- Do not claim “world-best” performance without benchmark evidence.
- Do not use random single-stock OOS as the final validation methodology for Tactical Units.
- Do not use post-outcome information to construct point-in-time cohorts.
- Do not use `MFE >= 10%` as an input when it is the 1516 mission outcome label.
- Do not let one Tactical Unit's optimized strategy automatically become another unit's strategy.
- Do not truncate warm-up data merely to draw an entry window.
- Do not use nearest-time alignment to manufacture cross-symbol comparisons.
- Do not bypass BrokerEmulator or accounting rules in the multi-symbol layer.
- Do not weaken existing Stage 1 tests to make multi-layer work pass.

---

# 13. Product success criterion

The platform succeeds when a researcher can repeatedly perform this workflow without source-code surgery:

```text
Choose / generate Market Regime evidence
 -> choose Tactical Unit
 -> load point-in-time multi-symbol cohort
 -> compare benchmark/group structure
 -> select/rank candidates
 -> apply unit-specific DSL(s)
 -> apply common policy gates
 -> run in parallel
 -> inspect exact charts/evidence
 -> optimize parameters
 -> propose bounded structural improvement
 -> validate on unseen scenario/cohort/window
 -> promote/reject with immutable memory
```

That is the product-level meaning of combining **market knowledge (where/whom to fight) + self knowledge (how to fight)** in a verifiable DSL system.
