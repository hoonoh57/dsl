# CTXDSL1 Generic Read-Only Parent Context Reference — Implementation Checkpoint

Status: **TRUSTED THROUGH COMBINED CTXDSL1 + CTXBT1 FULL CHECKPOINT / 2026-08-27 KST**

## 1. Trusted predecessor and final validation

PCTX2B was trusted at:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXDSL1 first received focused local validation:

```text
python -m unittest -v test_stage1_dsl_parent_context.py
Ran 6 tests in 0.162s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

That first pasted result did not include the exact local SHA, so no standalone exact CTXDSL1 SHA was claimed at that point.

CTXDSL1 was then revalidated together with CTXBT1 at exact checkout:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
python -m unittest -v test_stage1_backtest_parent_context.py
Ran 5 tests in 0.064s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the CTXDSL1 Parser/Semantic/Runtime path is trusted as part of the exact combined checkpoint `99bb2e5f5a248dc61cddb23677b5798b258848f2`.

## 2. Objective

CTXDSL1 is the single generic Core-facing seam reserved by the Core Freeze policy:

```text
precomputed PCTX1 provider results
 -> PCTX2B exact DEPLOYMENT frame
 -> immutable DSLContextSeriesBinding
 -> ctx.<registered feature_id>
 -> existing Instrument DSL calculation
```

It does not add feature-specific provider functions or permit provider calls from DSL execution.

## 3. Syntax

Registered parent features are read by prefixing their stable public feature ID with `ctx.`:

```dsl
market_ok = ctx.market.kospi_slope > 0
regime_ok = ctx.market.regime_state == "RISK_ON"
permission = ctx.market.entry_permitted
```

`ctx` is a reserved read-only namespace. Assignment/state/set attempts targeting `ctx` fail closed.

## 4. Binding policy

Module:

```text
core/dsl_context.py
```

Schema/policy:

```text
dsl_parent_context_series/v1
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

Executable binding requires:

- a PCTX2B DEPLOYMENT frame;
- matching PCTX1 registry;
- exact strictly ordered target timestamps;
- one precomputed context point per bar;
- fixed provider/manifest topology;
- registered `required=true` feature;
- typed NUMBER/BOOLEAN/STRING value.

Optional-absent features remain evidence-side only and are not silently mapped to zero, false or null inside executable DSL.

## 5. Semantic/runtime rules

PCTX public types map to DSL series types:

```text
NUMBER  -> series<number>
BOOLEAN -> series<bool>
STRING  -> series<string>
```

Unknown/unbound `ctx.*` references fail semantic analysis. Direct parent-context history syntax such as:

```text
ctx.market.kospi_slope[1]
```

remains rejected in v1 so the DSL does not create a second implicit resampling/history policy.

`on_bar` may read the exact current-bar frozen value but cannot mutate the namespace.

## 6. Mutation boundary

CTXDSL1 changed:

```text
core/dsl_parser.py
core/dsl_semantic.py
core/dsl_runtime.py
core/bar_runtime.py
```

and added:

```text
core/dsl_context.py
test_stage1_dsl_parent_context.py
```

It does not move provider calculation, DB/network behavior, peer-symbol discovery/ranking or Broker authority into the DSL runtime.

## 7. Nonclaims

CTXDSL1 does not prove that any parent feature improves profitability and does not itself create an operational macro gate. It does not permit arbitrary peer-symbol reads or provider I/O from Instrument DSL.

`REMEDIATION_REQUIRED` remains broader repository status.
