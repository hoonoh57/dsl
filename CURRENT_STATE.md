# Quant DSL Current State

Status: **CTXDSL1_GENERIC_PARENT_CONTEXT_REFERENCE_IMPLEMENTED_AWAITING_TRUSTED_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
12. earlier product/execution/playbook/audit checkpoints
13. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted Full checkpoints

Every exact checkout below received operator:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

```text
E0    ac01525223f897f155de63f02529b0a6429a0882
E1    6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2    620f741730b0ae821fc48affd22b5420f38a6cac
E3A   06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3    cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4    560526b7f5af19462a57fd1e5b433bcbe5596500
E5    c1351152d58e4219b9998f0b35b7636f340dc986
E6    ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7    dc420d7f7961a4f0517b00c059d159b8face706c
E8    3256f1de6b9bb7e8b79342ea037edcd51125bcda
PCTX1 866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
```

E4's first Full failure was an `environment issue` caused by a stale external Chart SSOT checkout; the same DSL SHA passed after the Chart dependency was fast-forwarded without weakening product/tests.

## Core / parent-context architecture

Core remains single-instrument and deterministic. Provider calculation/I/O, peer-symbol discovery/ranking, universe/allocation, adaptive learning and external DB/network behavior remain outside Instrument DSL evaluation.

Trusted parent-context production/transport is now:

```text
PCTX1 registered typed Provider Result
 -> immutable ParentContextAssembly
 -> PCTX2B exact DEPLOYMENT/OBSERVED ParentContextFrame
 -> exact-time read-only binding
```

PCTX2B policy remains:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

## CTXDSL1 current Core-facing tranche

CTXDSL1 validates the one generic context-reference seam reserved by the Core Freeze policy.

New executable:

```text
core/dsl_context.py
```

Core files changed:

```text
core/dsl_parser.py
core/dsl_semantic.py
core/dsl_runtime.py
core/bar_runtime.py
```

Regression:

```text
test_stage1_dsl_parent_context.py
```

Syntax is generic and feature-registry driven:

```dsl
market_ok = ctx.market.kospi_slope > 0
regime_ok = ctx.market.regime_state == "RISK_ON"
permission = ctx.market.entry_permitted
```

No feature-specific parser/runtime function is added. `ctx` is a reserved read-only namespace.

### Executable binding contract

Schema/policy:

```text
dsl_parent_context_series/v1
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

Executable binding requires:

- PCTX2B `DEPLOYMENT` frame only;
- matching PCTX1 registry;
- exact target timestamp for every bar;
- stable manifest topology;
- registered `required=true` feature;
- typed NUMBER/BOOLEAN/STRING value.

Optional-absent features are not silently defaulted into executable DSL. Unknown/unbound features fail semantic analysis.

Direct `ctx.*[n]` history is rejected in v1 so the language does not invent a second hidden parent-context resampling/history policy.

`on_bar` may read the exact current-bar frozen value, but cannot mutate `ctx`.

### Existing behavior and boundaries

DSLs with no `ctx.*` binding retain the existing compile path. A DSL that references `ctx.*` without an exact binding fails closed.

CTXDSL1 has **not** changed:

```text
BacktestEngine
BrokerEmulator
TA/indicator calculations
provider calculation/I/O
entry_gate/common execution policy
Chart SSOT
```

Backtest context-frame integration is a separate future executable boundary.

## Remote CI status

GitHub Actions for executable head `97f9d37b811cb0e70174cb4990d658a2be32478e` did not execute tests. Both workflows terminated before any step received a runner (`runner_id=0`, empty step list).

Classification:

```text
environment issue
```

No test/workflow/product guard was weakened. Therefore CTXDSL1 is **not trusted yet** and needs local execution evidence.

## Current nonclaims

Do not claim yet:

- trusted Full PASS for CTXDSL1;
- production KOSPI/KOSDAQ/Sector/Group parent providers;
- profitable/generalizing parent-context strategy rules;
- Backtest/Broker operational context authority;
- automatic macro gating or allocation;
- arbitrary peer-symbol access from DSL;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

First run the focused new regression at the exact current checkout:

```powershell
python -m unittest -v test_stage1_dsl_parent_context.py
```

If focused regression passes, run:

```powershell
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If any executable test fails, classify first as exactly `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown` before changing code.
