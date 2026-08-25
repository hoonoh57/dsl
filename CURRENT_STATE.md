# Quant DSL Current State

Status: **MULTI_LAYER_P0_SYSTEM_VALIDATED / REMEDIATION_REQUIRED**
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `MULTI_LAYER_DSL_ARCHITECTURE.md` — current product architecture addendum and three-layer tactical requirement. **Where it conflicts with the older sequential Stage 2/3/4 assumption, this document wins.**
2. `PRODUCT_IMPLEMENTATION_PLAN.md` — original product roadmap and validated Stage 1 kernel plan.
3. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification operating policy.
4. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
5. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.

## Product definition after consolidated UI review

The trusted single-symbol engine is a **tactical execution kernel / workbench**, not the final research methodology.

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

Examples of distinct Tactical Units include `1516 @ 09:05`, High-Beta, Leading-Sector, Theme/Policy and future condition-search cohorts. Each may own different feature logic, mission labels and strategy families.

For `1516 @ 09:05`, the captured cohort is fixed first; same-day post-capture `MFE >= 10%` is an outcome label, not a cohort-selection input.

## Trusted validation checkpoints

### Historical Stage 1 kernel checkpoint

Before the multi-layer extension, the trusted local Windows PowerShell 5.1 verifier completed:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

That remains valid evidence for the single-symbol kernel boundary.

### Multi-layer P0 checkpoint — trusted PASS

