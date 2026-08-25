# Quant DSL Current State

Status: **MULTI_LAYER_P0_IMPLEMENTED_AWAITING_TRUSTED_VALIDATION / REMEDIATION_REQUIRED**
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `MULTI_LAYER_DSL_ARCHITECTURE.md` — current product architecture addendum and three-layer tactical requirement. **Where it conflicts with the older sequential Stage 2/3/4 assumption, this document wins.**
2. `PRODUCT_IMPLEMENTATION_PLAN.md` — original product roadmap and validated Stage 1 kernel plan.
3. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification operating policy.
4. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
5. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.

## Product correction established during consolidated UI review

The trusted Stage 1 single-symbol engine is a **tactical execution kernel / workbench**, not the final research methodology.

The product is not:

```text
random single symbol
 -> write one strategy
 -> optimize numeric parameters
 -> final 20% bars as universal OOS
```

The product is:

```text
Market Regime / Opportunity Window
 -> eligible Tactical Unit
 -> point-in-time multi-symbol cohort
 -> relative / lead-lag / leader-follower evidence
 -> unit-specific DSL tactic
 -> common execution policy
 -> parallel deterministic execution
 -> scenario/cohort/window validation
 -> promote / reject / remember
```

Examples of distinct Tactical Units include `1516 @ 09:05`, High-Beta, Leading-Sector, Theme/Policy and future condition-search cohorts.  Each may own different feature logic, mission labels and strategy families.

For `1516 @ 09:05`, the captured cohort is fixed first; same-day post-capture `MFE >= 10%` is an outcome label, not a cohort-selection input.

## Historical trusted Stage 1 checkpoint

Before the multi-layer extension, the trusted local Windows PowerShell 5.1 verifier completed:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

That PASS remains valid evidence for the then-current single-symbol Stage 1 boundary.  It does **not** automatically validate subsequent multi-layer code changes.

## Consolidated UI findings already repaired

The UI review found and repaired concrete product defects without weakening assertions:

- Experiment A/B chart selection was made explicit through A/B chart actions.
- Closed-trade selection now highlights the row and produces selected-trade evidence plus ENTRY/EXIT/holding-region chart emphasis.
- promotion refresh behavior was corrected so current-head state can be reloaded correctly after server restart.
- OOS strict-JSON failure from non-finite metrics such as infinite PF was repaired at the API/storage boundary while preserving engine-internal numeric semantics.

The same UI review also exposed the larger **authority/product-scope drift** recorded in `MULTI_LAYER_DSL_ARCHITECTURE.md`.

## P0 multi-layer implementation now present

### Existing kernel preserved

Parser/Semantic/Runtime/Backtest/Broker/Seeker/Experiment/Chart SSOT remain the trusted instrument-level core.  No second trading engine or ad-hoc cross-symbol DSL runtime was introduced.

### `core/backtest.py`

Common/higher-layer entry controls were added:

```text
entry_gate                 # per-bar higher-layer authorization
entry_start_time           # HHMMSS inclusive
entry_end_time             # HHMMSS exclusive, 240000 sentinel allowed
max_entries_per_day        # 0 = unlimited
```

The policy affects actual entries only; indicator warm-up data remains available to DSL calculations.  Rejection diagnostics distinguish:

```text
higher_layer_gate_blocked
entry_time_blocked
entry_count_blocked
```

Default values preserve previous behavior.

### `core/multi_symbol.py`

New deterministic orchestration/evidence objects:

- `OpportunityWindow`
- `RegimeContext`
- `MissionSpec`
- `TacticalUnitSpec`
- `InstrumentTask`
- `MultiSymbolAnalysisEngine`

Implemented behavior:

- regime can block a Tactical Unit before any backtest is executed;
- opportunity windows produce per-bar entry authorization while retaining full warm-up history;
- multiple symbols execute through a bounded thread pool;
- result order follows Tactical Unit symbol order regardless of worker count;
- any symbol execution failure fails the scenario rather than silently dropping the symbol;
- exact timestamp overlap only — no nearest-time substitution;
- benchmark relative strength, beta, correlation and bounded lead/lag analysis;
- post-capture same-day MFE/MAE mission evidence;
- explicit rank metric;
- deterministic `scenario_hash` and `run_hash` independent of worker count.

### `stage1_main.py`

New API vertical slice:

```text
POST /api/stage1/multi-symbol/analyze
```

The request contains Regime + Tactical Unit + Instrument Tasks + Mission + optional benchmark.  The response is strict-JSON-safe and includes per-symbol backtest/relative/capture evidence plus cohort ranking/summary.

Health now advertises:

```text
multi_symbol_contract = multi_symbol_tactical/v1
```

### `test_stage1_multilayer.py`

Added contracts for:

- common time gate;
- max entries/day;
- higher-layer opportunity-window gate with warm-up preservation;
- ineligible-unit no-trade blocking;
- deterministic single-worker vs multi-worker scenario/run hashes;
- benchmark-relative ranking;
- post-capture MFE outcome labeling;
- exact capture-time fail-closed behavior.

## Validation status of the new P0 slice

The new files and integration were reviewed remotely at source/contract level.  A trusted local executable regression has **not yet been recorded after these mutations**.

Therefore do not claim:

- new multi-layer Full PASS;
- production High-Beta/1516/sector provider completion;
- process-level performance superiority;
- profitability/generalization;
- live trading readiness.

## Priority after P0

The next coherent productization tranche is P1 from `MULTI_LAYER_DSL_ARCHITECTURE.md`:

1. immutable Tactical Scenario store and lineage;
2. point-in-time cohort providers for 1516 / High-Beta / Leading-Sector;
3. `_AL` + continuation + warm-up-aware market-data provider;
4. multi-symbol shared-Chart Evidence UI with regime shading and selected/near-miss/control comparison;
5. scenario/date/window OOS instead of arbitrary single-stock final-bar OOS;
6. then sector/group cascade, narrative context and portfolio competition.

## Verification policy

Do not ask the user for per-file or per-feature validation.  Continue automatic/static remediation as far as possible.  After one coherent multi-layer implementation tranche, run one consolidated trusted Windows verification.  Any failure must first be classified as test defect / product defect / authority drift / environment issue / unknown; do not weaken tests or add product fallbacks to manufacture green results.
