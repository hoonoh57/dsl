# P1 Tactical Data / Multi-Symbol Research Slice

Status: **IMPLEMENTED_AWAITING_TRUSTED_WINDOWS_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Scope

This tranche connects the validated Stage 1 / multi-layer P0 kernel to the first
production-oriented Tactical Unit workflows.

Implemented boundaries are:

1. Kiwoom `1516 @ 09:05` exact point-in-time cohort and post-execution outcome evaluation;
2. fail-closed stored minute-bar source contract;
3. exact-as-of High-Beta daily cohort inspection;
4. exact point-in-time sector-membership provider contract;
5. multi-symbol Chart Document evidence through the shared Chart SSOT;
6. Tactical launcher, deterministic stress harness and consolidated P1 verifier.

It does **not** claim profitability, live-trading readiness, a concrete sector
snapshot authority, or a trusted P1 Full PASS.

## 1516 data authority

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

Outcome fields are never copied into `CohortMember.features`. `label_10` is
cross-checked against `max_ret_in_period`. Exact-group absence, duplicate codes,
malformed labels and inconsistent ranks fail closed.

## Stored minute-bar authority

`core/tactical_market.py` provides `MySQLBarProvider`.

It supports an explicitly named OHLCV table with either one datetime column or
separate date/time columns, discovers a bounded set of schema aliases, validates
OHLCV/timestamp integrity and requires the requested warm-up count.

There is intentionally **no production database/table default**.

The concrete source must be supplied either by constructor/API fields or:

```text
TACTICAL_MINUTE_DATABASE
TACTICAL_MINUTE_TABLE
TACTICAL_MINUTE_TIMEFRAME   # optional, defaults to 5m
```

Repository audit found no connected-source evidence for a production table named
`minute_candles_5m`. A separate legacy research repository does contain
`minute_candles_k150` with `timeframe_min = 1`, but that source is K150-specific
and therefore is not silently substituted for a general 1516 cohort.

This is an authority decision, not a compatibility fallback: unknown production
minute storage must fail closed.

## 1516 tactical orchestration

`core/tactical_research.py` composes:

```text
frozen 1516 cohort
 -> per-symbol canonical OHLCV
 -> capture + 1 second common entry gate
 -> validated MultiSymbolAnalysisEngine / Broker authority
 -> immutable Tactical Scenario/Run
 -> post-execution merge of official 1516 outcomes
 -> cohort retention / precision evidence
```

For a 09:05:00 capture the common entry gate is `09:05:01`. Therefore the bar
containing the search observation itself cannot authorize a post-capture entry.
The first eligible fill depends on canonical timestamps and execution policy.

Point-in-time ranking such as `feature:search_volume` is calculated from frozen
cohort metadata only. It is not derived from `label_10`, `max_ret_in_period` or
other future outcomes.

## High-Beta exact-as-of cohort

`core/tactical_beta_provider.py` implements `HighBetaDailyCohortProvider`.

The provider:

- queries only rows at or before an explicit `as_of`;
- requires the benchmark to exist on the exact `as_of` date;
- computes `beta = cov(benchmark_return, symbol_return) / var(benchmark_return)`;
- requires minimum overlapping sessions;
- ranks candidates by Beta and freezes the resulting cohort;
- never uses future returns or a nearby date.

The concrete daily table name `daily_candles` is supported by the connected
research repository, but its database is deployment-configurable. Therefore the
P1 provider does not guess the database; supply it explicitly or set:

```text
TACTICAL_DAILY_DATABASE
TACTICAL_DAILY_TABLE        # optional, defaults to daily_candles
```

`tactical_main.py` exposes:

```text
GET /api/stage1/tactical/high-beta/cohort
```

This endpoint is **cohort inspection only**. An end-of-day High-Beta snapshot
must not be forced through the 1516 same-session `capture+1s` timing rule.
Next-session High-Beta tactic execution requires its own explicit timing
contract and is outside this P1 boundary.

## Sector membership

`core/tactical_sector_provider.py` implements
`SectorMembershipSnapshotProvider`.

It requires an explicit database/table plus exact `as_of` and `sector_id`. The
legacy static leader/follower catalog and its dummy fallback are research history,
not production point-in-time membership authority. Until a concrete immutable
sector snapshot source is identified, the provider remains an explicit-source,
fail-closed boundary only.

## Shared Chart evidence

`core/tactical_chart_document.py` emits only generic `chart-document/v1`
bars/series/markers/geometries.

Comparison symbols are selected from point-in-time ranking, never from official
outcomes.

The capture cutoff is preserved exactly in document metadata. Its visual
`vertical-region` now uses two strictly increasing **actual focus-market bar
timestamps** beginning at/after the cutoff. This is required because the donor
Lightweight Chart surface renders a vertical region with rectangle width
`abs(x2-x1)`; equal `fromTime`/`toTime` is invisible. If a non-zero actual-bar
interval cannot be proven, document construction fails closed.

The shared Chart SSOT remains the only Chart-native rendering owner.

## Cohort-level validation

`core/tactical_validation_runner.py` aggregates already-executed immutable
cohort reports strictly according to `TacticalValidationManifest`.

It refuses missing, duplicate or unmanifested cohort reports and never rebuilds
Train/Validation/OOS partitions from outcomes.

## Tactical application/UI

`tactical_main.py` serves the validated Stage 1 app plus:

```text
/tactical
GET  /api/stage1/tactical/1516/cohort
POST /api/stage1/tactical/1516/run
GET  /api/stage1/tactical/high-beta/cohort
GET  /api/stage1/tactical/health
```

The 1516 cohort-inspection endpoint excludes future outcomes. The run endpoint
combines outcomes only after execution and returns shared Chart Document evidence.
The UI does not pre-fill an undocumented minute database/table.

## Operational boundary

`scripts/start_tactical_stack.ps1` supports:

```text
Start | Status | Stop | Preflight | Smoke
```

It resolves the sibling/shared Chart repo, requires Node.js >= 24, checks Python
imports, starts `tactical_main:app` and the donor Chart server, verifies health,
and tracks only processes that it started. PID state construction is written in
PowerShell 5.1-safe explicit assignments.

`scripts/tactical_contract_stress.py` checks deterministic worker-count parity,
large-cohort execution, Chart Document projection, point-in-time leak rejection
and whole-scenario failure on corrupted symbol data. Its synthetic data is an
explicit test fixture only and is never a production fallback.

`scripts/verify_tactical_p1.ps1` runs:

```text
base Stage 1 verifier
 -> Tactical preflight
 -> Tactical quick stress
 -> Tactical full stress (Full mode)
 -> isolated-port live Tactical/Chart smoke
 -> final Tactical P1 PASS marker
```

## Validation status

All P1 mutations remain **unverified on the trusted Windows host** until the
consolidated command actually succeeds there.

Do not claim:

- P1 Full PASS;
- production profitability/generalization;
- live trading readiness;
- a concrete sector membership source;
- a concrete 1516 minute table until supplied by deployment configuration;
- donor repository-wide Chart compliance.

`REMEDIATION_REQUIRED` remains authoritative.

## Next boundary

No per-feature human validation is required now. The next human-visible step is
one consolidated trusted Windows run after this source boundary is merged to
`main`:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure before changing code. If it
passes, record that exact commit as Tactical P1 Full-verified and then perform
one consolidated WYSIWYG/UI validation.