After the multi-layer architecture, parallel engine, common entry policy, Kiwoom history/warm-up work, Tactical Cohort/Scenario/Validation components and API integration were added, the user pulled the complete mutation set and ran:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_stage1.ps1 -Mode Full
```

Result:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

This is the first trusted executable Full PASS for the current multi-layer P0 codebase. It validates the current repository's Stage 1 regression boundary plus all newly discovered `test_stage1_*.py` multi-layer contracts included by the verifier.

It does **not** prove:

- profitability/generalization of any tactical unit;
- production readiness of 1516 / High-Beta / Leading-Sector data providers;
- donor repository-wide Chart compliance;
- live trading readiness;
- process/distributed performance superiority.

## Consolidated UI findings already repaired

The UI review found and repaired concrete product defects without weakening assertions:

- Experiment A/B chart selection was made explicit through A/B chart actions.
- Closed-trade selection highlights the row and produces selected-trade evidence plus ENTRY/EXIT/holding-region chart emphasis.
- promotion refresh behavior was corrected so current-head state can be reloaded correctly after server restart.
- OOS strict-JSON failure from non-finite metrics such as infinite PF was repaired at the API/storage boundary while preserving engine-internal numeric semantics.

The same UI review exposed the larger product-scope drift now governed by `MULTI_LAYER_DSL_ARCHITECTURE.md`.

## Current validated multi-layer P0 capabilities

### Existing kernel preserved

Parser/Semantic/Runtime/Backtest/Broker/Seeker/Experiment/Chart SSOT remain the instrument-level core. No second trading engine or ad-hoc cross-symbol DSL runtime was introduced.

### Common tactical policy — `core/backtest.py`

Validated higher-layer entry controls:

```text
entry_gate                 # per-bar higher-layer authorization
entry_start_time           # HHMMSS inclusive
entry_end_time             # HHMMSS exclusive, 240000 sentinel allowed
max_entries_per_day        # 0 = unlimited
```

The policy affects actual entries only; indicator warm-up data remains available to DSL calculations. Rejection diagnostics distinguish:

```text
higher_layer_gate_blocked
entry_time_blocked
entry_count_blocked
```

Default values preserve previous behavior.

### Parallel tactical engine — `core/multi_symbol.py`

Validated orchestration/evidence objects include:

- `OpportunityWindow`
- `RegimeContext`
- `MissionSpec`
- `TacticalUnitSpec`
- `InstrumentTask`
- `MultiSymbolAnalysisEngine`

Current behavior includes:

- regime can block a Tactical Unit before any backtest executes;
- opportunity windows gate entries while retaining complete warm-up history;
- multiple symbols execute through a bounded thread pool;
- result order remains deterministic independent of worker count;
- a symbol execution failure fails the scenario instead of silently dropping that symbol;
- exact timestamp matching only — no nearest-time substitution;
- benchmark relative strength, beta, correlation and bounded lead/lag analysis;
- post-capture same-day MFE/MAE mission evidence;
- explicit ranking metric;
- deterministic scenario/run identity including relevant benchmark/context provenance.

### Point-in-time cohorts — `core/tactical_cohort.py`

Validated boundaries:

- a Tactical Unit cohort is frozen at an explicit `as_of` timestamp;
- capture times may not come from the future relative to the cohort snapshot;
- post-capture outcome fields such as mission success cannot leak into input cohort features;
- missing requested cohort data fails closed instead of falling back to an unrelated universe.

### Immutable tactical research memory — `core/tactical_store.py`

Validated persistence model:

```text
tactical_scenarios
tactical_runs
tactical_heads
```

Scenario and Run evidence are immutable/content-identified. Execution does not implicitly change the applied head; promotion is explicit.

### Tactical validation — `core/tactical_validation.py`

The multi-layer validation unit is a point-in-time cohort/scenario boundary rather than an arbitrary final fraction of one stock's bars. Train/validation/OOS cohort overlap is rejected.

The legacy single-symbol holdout remains useful as an instrument-level diagnostic, but it is not the final Tactical Unit generalization authority.

### Kiwoom history / `_AL` / warm-up — `core/kiwoom_rest.py`

Validated provider contracts now include:

- explicit KRX/NXT/SOR symbol form support, including `_AL` for SOR/all-market data;
- continuation-aware multi-page chart retrieval;
- required-history / warm-up coverage checks;
- fail-closed behavior when the requested history cannot be proven available.

This allows indicator state to be built from pre-entry data (for example 08:00 onward where available) while keeping entry authorization as a separate execution policy.

### Application/API slice — `stage1_main.py`, `core/tactical_service.py`

Current vertical slice includes multi-symbol tactical analysis through the existing Stage 1 application boundary while preserving Broker/Backtest authority.

The multi-layer endpoint returns strict-JSON-safe evidence and keeps the instrument-level DSL as the strategy SSOT.

## Current test coverage added to the trusted verifier boundary

The Full verifier now exercises the newly added multi-layer contracts through normal `test_stage1_*.py` discovery, including:

- `test_stage1_multilayer.py`
- `test_stage1_tactical_store.py`
- `test_stage1_tactical_validation.py`
- `test_stage1_kiwoom_history.py`
- `test_stage1_oos_json_contract.py`

These cover common time/count gates, opportunity windows, regime blocking, deterministic multi-worker results, benchmark identity, post-capture labels, point-in-time leakage rejection, immutable scenario/run storage, cohort OOS separation, Kiwoom continuation/history semantics and strict JSON output.

## Current product status

`MULTI_LAYER_P0_SYSTEM_VALIDATED` means:

- the current multi-layer P0 source is connected;
- the trusted Windows Full verifier is green on the current repository state;
- the validated single-symbol kernel remains intact under the new orchestration layer.

`REMEDIATION_REQUIRED` remains because the product is not yet at the final tactical research/workbench target. P1 data/provider/UI integration is still required before claiming the intended multi-unit research workflow is complete.

## P1 — next coherent implementation tranche

Priority order:

1. **Production point-in-time Tactical Unit providers**
   - `1516 @ 09:05` performance/capture cohorts from the actual performance DB path;
   - High-Beta cohort snapshots from existing beta research assets;
   - Leading-Sector / leader-follower cohort snapshots from market/sector research assets.

2. **Canonical feature/context bundle per Tactical Unit**
   - capture-time trading value / momentum / beta / relative-strength fields;
   - market/regime context;
   - sector/group/theme metadata where known at the cutoff;
   - strict separation of input features from future outcome labels.

3. **Multi-symbol Evidence UI on shared Chart SSOT**
   - market/index + selected symbols;
   - regime/opportunity shading;
   - selected / near-miss / control comparison;
   - exact entry/exit/capture audit.

4. **Scenario/date/window validation runner**
   - train/validation/OOS by immutable cohort snapshots;
   - Tactical Unit-level recall/precision/mission-retention metrics;
   - no random-stock or arbitrary final-bar methodology as final authority.

5. **Tactical-unit-specific Strategy Factory loop**
   - Seeker/LLM iteration scoped to one unit/context contract;
   - preserve different strategy families for 1516, High-Beta, Leading-Sector, Theme/Policy.

6. **Then P2**
   - sector/group cascade;
   - narrative/theme context;
   - portfolio/capital competition;
   - process/distributed parallelism only after measured need and benchmark evidence.

## Verification policy

Do not ask the user for per-file or per-feature validation. Continue implementation and remote/static remediation in coherent tranches. After a coherent P1 slice is connected, perform one consolidated trusted Windows verification. Any failure must first be classified as test defect / product defect / authority drift / environment issue / unknown; do not weaken tests or add product fallbacks to manufacture green results.

## Next action

Proceed with P1 production cohort/provider integration and shared multi-symbol evidence workflow. Do not reopen the old random-single-symbol methodology as the product's final research path.
