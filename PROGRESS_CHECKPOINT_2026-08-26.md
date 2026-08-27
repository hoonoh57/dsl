# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **PCTX2B_TRUSTED_FULL_PASS / CTXDSL1_LOCAL_PASS_REPORTED / CTXBT1_BACKTEST_CONTEXT_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / CORE_DSL_FREEZE_ACTIVE**

## Trusted exact Full checkpoints

Each exact checkout below received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

```text
E0     ac01525223f897f155de63f02529b0a6429a0882
E1     6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2     620f741730b0ae821fc48affd22b5420f38a6cac
E3A    06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3     cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4     560526b7f5af19462a57fd1e5b433bcbe5596500
E5     c1351152d58e4219b9998f0b35b7636f340dc986
E6     ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7     dc420d7f7961a4f0517b00c059d159b8face706c
E8     3256f1de6b9bb7e8b79342ea037edcd51125bcda
PCTX1  866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
```

E4's first Full failure was `environment issue`: the external Chart SSOT checkout was stale. After fast-forwarding that dependency, the same E4 DSL SHA passed without weakening product/tests.

## Parent-context mainline

Current safe topology:

```text
PCTX1 typed provider contract
 -> PCTX2B exact-time frozen frame
 -> CTXDSL1 generic read-only ctx.* binding
 -> CTXBT1 Backtest compile integration
 -> existing common execution policy
 -> BrokerEmulator
```

Provider calculation, DB/network access, peer-symbol discovery/ranking and portfolio allocation remain outside Instrument DSL and Backtest/Broker execution.

## PCTX2B trusted checkpoint

PCTX2B established:

```text
target_time == knowledge_cutoff == context.as_of
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

Trusted exact SHA:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

## CTXDSL1 local evidence

CTXDSL1 added generic registered parent-context references:

```dsl
ctx.market.kospi_slope
ctx.market.regime_state
ctx.market.entry_permitted
```

with policy:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

The operator reported the requested focused validation:

```text
Ran 6 tests in 0.162s
OK
```

followed by:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

The pasted output did not include the local `git rev-parse HEAD`, so CTXDSL1 is not separately recorded as an exact trusted-SHA checkpoint. CTXBT1's next exact Full validation will subsume the language/runtime change.

## CTXBT1 executable boundary

New files:

```text
core/backtest_parent_context.py
test_stage1_backtest_parent_context.py
CTXBT1_EXACT_PARENT_CONTEXT_BACKTEST_INTEGRATION.md
```

Changed:

```text
core/backtest.py
```

`BacktestEngine.run(...)` optionally receives both:

```text
parent_context_frame
parent_feature_registry
```

The adapter requires exact market bar timestamps, matching target instrument and DEPLOYMENT-only context. It creates one CTXDSL1 immutable binding and passes it to `DSLRuntime.compile(...)`.

No nearest lookup, fill-forward, provider call or missing-value default is permitted.

### Authority separation

Supplying context alone is not an implicit entry gate. A DSL with no `ctx.*` reference must retain the same tactic result with or without a context frame.

When DSL context conditions are used, the existing external `entry_gate` remains an independent restrictive policy. Broker authority remains unchanged.

### Regression

`test_stage1_backtest_parent_context.py` covers:

- exact end-to-end context Backtest execution;
- expected signal timestamps;
- Broker authority unchanged;
- external gate independence;
- no implicit context gating for plain DSL;
- frame/registry pair requirement;
- target-symbol mismatch fail-close;
- missing exact context point fail-close;
- OBSERVED frame rejection;
- unbound ctx-reference rejection.

## Remote CI incident

CTXDSL1 and CTXBT1 GitHub Actions runs ended before any executable step ran. The jobs did not receive a usable runner and exposed no step list.

Classification:

```text
environment issue
```

No product/test/workflow guard was weakened.

## Current validation status

May claim E0-E8, PCTX1 and PCTX2B trusted exact Full PASS. May report CTXDSL1's focused + Full local PASS evidence, but not a standalone exact CTXDSL1 SHA. CTXBT1 is implemented and awaiting local executable validation.

Do not claim production parent providers, profitable macro context, automatic deployment authority, arbitrary peer-symbol DSL access, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate validation

At the exact current checkout:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_backtest_parent_context.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If any executable test fails, classify first as exactly `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown` before editing.
