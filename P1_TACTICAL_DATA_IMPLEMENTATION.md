# P1 Tactical Data / 1516 Vertical Slice

Status: **IMPLEMENTED_AWAITING_TRUSTED_WINDOWS_VALIDATION**
Updated: 2026-08-26 KST

## Scope

This tranche connects the validated multi-layer P0 engine to the first real
production-oriented Tactical Unit boundary: the Kiwoom `1516 @ 09:05`
performance cohort.

It does **not** claim profitability or live-trading readiness.

## Data authority

`performance_db.performance_result` is treated as two logically separate
regions.

### Point-in-time cohort input

- `search_date`
- `search_time`
- `condition_name`
- `hold_period`
- `code`
- `name`
- `search_volume`

### Post-search outcome evidence

- `ret_1m`
- `ret_3m`
- `ret_7h`
- `max_ret_in_period`
- `label_3`
- `label_5`
- `label_10`
- `actual_rank_by_max_ret`

Outcome fields are never copied into `CohortMember.features`.

## New modules

### `core/tactical_providers.py`

- `Performance1516CohortProvider`
- `PointInTimeMetricCohortProvider`
- `TacticalCohortBundle`
- `MySQLQueryExecutor`

The 1516 provider performs an exact group lookup only. No nearest date,
different condition, different hold period or dummy universe is substituted.

### `core/tactical_market.py`

`MySQLBarProvider` reads one explicitly configured OHLCV table, discovers a
small set of canonical schema aliases, validates OHLCV/timestamp integrity and
requires the requested warm-up bar count.

The provider fails when the requested timeframe differs from the configured
table timeframe.

### `core/tactical_research.py`

`TacticalResearchService.run_1516()` composes:

```text
frozen 1516 cohort
 -> per-symbol canonical OHLCV
 -> capture+1-second common entry gate
 -> deterministic multi-symbol engine
 -> immutable Tactical Scenario/Run
 -> post-execution merge of official 1516 outcomes
 -> cohort retention / precision evidence
```

For a 09:05 capture the common entry gate is `09:05:01`. Therefore a 5-minute
bar stamped 09:05 cannot be used as a post-capture entry fill. The first
eligible bar depends on the actual canonical timestamps supplied by the market
provider.

Point-in-time feature ranking such as `feature:search_volume` is calculated
from frozen cohort metadata only. It is not derived from post-search return or
`label_10`.

### `core/tactical_chart_document.py`

Builds Chart Document v1 using only generic Chart primitives.

Comparison symbols are selected from the point-in-time ranking, not from
`label_10` or `max_ret_in_period`.

### `core/tactical_validation_runner.py`

Aggregates already-executed immutable cohort reports strictly according to
`TacticalValidationManifest`. It does not repartition or reselect cohorts from
outcomes.

### `tactical_main.py`

Runs the existing Stage 1 application plus:

- `/tactical`
- `GET /api/stage1/tactical/1516/cohort`
- `POST /api/stage1/tactical/1516/run`
- `GET /api/stage1/tactical/health`

The cohort-inspection endpoint intentionally omits future outcomes.

## UI

`/tactical` exposes one operational 1516 workflow:

```text
load exact cohort
 -> inspect point-in-time membership/features
 -> run one DSL across the cohort
 -> inspect retention/precision
 -> inspect per-symbol official outcome only after execution
 -> render multi-symbol normalized comparison + focus audit in shared Chart SSOT
```

## Validation boundary

New tests are named `test_stage1_*.py`, so the existing Stage 1 discovery step
will execute them automatically.

This tranche must remain `REMEDIATION_REQUIRED` until the trusted local Windows
Full verifier is run on the new commit and returns PASS.

## Remaining P1 work

1. High-Beta exact snapshot adapter wired to the concrete beta source.
2. Leading-Sector / leader-follower point-in-time provider wired to its concrete
   source.
3. multi-unit scenario comparison and scenario/date/window OOS workbench.
4. operational launcher integration for `tactical_main:app`.
5. stress tests with large cohorts / worker counts / missing-data faults.
