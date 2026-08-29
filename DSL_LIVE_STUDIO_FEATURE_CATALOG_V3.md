# DSL Live Studio Feature Catalog v3

Status: **TRUSTED / UI_INTEGRATION_TRUSTED**

Trusted predecessor:

```text
Feature Catalog v2 invariant baseline: 5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
v2 UI integration trusted checkpoint: 089b727204088f5ac5dbd6ac041e470f4df2a8c4
```

v3 adds additional execution invariants without mutating the trusted v2 harness:

- `order.oco_sibling_cancel`
- `order.gtc_persistence`
- `order.close_long`
- `order.close_short`
- `order.close_position`
- `execution.pending_suppressed_position_occupied`
- `execution.same_bar_reentry`
- `execution.risk_exit_precedence`

The last invariant deliberately uses the exact observable Core contract name `risk_exit_precedence`; it does not claim a broader generic `hard_guard` primitive that is not directly surfaced by Backtest diagnostics.

A PASS requires each invariant to assert the intended Broker/Backtest behavior, not merely return without exception.

## Trusted local evidence

During local validation, two harness defects were found and corrected without changing Core/Backtest/Broker behavior or weakening assertions:

1. v3 runners referenced nonexistent public result key `executions`; the documented Backtest public result contract exposes those rows as `trades`.
2. `order.close_short` fixture used an exit condition that never became true in its deterministic market fixture.

Final focused evidence:

```text
python -m unittest test_live_studio_feature_invariants_v3.py
Ran 4 tests in 0.010s
OK
```

Trusted v3 executable correction checkpoint:

```text
be646bd1ac128936f4e1680da09c3b7b7aea744a
```

## Live Studio UI integration

v2 and v3 invariant catalogs are exposed through the same feature-blind `/api/invariants` surface. Selection dispatches by invariant id; run-all aggregates both catalogs. No Parser/Runtime/Backtest/Broker behavior was changed for UI integration.

UI integration commits:

```text
c8783d7fcd4abbc93df94227d0b813e802e20b82
06a0a2204471aba0a96cce8cb62f5309e7a0f31e
```

Local UI evidence:

```text
python -m unittest test_live_studio_invariant_ui.py
Ran 5 tests in 0.028s
OK
```

Therefore Feature Catalog v3 and its Live Studio invariant UI integration are trusted at this boundary.

`REMEDIATION_REQUIRED` remains the broader repository status.
