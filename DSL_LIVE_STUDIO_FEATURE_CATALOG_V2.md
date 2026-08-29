# DSL Live Studio Feature Catalog v2

Status: **TRUSTED FULL PASS + UI INTEGRATION TRUSTED / 2026-08-29 KST**

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

Trusted executable invariant baseline:

```text
5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
```

Trusted local evidence:

```text
python -m unittest test_live_studio_feature_invariants.py
Ran 5 tests in 0.038s
OK

python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.258s
OK

powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
[PASS] Tactical P1 verification completed: mode=Full.
```

The Live Studio UI integration that exposes v1 feature cases and v2 invariant cases was then locally validated at the branch state containing commit:

```text
089b727204088f5ac5dbd6ac041e470f4df2a8c4
```

with:

```text
test_live_studio_invariant_ui.py
Ran 4 tests in 0.025s
OK
```

plus the v2/core/v1 focused suites above and Full PASS. Therefore the UI integration is trusted as a presentation/runner surface over the already-trusted direct Core paths.

The catalog does not claim profitability or real-data authenticity and does not add deployment authority.

Broader repository status remains:

```text
REMEDIATION_REQUIRED
```
