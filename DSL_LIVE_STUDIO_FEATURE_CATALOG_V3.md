# DSL Live Studio Feature Catalog v3

Status: **REMOTE_UNVALIDATED**

Trusted predecessor:

```text
Feature Catalog v2 invariant baseline: 5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
UI integration locally PASS at branch state containing 089b727204088f5ac5dbd6ac041e470f4df2a8c4
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

Current v3 executable checkpoint before local validation:

```text
72013531fca28ea832808a0d3a89f12da3607762
```

Local gate:

```powershell
python -m unittest test_live_studio_feature_invariants_v3.py
python -m unittest test_live_studio_feature_invariants.py
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

No thresholds, guards, Parser rules, Broker rules, or prior invariant expectations may be weakened to obtain PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
