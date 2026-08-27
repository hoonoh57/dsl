# PCTX2B Causal Parent Context Frame / Read-Only Binder — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## 1. Trusted predecessor

PCTX1 Parent Feature Provider / Feature Manifest was operator-validated at exact DSL checkout:

```text
866bf0a5a25bf6759d1b264d62efcf9f1f277446
[PASS] Tactical P1 verification completed: mode=Full.
```

## 2. PCTX2B objective

PCTX2B defines the exact intraday time-axis contract between immutable parent-context production and future tactic consumption.

```text
PCTX1 provider results
 -> exact ParentContextAssembly per decision timestamp
 -> ParentContextFrame
 -> exact read-only ParentContextBinder
```

Every point requires:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
```

Resolution policy:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
```

Missing timestamps fail closed. No nearest substitution, interpolation, implicit carry-forward or provider call occurs during lookup.

## 3. Executable contracts

```text
core/parent_context_frame.py
```

Schemas:

```text
parent_context_frame/v1
parent_context_binding/v1
```

Primary contracts:

```text
ParentContextPoint
ParentContextFrame
BoundParentFeature
ParentContextBinding
ParentContextBinder
```

One frame is scoped to one target instrument, one OBSERVED/DEPLOYMENT mode and one stable registered manifest topology. Provider/version drift inside a frame fails closed.

Binding policy:

```text
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

The binder resolves registered feature IDs from an already-frozen exact-time context and re-checks NUMBER/STRING/BOOLEAN types. Optional absence remains explicit `present=false`, `value=null` evidence.

## 4. Regression coverage

```text
test_stage1_parent_context_frame.py
```

Coverage includes deterministic ordering/identity, exact-time resolution, no nearest/fill-forward behavior, target/cutoff/context-as-of equality, provider/manifest drift rejection, typed registered binding, optional absence, unknown feature/registry mismatch/missing point fail-close.

## 5. Mutation boundary

PCTX2B itself changed none of Parser/Semantic/Runtime/Backtest/Broker/TA/Chart authority. It established only causal transport and sidecar binding.

## 6. Trusted Full checkpoint

The operator confirmed exact checkout:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
```

and ran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **PCTX2B is trusted Full-green at `ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4`.**

## 7. Next boundary

After PCTX2B became trusted, the user explicitly authorized autonomous remote grammar improvements with local verification requested only when genuinely needed.

The next Core-facing validation tranche is therefore documented separately as:

```text
CTXDSL1_GENERIC_PARENT_CONTEXT_REFERENCE_IMPLEMENTATION.md
```

CTXDSL1 must preserve PCTX2B exact-time/no-provider-call semantics. PCTX2A concrete production providers and operational Backtest/Broker integration remain separate future boundaries.
