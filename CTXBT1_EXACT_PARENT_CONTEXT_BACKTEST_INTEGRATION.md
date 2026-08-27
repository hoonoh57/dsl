# CTXBT1 Exact Parent Context Backtest Integration — Implementation Checkpoint

Status: **IMPLEMENTED / REMOTE CI ENVIRONMENT BLOCKED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## 1. Predecessor evidence

PCTX2B is trusted Full-green at:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXDSL1 then introduced generic read-only `ctx.*` Parser/Semantic/Runtime support. The operator reported:

```text
Ran 6 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

for the requested CTXDSL1 local validation session. The exact local SHA was not included in that pasted output, so the standalone CTXDSL1 exact-SHA checkpoint remains conservatively unclaimed. CTXBT1 validation at an exact later SHA will cover CTXDSL1 and CTXBT1 together.

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

The Backtest does not calculate market regime, sector strength, leader/follower state or any other parent feature.

## 3. New adapter

New module:

```text
core/backtest_parent_context.py
```

Policy:

```text
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

`prepare_backtest_parent_context(...)` requires either both or neither of:

```text
parent_context_frame
parent_feature_registry
```

When supplied it requires:

- `ParentContextFrame` type;
- matching `ParentFeatureRegistry`;
- DEPLOYMENT-only executable frame through CTXDSL1 binding;
- market `_meta.instrument` present;
- market instrument exactly equal to `frame.target_symbol`;
- exact market `time[]` for every context point consumed;
- no nearest lookup, interpolation or fill-forward;
- no provider call or source acquisition during Backtest.

Any exact binding error fails closed as a Backtest boundary error.

## 4. BacktestEngine integration

`BacktestEngine.run(...)` adds optional parameters:

```text
parent_context_frame=None
parent_feature_registry=None
```

When absent, the historical Backtest compile/execution path is unchanged.

When present, CTXBT1 builds exactly one immutable `DSLContextSeriesBinding` from the market bar timeline and passes it to:

```text
DSLRuntime.compile(
    ...,
    context_binding=binding,
    target_times=data["time"],
)
```

The existing timeframe check, signal extraction, entry policy, deferred-order handling, accounting and BrokerEmulator execution remain unchanged.

## 5. No implicit macro gate

Supplying a parent-context frame does not automatically block or permit entries.

```text
context supplied + DSL does not reference ctx.*
 -> same tactic signals/execution as context absent
```

Parent context affects a tactic only when its DSL explicitly references a registered `ctx.*` feature.

The existing external `entry_gate` remains a separate common execution restriction and can still block an entry even when the DSL's parent-context expression is true.

Therefore:

```text
DSL ctx condition
AND optional external entry_gate
AND existing execution policy
 -> BrokerEmulator
```

CTXBT1 does not make parent context an implicit Broker authority.

## 6. Provenance diagnostics

Backtest diagnostics now include a `parent_context` section.

When no context is supplied:

```text
supplied = false
```

When supplied it records only provenance, not hidden provider internals:

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

Execution authority remains:

```text
BrokerEmulator
```

## 7. Regression coverage

New regression:

```text
test_stage1_backtest_parent_context.py
```

Coverage includes:

- end-to-end Backtest consumption of NUMBER/BOOLEAN/STRING parent context;
- exact signal-time behavior;
- unchanged Broker execution authority;
- external `entry_gate` remains separate and restrictive;
- supplying context without `ctx.*` does not implicitly gate/alter a tactic;
- frame/registry pair requirement;
- market symbol versus frame target-symbol mismatch fail-close;
- missing exact context timestamp fail-close;
- OBSERVED frame rejected for executable DSL use;
- ctx-referencing Backtest without a binding fails closed.

The standard Full verifier discovers this file through `test_stage1_*.py`.

## 8. Mutation boundary

CTXBT1 changes:

```text
core/backtest.py
```

and adds:

```text
core/backtest_parent_context.py
test_stage1_backtest_parent_context.py
```

It does not modify:

```text
BrokerEmulator
PCTX1 provider calculation semantics
PCTX2B frame resolution semantics
CTXDSL1 grammar/type semantics
TA/indicator authority
multi-symbol ranking/allocation
production source acquisition
Chart SSOT
```

## 9. Remote CI incident

GitHub Actions for CTXBT1 commits again terminated before any workflow step ran. The jobs had no executable step list and did not obtain a usable runner.

Classification:

```text
environment issue
```

No product test, workflow guard or execution rule was weakened in response.

## 10. Nonclaims

CTXBT1 does not establish:

- a production KOSPI/KOSDAQ parent-feature calculator;
- production Sector/Group/Leader-Follower providers;
- evidence that any macro feature improves profitability;
- automatic deployment authorization;
- Broker-side context calculation;
- arbitrary peer-symbol reads from Instrument DSL;
- live trading readiness;
- repo-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 11. Validation gate

Because remote Actions did not execute product tests, run the focused CTXBT1 regression locally first at the exact checkout:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_backtest_parent_context.py
```

If it passes, run the consolidated boundary at the same SHA:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not begin concrete PCTX2A provider implementation or operational deployment/Broker wiring until CTXBT1 receives trusted executable validation.
