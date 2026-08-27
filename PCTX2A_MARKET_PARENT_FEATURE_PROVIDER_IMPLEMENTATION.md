# PCTX2A Deterministic Market Parent Feature Provider — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## 1. Trusted checkpoint

Operator validation was completed at exact checkout:

```text
6f6aef0b09354b1171ce3eccc78d4daa451fe183
```

Focused regression:

```text
python -m unittest -v test_stage1_market_parent_feature_provider.py
Ran 7 tests in 0.013s
OK
```

Consolidated boundary:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore PCTX2A is trusted Full-green at that exact SHA.

## 2. Objective

PCTX2A is the first concrete deterministic MARKET-layer calculator behind the PCTX1 provider contract.

```text
explicit SessionMarketProvider
 + explicit benchmark symbol / namespace / source authority
 -> deterministic causal benchmark calculations
 -> ParentFeatureProviderResult
 -> PCTX1 ParentContextAssembler
 -> PCTX2B exact frame
 -> optional CTXDSL1 / CTXBT1 consumption
```

The provider remains descriptive evidence, not an ALLOW/BLOCK policy engine.

## 3. Executable

```text
core/market_parent_feature_provider.py
```

Primary contracts:

```text
MarketParentFeatureConfig
KrxBenchmarkMarketParentFeatureProvider
```

Provider version and calculation policy:

```text
v1
EXACT_SOURCE_BAR_PREFIX_DETERMINISTIC_NO_GATE_DECISION
```

## 4. Explicit source authority

Construction requires:

```text
SessionMarketProvider
benchmark_symbol
feature_namespace
source_authority
```

The provider does not guess a source, table, benchmark, universe or target instrument.

The existing `SessionMarketProvider` seam can be backed by an explicitly configured adapter such as `MySQLBarProvider`; unit tests use deterministic fixtures.

## 5. Exact causal source contract

PCTX2A requires:

```text
as_of == knowledge_cutoff
last source bar timestamp == as_of
no source bar timestamp > as_of
strictly increasing unique source timestamps
matching configured benchmark instrument/timeframe
sufficient finite valid OHLCV history
```

A stale/future/malformed source fails closed.

Result metadata carries a deterministic `source_prefix_hash` over the exact source bars used for calculation.

## 6. Descriptive feature set

For namespace `kospi`, v1 publishes:

```text
market.kospi_return_short_pct
market.kospi_return_long_pct
market.kospi_sma_slope_pct
market.kospi_price_to_sma_pct
market.kospi_atr_pct
market.kospi_volume_ratio
market.kospi_regime_state
```

Default config:

```text
timeframe = 5m
short_return_bars = 3
long_return_bars = 12
sma_period = 20
slope_bars = 3
atr_period = 14
volume_period = 20
```

`regime_state` is descriptive `UPTREND / DOWNTREND / MIXED` evidence only. No public feature is an entry permission, block, allocation or order authority.

## 7. Trusted compatibility

Regression verifies:

- explicit manifest/type/descriptive identities;
- deterministic same-prefix result identity;
- changed causal prefix changes result identity;
- future/stale source fail-close;
- source identity mismatch fail-close;
- exact cutoff requirement;
- root dependency rejection;
- config/history fail-close;
- PCTX1 assembly and PCTX2B exact-frame interoperability.

PCTX2A does not alter PCTX2B/CTXDSL1/CTXBT1/Broker semantics.

## 8. Next boundary

The next executable tranche is PCTX2C exact root-provider frame orchestration:

```text
target instrument exact bar timeline
 -> precompute PCTX2A result at every target time
 -> PCTX1 assemblies
 -> PCTX2B frame
```

This orchestration remains outside Backtest execution. Sector/Group dependency DAGs and operational deployment wiring remain later boundaries.

## 9. Nonclaims

PCTX2A does not establish:

- profitable/generalizing macro context;
- validated automatic macro entry authority;
- Sector/Group/Leader-Follower providers;
- multi-symbol ranking/allocation;
- arbitrary peer-symbol DSL reads;
- Broker-side parent calculation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.
