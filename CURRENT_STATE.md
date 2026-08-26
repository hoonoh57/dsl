# Quant DSL Current State

Status: **MICRO_FIRST_MACRO_READY_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — current implementation order and macro-ready extension seam.
2. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final multi-layer product/deployment architecture and Tactical Unit methodology.
3. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — current micro tactical discovery/competition checkpoint.
4. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — current P1 real-data/provider/UI/verification boundary.
5. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and validated Stage 1 kernel plan.
6. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification operating policy.
7. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
8. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.

## Product direction

Two different orders are now explicitly separated.

### Final runtime / deployment order

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

### Current research / development order

```text
Micro tactic discovery
 -> multi-symbol / multi-date robustness
 -> tactic characterization
 -> tactic competition
 -> context attribution
 -> market/sector/group deployment rules
 -> portfolio command
```

This means macro functionality is architecturally reserved now, but current research priority is to develop the minimum/strongest repeatable individual-stock tactic first.

The validated single-symbol DSL/Backtest/Broker engine remains the instrument-level tactical kernel. Macro layers must be additive context/command layers and may not force a rewrite of Parser, Runtime, Backtest, BrokerEmulator or historical micro evidence.

## Macro-ready seam now implemented

`core/battlefield_context.py`

- `ContextLayerSnapshot`
- `BattlefieldContext`
- `DeploymentDecision`

Current micro baseline uses `BattlefieldContext(mode="NEUTRAL")`.

Later market/index, breadth/volatility, sector, high-beta, theme/policy, leader/follower and other point-in-time context can be attached as immutable layer snapshots.

A context timestamp later than a battle knowledge cutoff fails closed.

Macro context is not permitted to mutate:

- DSL source;
- indicator calculations;
- historical OHLCV;
- BrokerEmulator accounting;
- previously recorded micro results.

A future `DeploymentDecision` may allow/block/prioritize a validated tactic, but does not rewrite the tactic.

## Micro tactical discovery now implemented

`core/tactical_discovery.py`

### BattleCase

The atomic research battle is `case_id`, not symbol alone.

This allows the same symbol to appear on many dates while preserving independent battle identity.

Each BattleCase records:

- symbol;
- session date;
- canonical OHLCV snapshot;
- execution settings;
- battle knowledge cutoff;
- optional immutable BattlefieldContext;
- optional explicit entry gate;
- metadata and immutable case hash.

### TacticCandidate

A candidate records:

- candidate id;
- DSL source;
- explicit complexity units;
- metadata;
- immutable candidate hash.

Complexity is explicit provenance. The engine does not infer a hidden complexity score from source length.

### TacticalDiscoveryEngine

One tactic is executed over a frozen BattleCase set with bounded parallel workers.

Default micro-baseline invariants:

- `NEUTRAL` BattlefieldContext only;
- uniform execution settings across all cases;
- any malformed case fails the whole discovery run;
- result order follows BattleCase input order;
- worker count must not change `case_set_hash`, aggregate evidence or `run_hash`;
- BacktestEngine/BrokerEmulator remain execution/accounting authority.

Aggregate evidence includes:

- profitable / losing / no-trade cases;
- average / median / best / worst case return;
- average / worst MDD;
- total / average trades;
- costs;
- MFE / MAE / MFE giveback;
- finite PF median / infinite-PF case count;
- top-1 / top-3 winner concentration;
- explicit tactic complexity.

Complete per-case Backtest evidence is retained for later chart/failure audit.

## Tactical competition now implemented

`core/tactical_competition.py`

Different tactics may compete only on the exact same frozen `case_set_hash` and context policy.

There is no hidden universal ranking score.

The engine publishes:

- per-metric leaderboards;
- conservative Pareto frontier;
- explicit dominated-by relations;
- immutable comparison hash.

Primary current Pareto axes:

```text
maximize: average return, profitable-case rate
minimize: worst drawdown risk, cost/case, complexity
```

Median return, PF, trade frequency and other evidence remain visible instead of being silently folded into one opaque score.

## Tactical P1 implementation already present

### 1516 exact point-in-time cohort

`core/tactical_providers.py`

- exact `performance_result` group by date/time/condition/hold period;
- `code`, `name`, `search_volume` retained as point-in-time evidence;
- future returns, `max_ret_in_period`, labels and actual future rank isolated as post-execution outcomes;
- malformed/inconsistent groups fail closed;
- no nearby cohort or dummy fallback.

### Explicit stored minute market source

`core/tactical_market.py`

- schema-adaptive OHLCV reader;
- strict timeframe and warm-up coverage;
- timestamp/OHLCV integrity checks;
- no production database/table guess;
- source must be explicit or supplied by `TACTICAL_MINUTE_DATABASE` / `TACTICAL_MINUTE_TABLE`.

