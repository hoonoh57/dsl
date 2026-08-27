# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1-PCTX2B + CTXDSL1-CTXBT1 TRUSTED / PCTX2A ACTIVE / 2026-08-27 KST**

## 1. Governing rule

The Instrument DSL remains a deterministic single-instrument tactical language while inheriting verified parent-layer battlefield intelligence only through immutable point-in-time context.

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, and consumed inside DSL only through a narrow registered read-only binding contract.**

The DSL may know a stable `feature_id`; it must not know or execute the provider algorithm that produced the value.

## 2. Responsibility split

```text
source adapter / provider-specific calculator
 -> Parent Feature Provider
 -> ParentFeatureProviderResult
 -> ContextLayerSnapshot
 -> BattlefieldContext
 -> exact causal Context Frame
 -> generic registered ctx.* binding
 -> Instrument DSL local tactic
 -> Backtest common execution policy
 -> BrokerEmulator
```

Providers may read authoritative market/index/sector/group data and already-frozen parent results. They do not emit Broker orders or mutate DSL runtime state.

## 3. Prohibited provider behavior inside DSL execution

Parser/Runtime/Backtest/Broker must not perform:

```text
market.get_kospi_slope()
sector.find_current_leader()
request_symbol(...)
rank_symbols(...)
network/database discovery
peer-symbol scans
provider invocation
```

Runtime receives only precomputed immutable context bindings.

## 4. Trusted PCTX1 provider/manifest contract

`core/parent_feature_provider.py` implements:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider Protocol
ParentContextAssembly
ParentContextAssembler
```

Schemas:

```text
parent_feature_provider/v1
parent_feature_registry/v1
parent_context_assembly/v1
```

Trusted exact checkpoint:

```text
866bf0a5a25bf6759d1b264d62efcf9f1f277446
[PASS] Tactical P1 verification completed: mode=Full.
```

Every public feature has explicit provider/version/layer/context/type/causality/missing semantics. Missing required data, unknown features, incompatible type, missing source, future data, excessive staleness or malformed dependencies fail closed.

## 5. Trusted PCTX2B exact-time transport

`core/parent_context_frame.py` implements immutable exact context transport.

Schemas:

```text
parent_context_frame/v1
parent_context_binding/v1
```

Required point identity:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
```

Resolution policy:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
```

No nearest-time substitution, interpolation, hidden carry-forward or provider call is allowed.

Trusted exact checkpoint:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

## 6. Trusted Core-facing generic binding

CTXDSL1 implements the only allowed generic Core-facing read seam:

```dsl
ctx.market.<registered_feature>
ctx.sector.<registered_feature>
ctx.group.<registered_feature>
```

The syntax is registry-driven rather than feature-specific.

Binding policy:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

NUMBER/BOOLEAN/STRING required features become typed DSL series. Optional absence is not silently converted to zero/false/null. Unknown/unbound features fail closed. Direct `ctx.*[n]` history remains rejected in v1 to avoid a second hidden resampling/history policy.

CTXBT1 connects that immutable binding to Backtest using:

```text
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

Supplying context is not an implicit entry gate. Context affects tactic behavior only when the DSL explicitly references `ctx.*`. The external `entry_gate` remains a separate restrictive common policy. Broker authority remains `BrokerEmulator`.

Trusted combined exact checkpoint:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
Ran 5 CTXBT1 focused tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

This exact checkpoint covers CTXDSL1 and CTXBT1 together.

## 7. PCTX2A concrete MARKET provider — active tranche

The first concrete provider is:

```text
core/market_parent_feature_provider.py
```

Primary contract:

```text
KrxBenchmarkMarketParentFeatureProvider
```

Construction requires explicit:

```text
SessionMarketProvider
benchmark_symbol
feature_namespace
source_authority
```

The provider must not guess a database/table/source/benchmark/universe.

Calculation policy:

```text
EXACT_SOURCE_BAR_PREFIX_DETERMINISTIC_NO_GATE_DECISION
```

PCTX2A requires exact `as_of == knowledge_cutoff`, exact source end-bar identity, no future bars, matching benchmark instrument/timeframe, finite valid OHLCV and sufficient history.

For namespace `kospi`, v1 publishes descriptive registered features:

```text
market.kospi_return_short_pct
market.kospi_return_long_pct
market.kospi_sma_slope_pct
market.kospi_price_to_sma_pct
market.kospi_atr_pct
market.kospi_volume_ratio
market.kospi_regime_state
```

The provider does not publish `ALLOW`, `BLOCK`, `PERMIT`, `GATE`, allocation or order authority. `regime_state` is descriptive context only.

PCTX2A remains awaiting trusted local focused + Full validation at an exact SHA.

## 8. Cascading parent inheritance

Cascading calculation remains explicit and causal:

```text
raw market/index data
 -> MARKET provider result
 -> SECTOR provider result + MARKET result hash
 -> GROUP provider result + parent result hashes
 -> ParentContextAssembler
 -> exact BattlefieldContext frame
```

Every parent dependency is immutable `result_hash` evidence. Missing/future dependencies fail closed.

## 9. Evidence before gate

The deployment progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED parent context
 -> E8 context attribution
 -> separate Validation/OOS evidence
 -> explicit DEPLOYMENT policy evidence
 -> separately validated operational integration
```

A descriptive market regime is not itself entry authority. Parent context must amplify a valid micro tactic rather than become life support for a weak one.

## 10. Multi-symbol boundary

A future Multi-Symbol Add-on may publish registered sector/group features through this provider seam, but Instrument DSL still may not perform arbitrary peer-symbol reads, universe construction, ranking or allocation.

Selection/ranking remains separate from parent-context inheritance.

## 11. Backtest/live parity

Backtest semantics:

```text
source data known by t
 -> deterministic provider calculation
 -> immutable provider result/context at t
 -> exact frame point at t
 -> ctx.* tactic evaluation at t
```

Live semantics must preserve the same feature definition, provider version, cutoff, missing/stale behavior and exact decision-time contract even if operational source adapters differ.

## 12. Core promotion boundary

Only generic read-only registered context references belong in Core.

Still outside Core:

- market/sector/group calculation logic;
- provider I/O;
- source/database/network acquisition;
- sector membership discovery;
- leader/follower detection;
- peer-symbol comparison/ranking;
- universe construction;
- portfolio allocation;
- adaptive/model inference producing context.

## 13. Current nonclaims

Do not claim yet:

- PCTX2A trusted Full PASS;
- OOS profitability benefit from PCTX2A features;
- production Sector/Group/Leader-Follower providers;
- automatic deployment authorization from market context;
- arbitrary peer-symbol DSL access;
- autonomous allocation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 14. Immediate gate

Validate PCTX2A focused regression and Tactical P1 Full at one exact checkout before beginning later parent layers or operational deployment-policy wiring.

If a verifier fails, classify the first executable failure before editing as exactly:

```text
test defect
product defect
authority drift
environment issue
unknown
```
