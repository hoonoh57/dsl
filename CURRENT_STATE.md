# Quant DSL Current State

Status: **P1_1516_VERTICAL_SLICE_IMPLEMENTED_AWAITING_TRUSTED_VALIDATION / REMEDIATION_REQUIRED**
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `MULTI_LAYER_DSL_ARCHITECTURE.md` — current product architecture and Tactical Unit methodology.
2. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — current P1 1516 data/provider/UI implementation checkpoint.
3. `PRODUCT_IMPLEMENTATION_PLAN.md` — original product roadmap and validated Stage 1 kernel plan.
4. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification operating policy.
5. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
6. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.

## Product definition

The validated single-symbol engine is the instrument-level tactical kernel, not the final research methodology.

The product path remains:

```text
Market Regime / Opportunity Window
 -> eligible Tactical Unit
 -> point-in-time multi-symbol cohort
 -> relative / lead-lag / group evidence
 -> unit-specific DSL tactic
 -> common execution policy
 -> parallel deterministic execution
 -> scenario/cohort/window validation
 -> promote / reject / remember
```

`1516 @ 09:05`, High-Beta, Leading-Sector, Theme/Policy and future condition-search cohorts are separate Tactical Units and may own different features and tactics.

For `1516 @ 09:05`, cohort membership is frozen first. Post-search `max_ret_in_period` / `label_10` are outcome evidence only and may not participate in cohort construction or pre-execution candidate ranking.

## Trusted validation checkpoint before this P1 tranche

The current branch base was the multi-layer P0 checkpoint that had a trusted local Windows PowerShell 5.1 Full verifier PASS:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

That PASS remains evidence for the P0 base commit. It does **not** automatically validate the P1 mutations described below.

## P1 1516 vertical slice now implemented

### Production point-in-time cohort provider

`core/tactical_providers.py`

- `Performance1516CohortProvider` reads one exact `performance_result` group by search date/time/condition/hold period.
- point-in-time member features are kept separate from future return labels.
- no nearest-date, alternate-condition, alternate-hold or dummy fallback is permitted.
- `label_10` is checked against `max_ret_in_period` and malformed/ambiguous groups fail closed.
- `PointInTimeMetricCohortProvider` supplies a configurable exact-snapshot contract for later High-Beta / sector sources without inventing a source table.

### Stored minute-bar provider

`core/tactical_market.py`

- explicitly configured MySQL database/table;
- schema alias discovery for code/time/OHLCV;
- separate-date/time or datetime timestamp support;
- strict timestamp/OHLCV validation;
- required warm-up coverage;
- exact timeframe/table contract;
- no generated or dummy bars.

Current defaults target the existing 5-minute data-lake naming convention but remain explicit and fail closed when the actual table contract differs.

### 1516 tactical orchestration

`core/tactical_research.py`

The 1516 run path is:

```text
exact frozen cohort
 -> canonical per-symbol bars
 -> capture + 1 second entry authorization
 -> existing MultiSymbolAnalysisEngine / BrokerEmulator
 -> immutable Tactical Scenario/Run
 -> official 1516 outcome merge only after execution
 -> retention / precision evidence
```

For a 09:05:00 cohort the common entry gate is `09:05:01`. Therefore the bar that contains the search observation itself cannot be used as a post-capture entry fill.

Point-in-time feature ranking such as `feature:search_volume` is computed from frozen member metadata only. Future returns and `label_10` are not ranking inputs.

### Multi-symbol Chart Evidence

`core/tactical_chart_document.py`

- emits only generic `chart-document/v1` bars/series/markers/geometries;
- focus/comparison symbols come from point-in-time ranking;
- post-outcome labels are not used to choose what is displayed as selected/near comparison evidence;
- capture cutoff and regime windows are represented as generic vertical-region evidence.

The shared Chart SSOT remains the only chart-native rendering owner.

### Cohort-level validation summary

`core/tactical_validation_runner.py`

- consumes the existing immutable `TacticalValidationManifest`;
- aggregates Train / Validation / OOS reports by frozen cohort hash;
- refuses missing, duplicate or unmanifested cohort reports;
- does not reconstruct partitions from outcomes.

### Tactical application/UI

`tactical_main.py` serves the existing Stage 1 app plus:

```text
/tactical
GET  /api/stage1/tactical/1516/cohort
POST /api/stage1/tactical/1516/run
GET  /api/stage1/tactical/health
```

The cohort inspection endpoint intentionally excludes future outcomes. The run endpoint combines outcomes only after execution and returns the shared Chart Document evidence.

`core/templates/tactical.html` and `core/static/tactical.js` implement the first multi-symbol research UI.

### New regression coverage

The existing Stage 1 discovery pattern will include:

- `test_stage1_tactical_providers.py`
- `test_stage1_tactical_market.py`
- `test_stage1_tactical_research.py`
- `test_stage1_tactical_chart_document.py`
- `test_stage1_tactical_validation_runner.py`

No legacy assertion was weakened to add this tranche.

## Current validation status

The P1 source has been implemented and source-reviewed, but a trusted Windows Full verifier has **not yet been recorded for these mutations**.

Therefore do not claim:

- P1 Full PASS;
- production profitability/generalization;
- completed High-Beta provider integration;
- completed Leading-Sector provider integration;
- live trading readiness;
- donor repository-wide Chart compliance.

`REMEDIATION_REQUIRED` remains authoritative.

## Remaining P1 work before consolidated human validation

Continue implementation without per-feature user validation:

1. operational launcher integration for `tactical_main:app` and tactical health/smoke;
2. tactical operational/stress harness including larger cohorts, worker-count determinism and missing-data faults;
3. concrete High-Beta source discovery/integration without guessing an undocumented table;
4. concrete Leading-Sector / leader-follower source discovery/integration;
5. multi-unit scenario/date/window validation workbench and evidence comparison;
6. then run one consolidated trusted Windows Full verification;
7. only after the automated boundary is green, perform consolidated WYSIWYG/UI validation.

## Failure policy

Any executable failure must first be classified as one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

Do not weaken assertions, add compatibility allowlists, use dummy data, substitute nearby cohorts or bypass Broker/Chart authority to manufacture a PASS.
