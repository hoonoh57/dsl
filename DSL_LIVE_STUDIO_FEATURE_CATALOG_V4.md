# DSL Live Studio Feature Catalog v4

Status: **V4_INVARIANTS_TRUSTED / V4_UI_INTEGRATION_REMOTE_UNVALIDATED**

Local focused evidence:

```text
python -m unittest test_live_studio_feature_invariants_v4.py
Ran 5 tests in 0.005s
OK
```

Trusted v4 invariant set:

```text
order.limit_fill
order.cancel_unknown_fail_closed
execution.take_profit_precedence
execution.trailing_stop
```

Scope:

- verifies existing deterministic Core/Broker behavior only
- does not add or weaken Parser, Runtime, Backtest, Broker, risk, or deployment rules
- uses executable example DSL + deterministic fixtures
- no profitability or real-market-data claim

Live Studio integration now combines v2 + v3 + v4 under the existing `실행 계약` catalog and dispatches each invariant to its owning runner. This integration is executable code and remains `REMOTE_UNVALIDATED` until user-local focused PASS.

Next local gate:

```powershell
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_invariant_ui.py
```

`REMEDIATION_REQUIRED` remains the broader repository status.
