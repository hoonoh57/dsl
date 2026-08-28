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

## Initial API

```text
GET  /api/capabilities
POST /api/validate
POST /api/evaluate
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
5. Add production historical adapters only after the direct engine vertical slice is locally trusted.
6. Natural-language/LLM tooling remains an authoring layer; DSL validation/execution remains deterministic.

## Local trust gate

```powershell
git fetch origin
git switch dsl-live-studio
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_core_path.py
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

## Next tranche after local PASS

Build a production-grade historical data adapter/provenance boundary and then a richer evaluation UI over the same direct Core path. Do not reintroduce legacy `app_ui.py` as a dependency.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.
