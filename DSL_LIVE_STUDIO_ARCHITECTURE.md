# DSL Live Studio Architecture

Branch: `dsl-live-studio`

## Decision

The UX branch that reused `app_ui.py` is not suitable for measuring current DSL-engine capability because its `/api/backtest` path is a legacy fixed-strategy demo engine. Therefore the live studio is developed as an independent product surface from trusted `main`.

`ux-max-ui` remains only as a workflow/UI experiment and is not an authority for DSL engine performance.

## Direct engine path

```text
user / LLM-produced DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime.compile
 -> BacktestEngine.run
 -> BrokerEmulator
 -> executions / closed trades / diagnostics / metrics / chart data
```

`live_studio_main.py` MUST NOT import `app_ui.py` or reuse the legacy demo `Engine.run_backtest`.

## Data modes

Two modes are deliberately distinct.

### Synthetic engine fixture

Used only to test and measure DSL engine behavior deterministically.

```text
data_claim = SYNTHETIC_ENGINE_FIXTURE
```

This is not real-market evidence.

### Caller-supplied market

The evaluation API accepts explicit OHLCV market data and forwards it to the real Core `BacktestEngine`.

```text
data_claim = CALLER_SUPPLIED_MARKET
```

The source metadata is preserved in `_meta`. Caller-supplied does not automatically prove vendor authenticity; real production adapters and provenance are a later boundary.

## Feature verification catalog

The Live Studio exposes an executable DSL feature catalog. A feature is not considered verified merely because it is registered or documented. Its declared example must pass the real engine path.

```text
catalog feature
 -> example DSL
 -> Parser PASS
 -> Semantic PASS
 -> DSLRuntime / BacktestEngine PASS
 -> BrokerEmulator / diagnostics observable
```

`FUNCTION_SPECS` is the SSOT for registered DSL functions. The catalog test requires every registered function to have an executable case. Non-function grammar/execution cases are registered separately.

Current first-pass categories include:

- TA / indicators
- math / logic
- state primitives
- session primitives
- MTF confirmed-series functions
- scalar input and historical references
- `state` + `on_bar` + `if/else`
- long/short MARKET orders
- LIMIT + stable client id + generic cancel
- `next_open`
- stop-loss / take-profit / trailing settings

Synthetic/intraday fixtures validate engine behavior only; they do not establish profitability or real-market evidence.

## Trusted local evidence — Feature Catalog v1

Local validation on `dsl-live-studio` after test-resource cleanup:

```text
python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.019s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.198s
OK

powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
[PASS] Tactical P1 verification completed: mode=Full.
```

Trusted executable baseline for this evidence includes commit:

```text
c9c5122d799d6c0cb30d45eb37890d16b582d322
```

Status:

```text
DSL_LIVE_STUDIO_DIRECT_CORE_PATH_TRUSTED
DSL_FEATURE_CATALOG_V1_TRUSTED_FULL_PASS
REMEDIATION_REQUIRED
```

## Initial API

```text
GET  /api/capabilities
POST /api/validate
POST /api/evaluate
GET  /api/features
POST /api/features/{feature_id}/run
POST /api/features/run-all
GET  /
```

`/api/validate` runs actual Parser + Semantic validation.

`/api/evaluate` refuses invalid DSL, then invokes `core.backtest.BacktestEngine` directly. It returns current Core outputs including:

- strategy name / timeframe
- metrics and numeric metrics
- executions
- closed trades
- indicators
- equity curve
- signal counts
- rejection counts
- broker history
- MFE / MAE diagnostics
- parent-context diagnostics
- data metadata

## Product priorities

1. Measure the current DSL faithfully before beautifying UI.
2. Never silently substitute a demo strategy for submitted DSL.
3. Keep data provenance visible.
4. Keep hard guards and BrokerEmulator execution semantics authoritative.
5. Natural-language/LLM tooling remains an authoring layer; DSL validation/execution remains deterministic.
6. Extend the executable catalog before adding more product features.
7. Add production historical adapters only after the full executable DSL contract matrix is locally trusted.

## Local trust gate

```powershell
git fetch origin
git switch dsl-live-studio
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Run the independent app:

```powershell
python .\live_studio_main.py
```

Open:

```text
http://127.0.0.1:8010/
```

## Next verification tranche

Before UI expansion or real-market adapters, extend the same catalog approach to non-function execution contracts that are not yet fully represented by Feature Catalog v1:

```text
ctx.* exact parent-context binding
missing/unbound ctx fail-closed
MARKET / LIMIT / STOP / STOP_LIMIT
DAY / GTC / OCO / stable client ids
close_long / close_short / close_position
bar_close / next_open timing
entry_gate suppression-only behavior
entry time window / max entries per day
pending-order cancel and position-occupied suppression
MTF confirmed-only / no-lookahead invariants
hard-guard precedence where exposed through current Core contracts
```

These cases may require dedicated fixtures/runners rather than weakening the generic feature runner. A PASS must demonstrate the intended invariant, not merely that `BacktestEngine.run()` returned without raising.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.
