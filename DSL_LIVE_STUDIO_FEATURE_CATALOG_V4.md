# DSL Live Studio Feature Catalog v4

Status: **V4_INVARIANTS_TRUSTED / V4_UI_INTEGRATION_TRUSTED**

Local focused evidence:

```text
python -m unittest test_live_studio_feature_invariants_v4.py
Ran 5 tests in 0.005s
OK

python -m unittest test_live_studio_invariant_ui.py
Ran 6 tests in 0.032s
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

Live Studio integration combines v2 + v3 + v4 under the existing `실행 계약` catalog and dispatches each invariant to its owning runner.

The v4 UI integration is now trusted by exact user-local focused PASS evidence. The next mainline step is manual/visual Live Studio verification: select categorized feature or execution-contract examples, inspect the loaded DSL, run validation and Core backtest/invariant execution, and confirm the observable result matches the documented intent.

This manual verification remains distinct from automated invariant PASS. Synthetic fixtures are engine-verification data only and must not be represented as authenticated real-market data.

`REMEDIATION_REQUIRED` remains the broader repository status.
