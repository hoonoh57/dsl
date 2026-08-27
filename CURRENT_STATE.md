# Quant DSL Current State

Status: **PCTX2A_TRUSTED_FULL_PASS / PCTX2C_EXACT_ROOT_PROVIDER_FRAME_ORCHESTRATION_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
15. earlier product/execution/playbook/audit checkpoints
16. `PROGRESS_CHECKPOINT_2026-08-26.md`

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
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
```

PCTX2A additionally received focused regression:

```text
Ran 7 tests in 0.013s
OK
```

CTXDSL1 + CTXBT1 additionally received focused CTXBT1 regression:

```text
Ran 5 tests in 0.064s
OK
```

E4's first Full failure was an `environment issue` caused by a stale external Chart SSOT checkout. Recent GitHub Actions for parent-context work also ended without executable steps or a usable runner; those incidents remain classified `environment issue`. No test/workflow/product guard was weakened.

## Governing architecture

Core remains deterministic and single-instrument. Provider calculation/I/O, peer-symbol discovery/ranking, universe/allocation, adaptive learning and parent dependency discovery remain outside Instrument DSL execution.

Trusted executable path:

```text
PCTX1 typed provider contract
 -> PCTX2B exact frozen frame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 Backtest exact binding
 -> existing common execution policy
 -> BrokerEmulator
```

Trusted concrete MARKET calculation:

```text
explicit SessionMarketProvider
 + benchmark symbol / namespace / source authority
 -> PCTX2A deterministic MARKET features
 -> PCTX1 result
```

PCTX2C now precomputes that provider evidence for each exact target tactical bar before Backtest:

```text
target instrument exact timeline
 + root provider(s)
 -> PCTX2C precomputation
 -> PCTX1 assembly at each t
 -> PCTX2B frame
 -> optional CTXDSL1 / CTXBT1 use
```

No provider is called from Parser/Semantic/Runtime/Backtest/Broker.

## PCTX2A trusted state

Trusted exact checkpoint:

```text
6f6aef0b09354b1171ce3eccc78d4daa451fe183
Ran 7 tests in 0.013s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

PCTX2A publishes descriptive benchmark features only:

```text
market.<namespace>_return_short_pct
market.<namespace>_return_long_pct
market.<namespace>_sma_slope_pct
market.<namespace>_price_to_sma_pct
market.<namespace>_atr_pct
market.<namespace>_volume_ratio
market.<namespace>_regime_state
```

It requires exact `as_of == knowledge_cutoff`, exact last source bar, no future source bar, explicit source/benchmark/timeframe authority and sufficient valid history. It publishes no ALLOW/BLOCK/PERMIT/GATE/allocation/order feature.

## PCTX2C current executable tranche

New module:

```text
core/parent_context_orchestrator.py
```

New regression:

```text
test_stage1_parent_context_orchestrator.py
```

Detailed checkpoint:

```text
PCTX2C_EXACT_ROOT_PROVIDER_FRAME_ORCHESTRATION.md
```

Schema/policy:

```text
parent_context_frame_build/v1
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

Primary contracts:

```text
ParentContextFrameBuild
RootParentContextFrameBuilder
```

### Exact orchestration contract

Target market must explicitly provide:

```text
_meta.instrument
_meta.timeframe
_meta.source
time[] as unique strictly increasing YYYYMMDDHHMMSS
```

For each target time `t`, every configured root provider is invoked before tactic execution with:

```text
as_of=t
knowledge_cutoff=t
dependencies=None
```

Returned result must have exact `as_of`, exact cutoff, the declared manifest and no dependency hashes.

The resulting PCTX1 assembly and PCTX2B frame contain one exact point for every target bar. There is no nearest lookup, fill-forward, interpolation or provider call from Backtest.

### Root-only scope

PCTX2C v1 supports independent root providers only, such as separately configured MARKET benchmark providers. Provider order is normalized by manifest identity, so caller order must not change `registry_hash`, `frame_hash` or `build_hash`.

Sector/Group/Leader-Follower cascading providers require a later explicit dependency-DAG tranche. They are not inferred or smuggled through PCTX2C.

### Execution separation

PCTX2C can build OBSERVED or DEPLOYMENT frames. OBSERVED remains evidence-only and CTXBT1 rejects it for executable `ctx.*` use. DEPLOYMENT merely makes exact binding possible; it does not create an implicit macro gate or Broker permission.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for PCTX2C;
- Sector/Group/Leader-Follower dependency orchestration;
- evidence that parent context improves OOS profitability;
- validated automatic macro entry authority;
- arbitrary peer-symbol reads from Instrument DSL;
- multi-symbol ranking/allocation deployment;
- Broker-side parent calculation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate PCTX2C before beginning dependency-DAG parent layers or operational deployment-policy wiring:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_parent_context_orchestrator.py
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

before changing code.
