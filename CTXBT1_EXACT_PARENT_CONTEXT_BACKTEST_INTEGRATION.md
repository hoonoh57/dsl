# CTXBT1 Exact Parent Context Backtest Integration — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## 1. Trusted exact checkpoint

The operator validated CTXDSL1 + CTXBT1 together at exact checkout:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
```

Focused CTXBT1 regression:

```text
python -m unittest -v test_stage1_backtest_parent_context.py
Ran 5 tests in 0.064s
OK
```

Consolidated boundary:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **CTXBT1 is trusted Full-green at `99bb2e5f5a248dc61cddb23677b5798b258848f2`**. This exact checkpoint also re-validates the CTXDSL1 grammar/semantic/runtime path included in the same checkout.

## 2. Objective

CTXBT1 wires an already-precomputed parent-context frame into historical Backtest execution without moving provider calculation or deployment authority into Backtest/Broker.

```text
PCTX1 registry/provider results
 -> PCTX2B exact DEPLOYMENT ParentContextFrame
 -> CTXBT1 backtest adapter
 -> CTXDSL1 immutable DSLContextSeriesBinding
 -> DSLRuntime ctx.* series
 -> existing Backtest execution
 -> unchanged BrokerEmulator
```

## 3. Adapter contract

Module:

```text
core/backtest_parent_context.py
```

Policy:

```text
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

`BacktestEngine.run(...)` optionally accepts both:

```text
parent_context_frame
parent_feature_registry
```

Both or neither must be supplied.

When supplied, the adapter requires:

- `DEPLOYMENT` ParentContextFrame;
- matching ParentFeatureRegistry;
- market `_meta.instrument` exactly matching frame target symbol;
- exact market timestamp coverage for every compiled bar;
- registered required typed features only;
- no nearest lookup, fill-forward, interpolation or default substitution;
- no provider/source call from Backtest execution.

## 4. No implicit macro gate

Supplying context alone does not permit or block an entry.

```text
context supplied + DSL does not reference ctx.*
 -> same tactic signals/execution as context absent
```

When the DSL explicitly references `ctx.*`, the resulting tactic signal is still subject to the independent external `entry_gate` and existing common execution policy.

Broker execution authority remains:

```text
BrokerEmulator
```

## 5. Provenance

Backtest diagnostics expose only parent-context provenance:

```text
target_symbol
frame_hash
registry_hash
binding_hash
bar_count
feature_ids
policy
binding_policy
```

This is evidence, not a second execution authority.

## 6. Regression boundary

`test_stage1_backtest_parent_context.py` covers:

- end-to-end `ctx.*` signal to Backtest/Broker path;
- exact timestamp behavior;
- Broker authority unchanged;
- external entry-gate independence;
- no implicit context gate for plain DSL;
- frame/registry pairing;
- target-symbol mismatch fail-close;
- missing exact timestamp fail-close;
- OBSERVED frame rejection;
- unbound `ctx.*` fail-close.

## 7. Remote CI incident

GitHub Actions around CTXDSL1/CTXBT1 repeatedly ended before executing workflow steps, with no usable runner/step list.

Classification:

```text
environment issue
```

No test, workflow guard, DSL semantic or execution rule was weakened.

## 8. Next boundary

With CTXBT1 trusted, the next allowed mainline tranche is:

```text
PCTX2A — concrete deterministic Market Parent Feature Provider
```

Provider calculation remains outside Parser/Semantic/Runtime/Backtest/Broker. Operational deployment authorization, Sector/Group providers and multi-symbol ranking remain later boundaries.

`REMEDIATION_REQUIRED` remains the broader repository-compliance status.
