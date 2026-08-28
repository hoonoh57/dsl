# DSL Live Studio Feature Catalog v2

Status: **REMOTE_UNVALIDATED**

v1 proved registered DSL functions and core examples could pass Parser/Semantic and the real BacktestEngine. v2 adds explicit observable invariants for execution contracts; merely running without exception is no longer sufficient.

Current invariant set:

- `context.exact_binding`
- `context.missing_fail_closed`
- `execution.entry_gate_suppression`
- `execution.next_open_timing`
- `execution.entry_time_window`
- `execution.max_entries_per_day`
- `order.stop_fill`
- `order.stop_limit_fill`
- `order.day_expiry`
- `order.stable_client_cancel`
- `mtf.confirmed_only`

Each invariant carries a DSL example and a deterministic fixture, executes through the current Core path, and checks an explicit result such as exact context binding coverage, signal/fill timestamp, rejection diagnostics, Broker lifecycle state, client-order cancellation identity, or confirmed-only MTF output.

The catalog does not claim profitability or real-data authenticity and does not add deployment authority.

Local gate:

```powershell
python -m unittest test_live_studio_feature_invariants.py
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Only after local focused + Full PASS should v2 be promoted and exposed as an authoritative UI verification category.
