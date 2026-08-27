# PCTX2D Explicit Dependency DAG + First SECTOR Provider — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## Trusted predecessor

PCTX2C received operator validation at exact checkout:

```text
7aee063932e0d70d38c2e7f876b140d049029771
Ran 6 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore exact root-provider frame orchestration is trusted Full-green at that SHA.

## Objective

PCTX2D adds the first explicit causal parent dependency graph and the first concrete SECTOR-layer provider without moving discovery, ranking or execution authority into Instrument DSL.

```text
explicit MARKET source/provider
 -> MARKET ParentFeatureProviderResult
 -> explicit dependency edge
 -> SECTOR benchmark provider
 -> SECTOR ParentFeatureProviderResult(parent result_hash)
 -> PCTX1 assembly
 -> PCTX2B exact frame
 -> optional CTXDSL1 / CTXBT1 consumption
```

Provider calculation remains entirely before Backtest.

## Dependency DAG orchestrator

New module:

```text
core/parent_context_dependency_orchestrator.py
```

Schema/policy:

```text
parent_context_dependency_frame_build/v1
EXPLICIT_DEPENDENCY_DAG_PRECOMPUTE_EVERY_EXACT_TARGET_BAR
```

Primary contracts:

```text
ParentProviderNode
DependencyParentContextFrameBuild
DependencyParentContextFrameBuilder
```

Each node declares:

```text
provider
depends_on = tuple[provider_id, ...]
```

The graph rejects:

- duplicate provider IDs;
- unknown dependency IDs;
- self dependency;
- duplicate dependency edges;
- cycles.

Execution order is deterministic topological order with provider-ID tie breaking. Caller node order does not define semantics.

For every exact target time `t`, a node receives only its declared already-computed parent results for `t`. The returned child result must satisfy:

```text
result.as_of == t
result.knowledge_cutoff == t
result.manifest == provider.manifest
sorted(result.dependency_result_hashes)
  == sorted(hash of each supplied declared dependency result)
```

Undeclared, missing or fabricated dependency evidence therefore fails closed.

## First SECTOR provider

New module:

```text
core/sector_parent_feature_provider.py
```

Primary contract:

```text
KrxSectorBenchmarkParentFeatureProvider
```

This provider requires explicit:

```text
SessionMarketProvider
sector_symbol
sector_namespace
source_authority
market_dependency_provider_id
market_return_feature_id
market_regime_feature_id
```

It does not discover sector membership or peer symbols.

### Exact causal inputs

At target `t` the provider requires:

- `as_of == knowledge_cutoff == t`;
- exactly one declared MARKET dependency result at `t`;
- required MARKET public feature IDs present in that dependency manifest;
- sector source ending exactly at `t`;
- no future sector source bar;
- explicit matching sector instrument/timeframe/source;
- sufficient finite history.

The child result stores the exact MARKET `result_hash` in `dependency_result_hashes`.

## Descriptive SECTOR features

For namespace `semiconductor`, v1 can publish:

```text
sector.semiconductor_return_short_pct
sector.semiconductor_return_long_pct
sector.semiconductor_sma_slope_pct
sector.semiconductor_price_to_sma_pct
sector.semiconductor_relative_strength_long_pct
sector.semiconductor_regime_state
sector.semiconductor_market_alignment
```

Relative strength is sector long return minus the declared MARKET long-return feature. `market_alignment` is descriptive alignment of the sector and market trend-state labels.

No feature provides ALLOW/BLOCK/PERMIT/GATE/order/allocation authority.

## Multi-symbol boundary

PCTX2D still does not perform:

```text
sector member discovery
peer-symbol reads from Instrument DSL
leader/follower ranking
cross-sectional selection
universe construction
portfolio allocation
```

A future Multi-Symbol Add-on may calculate such information and publish bounded registered provider outputs, but it remains a separate orchestration layer.

## Execution boundary

PCTX2D does not change:

```text
Parser/Semantic/Runtime ctx.* semantics
BacktestEngine context binding semantics
entry_gate
BrokerEmulator
PCTX2B exact frame resolution
PCTX2A MARKET calculation semantics
```

An OBSERVED frame remains evidence-only. DEPLOYMENT mode only makes exact registered context executable; it is not automatic entry permission.

## Regression

New regression:

```text
test_stage1_parent_context_dependency_orchestrator.py
```

Coverage includes:

- MARKET -> SECTOR exact DAG orchestration;
- end-to-end SECTOR `ctx.*` through CTXBT1/Broker;
- deterministic node-order invariance;
- unknown dependency rejection;
- cycle rejection;
- exact declared MARKET dependency requirement;
- dependency-result-hash equality enforcement;
- descriptive-only SECTOR manifest.

The standard Tactical P1 Full verifier discovers the test through `test_stage1_*.py`.

## Nonclaims

Do not claim yet:

- trusted Full PASS for PCTX2D;
- production sector membership intelligence;
- leader/follower or peer ranking;
- OOS profitability benefit from SECTOR features;
- automatic macro entry authority;
- live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

Validate at one exact checkout before beginning GROUP/leader-follower or operational deployment wiring:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_parent_context_dependency_orchestrator.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```
