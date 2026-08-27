# PCTX2A Deterministic Market Parent Feature Provider — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

CTXDSL1 + CTXBT1 were operator-validated together at exact checkout:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
python -m unittest -v test_stage1_backtest_parent_context.py
Ran 5 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the executable path from PCTX2B exact context through generic `ctx.*` and Backtest is trusted Full-green at that SHA.

## 2. Objective

PCTX2A supplies the first concrete deterministic MARKET-layer calculator behind the already-trusted PCTX1 provider contract.

```text
explicit SessionMarketProvider
 + explicit benchmark symbol / namespace / source authority
 -> deterministic causal benchmark calculations
 -> ParentFeatureProviderResult
 -> PCTX1 ParentContextAssembler
 -> PCTX2B exact frame
 -> optional CTXDSL1 / CTXBT1 consumption
```

The provider is descriptive evidence, not an ALLOW/BLOCK policy engine.

## 3. Executable

New module:

```text
core/market_parent_feature_provider.py
```

Primary contracts:

```text
MarketParentFeatureConfig
KrxBenchmarkMarketParentFeatureProvider
```

Provider version:

```text
v1
```

Calculation policy:

```text
EXACT_SOURCE_BAR_PREFIX_DETERMINISTIC_NO_GATE_DECISION
```

## 4. Explicit source authority

The provider does not guess a production source, benchmark, table, universe or market.

Construction requires:

```text
SessionMarketProvider
benchmark_symbol
feature_namespace
source_authority
```

The existing `SessionMarketProvider` seam can therefore be backed by an explicitly configured production adapter such as `MySQLBarProvider`, while unit/regression tests use deterministic fixtures.

The returned source metadata must identify:

- a non-empty source;
- the exact configured benchmark instrument;
- the exact configured timeframe.

## 5. Exact causal source prefix

PCTX2A requires:

```text
as_of == knowledge_cutoff
last source bar timestamp == as_of
no source bar timestamp > as_of
strictly increasing unique source timestamps
```

A stale last bar, future bar, malformed source identity or insufficient history fails closed.

The result metadata carries a deterministic `source_prefix_hash` over only the bars supplied through the exact `as_of` point. Data after `as_of` cannot participate in the feature calculation.

## 6. Feature set

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

The same concrete algorithm can be instantiated with another explicit namespace/symbol such as a separately authorized KOSDAQ benchmark. Each instance gets a distinct manifest identity.

All numeric values are finite `NUMBER`; regime state is `STRING`.

No public feature is named or defined as `allow`, `permit`, `block`, `gate`, allocation or order authority.

## 7. Default semantics

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

Semantics:

- short/long return: current close versus exact N-bar-prior close;
- SMA slope: current trailing SMA versus the same SMA `slope_bars` earlier;
- price-to-SMA: current close displacement from current trailing SMA;
- ATR%: trailing true-range mean divided by current close;
- volume ratio: current volume divided by the prior `volume_period` bars' mean;
- regime state: `UPTREND`, `DOWNTREND` or `MIXED` from current SMA level plus SMA slope sign.

Regime policy:

```text
SMA_LEVEL_AND_SLOPE_THREE_STATE
```

`regime_state` remains a descriptive context feature. It does not automatically authorize an entry.

## 8. PCTX1 compatibility

The provider returns a normal trusted `ParentFeatureProviderResult` with:

```text
manifest
as_of
knowledge_cutoff
source
features
metadata
result_hash
```

It is a root MARKET provider and rejects parent dependencies in v1.

Manifest metadata includes benchmark/source identity, algorithm policy and complete config so changing semantics changes manifest identity.

## 9. PCTX2B compatibility

Provider results can be assembled by `ParentContextAssembler` into `DEPLOYMENT` or `OBSERVED` context and then into exact PCTX2B frames.

PCTX2A does not alter:

```text
ParentContextFrame exact-time semantics
ParentContextBinder
CTXDSL1 grammar/type semantics
CTXBT1 Backtest adapter semantics
BrokerEmulator
entry_gate
```

## 10. Regression coverage

New regression:

```text
test_stage1_market_parent_feature_provider.py
```

Coverage includes:

- explicit manifest/type/descriptive feature identity;
- deterministic same-prefix result identity;
- future source rows cannot affect an earlier exact prefix;
- changing causal prefix changes result identity;
- future/stale source fail-close;
- source instrument/timeframe/source metadata mismatch fail-close;
- exact cutoff requirement;
- root dependency rejection;
- config/history fail-close;
- PCTX1 assembly and PCTX2B exact-frame interoperability.

The Tactical P1 Full verifier discovers this file through `test_stage1_*.py`.

## 11. Deliberate nonclaims

PCTX2A does not establish:

- that any market feature improves profitability;
- a validated macro entry gate;
- a Sector/Group/Leader-Follower provider;
- cross-symbol ranking or allocation;
- arbitrary peer-symbol reads from Instrument DSL;
- provider calls from Parser/Runtime/Backtest/Broker;
- automatic deployment authorization;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## 12. Validation gate

Before beginning a Sector/Group provider or operational deployment-policy wiring, validate this exact tranche locally:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_market_parent_feature_provider.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If an executable failure occurs, classify it first as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```
