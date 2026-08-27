# CTXDSL1 Generic Read-Only Parent Context Reference — Implementation Checkpoint

Status: **LOCAL FOCUSED + FULL PASS REPORTED / EXACT STANDALONE SHA NOT ECHOED / 2026-08-27 KST**

## 1. Trusted predecessor

PCTX2B received operator Full validation at exact checkout:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore PCTX2B is trusted Full-green at that SHA.

## 2. Objective

CTXDSL1 validates the single generic Core-facing seam reserved by the Core Freeze policy:

```text
precomputed PCTX1 provider results
 -> PCTX2B exact-time DEPLOYMENT frame
 -> immutable DSLContextSeriesBinding
 -> ctx.<registered feature_id>
 -> existing Instrument DSL calculation
```

It does not add feature-specific provider functions or allow provider calls from DSL execution.

## 3. Syntax

A registered feature ID is referenced by prefixing it with `ctx.`:

```dsl
market_ok = ctx.market.kospi_slope > 0
regime_ok = ctx.market.regime_state == "RISK_ON"
permission = ctx.market.entry_permitted
```

The parser reserves `ctx` as a read-only namespace. Assignment/state/set attempts targeting `ctx` fail closed.

No new parser production is required for each feature; the existing expression AST resolves nested attributes generically against runtime binding metadata.

## 4. Binding contract

New module:

```text
core/dsl_context.py
```

Schema:

```text
dsl_parent_context_series/v1
```

Binding policy:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

`DSLContextSeriesBinding.from_frame(...)` requires:

- a PCTX2B `DEPLOYMENT` frame;
- matching PCTX1 `ParentFeatureRegistry`;
- exact strictly ordered target timestamps;
- one exact precomputed context point for every target timestamp;
- fixed provider/manifest topology;
- registered typed values.

Only `required=true` manifest features are executable in CTXDSL1 v1. Optional-absent features remain evidence-side only and are not silently converted to zero/false/null inside executable DSL expressions.

## 5. Semantic types

PCTX public types map to DSL series types:

```text
NUMBER  -> series<number>
BOOLEAN -> series<bool>
STRING  -> series<string>
```

Equality/inequality supports compatible number, boolean and string values. Ordered comparisons remain numeric-only.

Unknown or unbound `ctx.*` references fail semantic analysis.

Direct history syntax such as:

```text
ctx.market.kospi_slope[1]
```

is intentionally rejected in v1. A required lagged/derived parent value should be defined causally by the provider/frame contract rather than adding a second hidden resampling/history policy.

## 6. Runtime behavior

`DSLRuntime.compile(...)` accepts optional keyword-only:

```text
context_binding
target_times
```

Without `context_binding`, all existing DSL behavior remains unchanged. A DSL that references `ctx.*` without a binding fails closed.

When a binding is supplied:

- `target_times` are mandatory;
- exact target timestamps must equal the binding timeline;
- binding bar count must equal market bar count;
- the runtime receives only frozen arrays;
- no provider, DB, network, universe or peer-symbol operation is invoked;
- `CompiledStrategy.context_binding_hash` preserves exact binding provenance.

`on_bar` may read exact current-bar `ctx.*` values through the same frozen arrays. It cannot mutate the namespace.

## 7. Mutation boundary

CTXDSL1 changes:

```text
core/dsl_parser.py
core/dsl_semantic.py
core/dsl_runtime.py
core/bar_runtime.py
```

and adds:

```text
core/dsl_context.py
test_stage1_dsl_parent_context.py
```

It did not modify BacktestEngine or BrokerEmulator in the CTXDSL1 tranche. Backtest integration is tracked separately as CTXBT1.

## 8. Regression coverage

`test_stage1_dsl_parent_context.py` covers:

- NUMBER/BOOLEAN/STRING registered context reads;
- context arithmetic/boolean/string equality;
- causal `on_bar` reads;
- exact target-time requirement;
- DEPLOYMENT-only executable binding;
- binding-required fail-close;
- unknown/optional executable reference fail-close;
- direct `ctx.*` history rejection;
- `ctx` namespace reassignment rejection;
- deterministic binding identity and provenance.

## 9. Validation evidence

Initial GitHub Actions runs failed before any workflow step ran. Jobs had no usable runner and an empty step list.

Classification:

```text
environment issue
```

No product/test/workflow guard was weakened.

The operator then reported the requested local focused regression result:

```text
Ran 6 tests in 0.162s
OK
```

and immediately afterward:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

The pasted output did not include the local `git rev-parse HEAD` line, so a standalone exact-SHA CTXDSL1 checkpoint is conservatively not asserted. The later exact CTXBT1 Full checkpoint is intended to subsume CTXDSL1 language/runtime coverage.

## 10. Promotion/nonclaims

This tranche implements the generic reserved seam; it does not claim that every parent feature or tactic family should use it. Production use remains opt-in and evidence-gated.

It does not establish:

- a production KOSPI/Sector/Group Provider;
- profitable/generalizing parent-context rules;
- automatic macro gating;
- arbitrary peer-symbol reads;
- network/DB access from DSL;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 11. Next boundary

CTXBT1 is the separate Backtest integration tranche. It may pass only precomputed exact DEPLOYMENT context into CTXDSL1 and must not move provider calculation or Broker authority into Backtest.
