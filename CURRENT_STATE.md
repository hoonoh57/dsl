# Quant DSL Current State

Status: **PCTX2C_TRUSTED_FULL_PASS / PCTX2D_DEPENDENCY_DAG_SECTOR_PROVIDER_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
13. `PCTX2A_MARKET_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md`
14. `PCTX2C_EXACT_ROOT_PROVIDER_FRAME_ORCHESTRATION.md`
15. `PCTX2D_DEPENDENCY_DAG_SECTOR_PROVIDER_IMPLEMENTATION.md`
16. earlier product/execution/playbook/audit checkpoints
17. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

Every exact checkout below received:

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
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
PCTX2C  7aee063932e0d70d38c2e7f876b140d049029771
```

Focused evidence includes CTXBT1 5 tests, PCTX2A 7 tests and PCTX2C 6 tests, each followed by the consolidated Full PASS at the exact trusted SHA shown above.

## Governing parent-context path

Core remains deterministic and single-instrument. Provider calculation/I/O, universe discovery, peer ranking and allocation remain outside Instrument DSL execution.

Trusted path:

```text
PCTX1 typed/versioned provider contract
 -> PCTX2B exact frozen frame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 Backtest exact binding
 -> existing execution policy
 -> BrokerEmulator
```

Trusted concrete/precompute layers:

```text
explicit benchmark SessionMarketProvider
 -> PCTX2A deterministic MARKET result
 -> PCTX2C exact root precomputation for every target bar
```

No provider is invoked from Parser/Semantic/Runtime/Backtest/Broker.

## PCTX2C trusted state

Trusted exact checkpoint:

```text
7aee063932e0d70d38c2e7f876b140d049029771
Ran 6 tests in 0.107s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

PCTX2C remains root-only and exact-time:

```text
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

## PCTX2D current executable tranche

New modules:

```text
core/parent_context_dependency_orchestrator.py
core/sector_parent_feature_provider.py
```

Regression:

```text
test_stage1_parent_context_dependency_orchestrator.py
```

Detailed checkpoint:

```text
PCTX2D_DEPENDENCY_DAG_SECTOR_PROVIDER_IMPLEMENTATION.md
```

Dependency orchestration policy:

```text
EXPLICIT_DEPENDENCY_DAG_PRECOMPUTE_EVERY_EXACT_TARGET_BAR
```

Each provider node explicitly declares `depends_on=(provider_id, ...)`. The graph rejects unknown/self/duplicate dependencies and cycles. Execution uses deterministic topological order. At every target `t`, each child receives only declared exact parent results from `t`, and its `dependency_result_hashes` must equal the supplied parent result hash set exactly.

### First SECTOR provider

`KrxSectorBenchmarkParentFeatureProvider` consumes:

```text
explicit sector SessionMarketProvider
explicit sector benchmark symbol/namespace/source authority
exact declared MARKET provider result
explicit MARKET return feature_id
explicit MARKET regime feature_id
```

It publishes descriptive features such as sector return, trend, relative strength and market alignment. It does not discover constituents, rank peer symbols or issue ALLOW/BLOCK/PERMIT/GATE/order/allocation authority.

### Execution separation

PCTX2D does not change CTXDSL1 grammar/runtime, CTXBT1 Backtest binding, `entry_gate` or Broker semantics. OBSERVED remains evidence-only. DEPLOYMENT makes registered exact context available but is not automatic entry permission.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for PCTX2D;
- GROUP/Leader-Follower provider logic;
- sector constituent discovery or peer ranking;
- evidence that MARKET/SECTOR context improves OOS profitability;
- validated automatic macro entry authority;
- multi-symbol allocation deployment;
- Broker-side parent calculation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate PCTX2D at one exact checkout before GROUP/leader-follower or operational deployment wiring:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_parent_context_dependency_orchestrator.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If an executable failure occurs, classify it first exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