No authority was accepted for a guessed general `minute_candles_5m` production table. A known K150-only minute table is not substituted for general 1516 membership.

### 1516 execution/evaluation

`core/tactical_research.py`

```text
exact frozen cohort
 -> canonical per-symbol bars
 -> capture + 1 second entry authorization
 -> existing MultiSymbolAnalysisEngine / Broker authority
 -> immutable Tactical Scenario/Run
 -> official outcome merge after execution only
 -> retention / precision evidence
```

For a 09:05:00 cohort the common entry gate is 09:05:01. Point-in-time feature ranking never uses future outcome fields.

### High-Beta exact-as-of cohort

`core/tactical_beta_provider.py`

- daily exact-as-of cutoff only;
- exact benchmark availability required;
- beta = covariance(benchmark return, symbol return) / benchmark return variance;
- overlap threshold and top-N ranking;
- no nearby-date/future-data fallback;
- production database explicit or `TACTICAL_DAILY_DATABASE`;
- `daily_candles` supported default table contract, overridable by `TACTICAL_DAILY_TABLE`.

`tactical_main.py` exposes exact High-Beta cohort inspection. It does not reuse the same-session 1516 execution timing contract.

### Sector exact membership boundary

`core/tactical_sector_provider.py`

- exact `as_of + sector_id` snapshot;
- explicit database/table only;
- static legacy leader/follower definitions and dummy fallback are not accepted as production PIT authority.

A concrete production sector snapshot source remains unresolved and therefore fail-closed.

### Multi-symbol Chart evidence

`core/tactical_chart_document.py`

- generic `chart-document/v1` only;
- comparison symbols selected from point-in-time ranking only;
- capture visual region uses two strictly increasing real focus-market bar times;
- missing non-zero cutoff evidence fails closed;
- shared Chart SSOT remains the sole Chart-native rendering owner.

### Tactical UI/API

`tactical_main.py`:

```text
/tactical
GET  /api/stage1/tactical/1516/cohort
POST /api/stage1/tactical/1516/run
GET  /api/stage1/tactical/high-beta/cohort
GET  /api/stage1/tactical/health
```

The 1516 inspection route omits future outcomes. Tactical UI requires explicit deployment configuration for minute data.

## Validation and stress boundary

Implemented:

- `scripts/start_tactical_stack.ps1`
  - Start / Status / Stop / Preflight / Smoke;
  - shared Chart and Tactical health;
  - Node >= 24 and Python dependency checks;
  - bounded Chart-repo discovery;
  - tracked-process-only stop;
  - PowerShell 5.1-safe PID-state handling.
- `scripts/tactical_contract_stress.py`
  - multi-symbol worker-count determinism;
  - larger cohort execution;
  - Chart projection;
  - point-in-time leakage rejection;
  - whole-scenario corrupted-data failure;
  - micro TacticalDiscovery worker-count determinism on a larger frozen BattleCase set.
- `scripts/verify_tactical_p1.ps1`
  - base Stage 1 verification;
  - Tactical preflight;
  - quick/full Tactical stress;
  - isolated-port live Tactical/Chart smoke;
  - final PASS marker only after all prior steps succeed.

New Stage1-discovered micro tests:

- `test_stage1_battlefield_context.py`
- `test_stage1_tactical_discovery.py`
- `test_stage1_tactical_competition.py`

Existing P1 Tactical provider/market/research/chart/sector/launcher tests remain active.

No legacy assertion has been weakened to add this tranche.

## Trusted validation history

A trusted local Windows PowerShell 5.1 Full verifier PASS exists for the earlier multi-layer P0 checkpoint:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

The first Tactical P1 Full attempt later found one High-Beta regression fixture defect. The product beta calculation was left unchanged; the fixture was corrected to represent the intended covariance ordering.

The macro-ready micro-discovery mutations described above were added after that failure and have not yet received a trusted local Full PASS.

## Current validation status

Do not claim yet:

- Tactical P1 Full PASS;
- any micro tactic is the strongest/profitable;
- production profitability/generalization;
- live trading readiness;
- completed macro deployment rules;
- a concrete production sector snapshot authority;
- a concrete general 1516 minute table unless supplied by deployment configuration;
- donor repository-wide Chart compliance.

`REMEDIATION_REQUIRED` remains authoritative.

## Next automated boundary

Run one consolidated trusted Windows verification after pulling current `main`:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not begin per-feature UI inspection before that automated boundary is green.

If the verifier fails, classify the first failure as:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before changing code.

If it returns:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

record that exact commit as the trusted macro-ready micro-discovery checkpoint, then continue micro strengthening with:

1. authoritative Korean regular-session BattleCase provider;
2. Tactic Family Registry;
3. multi-case Parameter Seeker adapter;
4. Tactical Characterizer;
5. winner/loser/near-miss Evidence UI;
6. only then incremental macro/sector/context attribution.
