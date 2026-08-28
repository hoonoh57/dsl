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

### Synthetic engine fixture

```text
data_claim = SYNTHETIC_ENGINE_FIXTURE
```

Used only for deterministic engine verification. It is not real-market evidence.

### Caller-supplied market

```text
data_claim = CALLER_SUPPLIED_MARKET
```

The source metadata is preserved in `_meta`. Caller-supplied does not itself prove vendor authenticity.

## Feature Catalog v1 — trusted

`FUNCTION_SPECS` is the SSOT for registered DSL functions. Each function has an executable example and must pass Parser, Semantic and the actual BacktestEngine path. Non-function grammar/execution examples are registered separately.

Trusted local evidence:

```text
python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.019s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.198s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

Trusted baseline:

```text
c9c5122d799d6c0cb30d45eb37890d16b582d322
```

## Feature Catalog v2 invariant contracts — trusted

V2 does not treat successful execution alone as proof. It asserts the intended observable invariant over the real Core path.

Trusted invariants currently include:

```text
context.exact_binding
context.missing_fail_closed
execution.entry_gate_suppression
execution.next_open_timing
execution.entry_time_window
execution.max_entries_per_day
order.stop_fill
order.stop_limit_fill
order.day_expiry
order.stable_client_cancel
mtf.confirmed_only
```

Trusted local evidence:

```text
python -m unittest test_live_studio_feature_invariants.py
Ran 5 tests in 0.039s
OK

python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.249s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

Trusted executable baseline for V2:

```text
5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
```

Status at that trusted checkpoint:

```text
DSL_LIVE_STUDIO_DIRECT_CORE_PATH_TRUSTED
DSL_FEATURE_CATALOG_V1_TRUSTED_FULL_PASS
DSL_FEATURE_CATALOG_V2_INVARIANTS_TRUSTED_FULL_PASS
REMEDIATION_REQUIRED
```

## Live Studio UI integration

The UI now has two independent verification modes:

```text
기능
 -> executable feature examples
 -> Parser / Semantic / Core Backtest

실행 계약
 -> invariant examples
 -> dedicated fixture/runner
 -> expected invariant assertion
```

APIs:

```text
GET  /api/capabilities
POST /api/validate
POST /api/evaluate
GET  /api/features
POST /api/features/{feature_id}/run
POST /api/features/run-all
GET  /api/invariants
POST /api/invariants/{invariant_id}/run
POST /api/invariants/run-all
GET  /
```

The UI integration is a new tranche above the trusted V2 baseline and remains `REMOTE_UNVALIDATED` until local `test_live_studio_invariant_ui.py` and Full verification pass.

## Product priorities

1. Measure the current DSL faithfully before beautifying UI.
2. Never silently substitute a demo strategy for submitted DSL.
3. Keep data provenance visible.
4. Keep hard guards and BrokerEmulator execution semantics authoritative.
5. Natural-language/LLM tooling remains an authoring layer; DSL validation/execution remains deterministic.
6. Expand invariant coverage before real-market product claims.
7. Do not weaken guards/contracts to make catalog tests pass.

## Current local trust gate

```powershell
git switch dsl-live-studio
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_invariant_ui.py
python -m unittest test_live_studio_feature_invariants.py
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Run:

```powershell
python .\live_studio_main.py
```

Open:

```text
http://127.0.0.1:8010/
```

## Next invariant expansion after UI trust

Remaining high-value contracts include OCO, explicit GTC persistence, close_long / close_short / close_position distinctions, position-occupied suppression, same-bar reentry, hard-guard precedence, and additional fail-closed malformed/unknown identity cases.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.
