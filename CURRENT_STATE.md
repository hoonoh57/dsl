# Quant DSL Current State

Status: **CTXBT1_EXACT_PARENT_CONTEXT_BACKTEST_IMPLEMENTED_AWAITING_LOCAL_EXECUTABLE_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-27 KST

## Authority order

1. `EVOLVING_MICRO_WARRIOR_PLAN.md`
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md`
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md`
7. `MULTI_LAYER_DSL_ARCHITECTURE.md`
8. E3-E8 implementation checkpoints
9. `PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md`
10. `PCTX2B_PARENT_CONTEXT_FRAME_BINDER_IMPLEMENTATION.md`
11. `CTXDSL1_GENERIC_PARENT_CONTEXT_REFERENCE_IMPLEMENTATION.md`
12. `CTXBT1_EXACT_PARENT_CONTEXT_BACKTEST_INTEGRATION.md`
13. earlier product/execution/playbook/audit checkpoints
14. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

Every exact checkout below received operator:

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

E4's first Full failure was an `environment issue` caused by a stale external Chart SSOT checkout; the same DSL SHA passed after the Chart dependency was fast-forwarded without weakening product/tests.

## Parent-context architecture

Core remains single-instrument and deterministic. Provider calculation/I/O, peer-symbol discovery/ranking, universe/allocation, adaptive learning and external DB/network behavior remain outside Instrument DSL evaluation.

The current parent-context path is:

```text
PCTX1 registered typed Provider Result
 -> immutable ParentContextAssembly
 -> PCTX2B exact DEPLOYMENT ParentContextFrame
 -> CTXDSL1 immutable DSLContextSeriesBinding
 -> generic read-only ctx.* expression
 -> CTXBT1 Backtest compile integration
 -> existing execution policy
 -> BrokerEmulator
```

No provider is called from Parser/Semantic/Runtime/Backtest/Broker.

## PCTX2B trusted transport

PCTX2B remains exact-time and fail-closed:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

Trusted exact checkpoint:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

## CTXDSL1 language/runtime evidence

CTXDSL1 introduced generic registry-driven syntax such as:

```dsl
market_ok = ctx.market.kospi_slope > 0
regime_ok = ctx.market.regime_state == "RISK_ON"
permission = ctx.market.entry_permitted
```

Binding policy:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

The operator reported:

```text
Ran 6 tests in 0.162s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

for the requested CTXDSL1 local validation. The pasted result did not echo the local `git rev-parse HEAD`, so a standalone exact-SHA CTXDSL1 checkpoint is intentionally not claimed. The next exact CTXBT1 Full checkpoint will cover CTXDSL1 and CTXBT1 together.

## CTXBT1 current executable tranche

New adapter:

```text
core/backtest_parent_context.py
```

Changed execution boundary:

```text
core/backtest.py
```

Regression:

```text
test_stage1_backtest_parent_context.py
```

Detailed checkpoint:

```text
CTXBT1_EXACT_PARENT_CONTEXT_BACKTEST_INTEGRATION.md
```

`BacktestEngine.run(...)` now optionally accepts:

```text
parent_context_frame
parent_feature_registry
```

Both or neither must be supplied.

When supplied, CTXBT1 requires:

- a PCTX2B `DEPLOYMENT` frame;
- a matching PCTX1 registry;
- market `_meta.instrument` exactly matching `frame.target_symbol`;
- exact market bar timestamps for the complete binding timeline;
- required typed registered features only;
- no provider call, nearest lookup, fill-forward or default substitution.

The adapter passes one immutable context binding into `DSLRuntime.compile(...)` using the market's exact `time[]`.

### No implicit context gate

Supplying parent context does not automatically block or permit entries.

If a DSL does not reference `ctx.*`, the context frame must not alter tactic signals, trades or accounting. If the DSL does reference `ctx.*`, the resulting tactic signal remains subject to the existing external `entry_gate` and common execution policy.

Broker authority remains:

```text
BrokerEmulator
```

CTXBT1 does not calculate parent features or issue Broker orders independently.

### Provenance

Backtest diagnostics now expose a `parent_context` provenance section including frame/registry/binding hashes, target symbol, bar count, feature IDs and policy. It does not expose provider source logic or create operational authority.

## Remote CI status

GitHub Actions for CTXDSL1 and CTXBT1 commits repeatedly ended before any workflow step executed. Jobs did not receive a usable runner and returned an empty step list.

Classification:

```text
environment issue
```

No workflow, test or product guard was weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted exact Full PASS for CTXBT1;
- a production KOSPI/KOSDAQ parent-feature calculator;
- production Sector/Group/Leader-Follower providers;
- evidence that a parent-context rule improves OOS profitability;
- automatic deployment authorization;
- Broker-side context calculation;
- arbitrary peer-symbol access from Instrument DSL;
- autonomous allocation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Run the focused CTXBT1 regression at the exact current checkout:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_backtest_parent_context.py
```

If focused regression passes, run at the same SHA:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If any executable test fails, classify the first failure exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown` before changing code.

Do not begin PCTX2A concrete provider implementation or operational deployment/Broker wiring before CTXBT1 is green.
