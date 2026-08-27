# Quant DSL Current State

Status: **PCTX2A_MARKET_PARENT_FEATURE_PROVIDER_IMPLEMENTED_AWAITING_LOCAL_EXECUTABLE_VALIDATION / REMEDIATION_REQUIRED**  
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
14. earlier product/execution/playbook/audit checkpoints
15. `PROGRESS_CHECKPOINT_2026-08-26.md`

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
```

The combined CTXDSL1 + CTXBT1 checkpoint additionally received focused CTXBT1 regression:

```text
Ran 5 tests in 0.064s
OK
```

CTXDSL1 had earlier also received its own focused six-test PASS; the exact later combined checkpoint is the trusted SHA recorded above.

E4's first Full failure was an `environment issue` caused by a stale external Chart SSOT checkout. CTXDSL1/CTXBT1 remote GitHub Actions also encountered an `environment issue`: jobs ended without executable steps or a usable runner. No product/test/workflow guard was weakened for either incident.

## Governing architecture

Core remains deterministic and single-instrument. Parent calculation, source I/O, peer-symbol discovery/ranking, universe/allocation and adaptive learning remain outside Instrument DSL evaluation.

The validated parent-context path is now:

```text
PCTX1 typed provider contract
 -> immutable ParentContextAssembly
 -> PCTX2B exact DEPLOYMENT ParentContextFrame
 -> CTXDSL1 generic read-only ctx.* binding
 -> CTXBT1 Backtest compile integration
 -> existing common execution policy
 -> BrokerEmulator
```

PCTX2A adds the first concrete MARKET calculator before that path:

```text
explicit SessionMarketProvider
 + explicit benchmark symbol / namespace / source authority
 -> PCTX2A deterministic MARKET features
 -> PCTX1 result/context contracts
```

No provider is called from Parser/Semantic/Runtime/Backtest/Broker.

## CTXDSL1 + CTXBT1 trusted state

Generic parent-context DSL references are registry-driven:

```dsl
ctx.market.<registered_feature>
```

Executable binding remains:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

Backtest integration remains:

```text
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

Supplying context is not an implicit entry gate. A plain DSL must behave the same with or without a context frame. A DSL that explicitly uses `ctx.*` remains subject to the separate external `entry_gate` and common execution policy. Broker authority remains `BrokerEmulator`.

Trusted combined checkpoint:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
Ran 5 tests in 0.064s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## PCTX2A current executable tranche

New module:

```text
core/market_parent_feature_provider.py
```

New regression:

```text
test_stage1_market_parent_feature_provider.py
```

Detailed checkpoint:

```text
PCTX2A_MARKET_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md
```

Primary contracts:

```text
MarketParentFeatureConfig
KrxBenchmarkMarketParentFeatureProvider
```

The provider requires explicit:

```text
SessionMarketProvider
benchmark_symbol
feature_namespace
source_authority
```

It never guesses a table, source, benchmark, universe or target instrument.

### Exact causal calculation

PCTX2A v1 requires:

```text
as_of == knowledge_cutoff
last source bar == as_of
no source bar > as_of
strict unique increasing source times
```

Stale/future/malformed source data, source identity mismatch, insufficient history or invalid OHLCV fail closed.

The result records `source_prefix_hash` over the exact source prefix used in calculation.

### Default descriptive feature set

For namespace `kospi`:

```text
market.kospi_return_short_pct
market.kospi_return_long_pct
market.kospi_sma_slope_pct
market.kospi_price_to_sma_pct
market.kospi_atr_pct
market.kospi_volume_ratio
market.kospi_regime_state
```

Default calculation config:

```text
timeframe = 5m
short_return_bars = 3
long_return_bars = 12
sma_period = 20
slope_bars = 3
atr_period = 14
volume_period = 20
```

`regime_state` is only `UPTREND / DOWNTREND / MIXED` descriptive evidence. PCTX2A publishes no ALLOW/BLOCK/PERMIT/GATE/allocation/order feature.

### Integration boundary

PCTX2A output is a normal PCTX1 `ParentFeatureProviderResult` and can flow through PCTX1 assembly and PCTX2B exact frames. It does not change PCTX2B/CTXDSL1/CTXBT1/Broker semantics.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for PCTX2A;
- evidence that PCTX2A market features improve OOS profitability;
- production Sector/Group/Leader-Follower providers;
- validated automatic macro entry authority;
- arbitrary peer-symbol reads from Instrument DSL;
- multi-symbol ranking/allocation deployment;
- Broker-side parent calculation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate the exact PCTX2A checkout before beginning later parent layers or deployment-policy wiring:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_market_parent_feature_provider.py
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
