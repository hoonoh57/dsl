# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1-PCTX2A TRUSTED / PCTX2C ACTIVE / 2026-08-27 KST**

## 1. Governing rule

The Instrument DSL remains a deterministic single-instrument tactical language while being able to inherit verified parent-layer battlefield intelligence.

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, and consumed inside DSL only through a narrow read-only binding contract.**

The DSL may know a stable `feature_id`; it must not know or execute the algorithm that produced the value.

## 2. Responsibility split

```text
source adapter / provider-specific calculator
 -> Parent Feature Provider
 -> ParentFeatureProviderResult
 -> ParentContextAssembly
 -> exact causal ParentContextFrame
 -> generic read-only ctx.* binding
 -> Instrument DSL local tactic
 -> existing Backtest/common execution policy
 -> BrokerEmulator
```

Providers may use authoritative market/index/sector/group data and already-frozen parent results. They do not emit Broker orders or mutate DSL runtime state.

## 3. No provider calls from DSL/Backtest execution

Prohibited inside Parser/Runtime/Backtest evaluation:

```text
market.get_kospi_slope()
sector.find_current_leader()
request_symbol(...)
rank_symbols(...)
network/database discovery
peer-symbol scans
provider.build(...)
```

Executable tactic evaluation receives precomputed immutable context only. No on-demand external behavior is permitted during tactic execution.

## 4. PCTX1 provider/manifest contract — trusted

`core/parent_feature_provider.py` defines:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider Protocol
ParentContextAssembly
ParentContextAssembler
```

Trusted checkpoint:

```text
866bf0a5a25bf6759d1b264d62efcf9f1f277446
[PASS] Tactical P1 verification completed: mode=Full.
```

Public feature semantics are explicit and versioned:

```text
feature_id
feature_key
value_type = NUMBER | STRING | BOOLEAN
semantic_version
causality_policy = CONFIRMED_ONLY
required
missing_policy = FAIL_CLOSED | OPTIONAL_ABSENT
```

Semantic changes require manifest/version identity changes.

## 5. Missing / stale / future behavior

No context value may be guessed.

- future `as_of` -> fail closed;
- manifest staleness exceeded -> fail closed;
- missing required feature -> fail closed;
- undeclared feature -> fail closed;
- incompatible type -> fail closed;
- missing source -> fail closed;
- optional feature -> explicitly absent, never silently zero/false;
- missing dependency -> fail closed.

## 6. PCTX2B exact-time transport — trusted

`core/parent_context_frame.py` defines exact causal transport.

Trusted checkpoint:

```text
ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
[PASS] Tactical P1 verification completed: mode=Full.
```

Every frame point requires:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
```

Resolution remains:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

No nearest lookup, interpolation, hidden carry-forward or provider invocation is permitted during binding.

## 7. Generic Core-facing `ctx.*` and Backtest binding — trusted

CTXDSL1 + CTXBT1 are trusted together at:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
[PASS] Tactical P1 verification completed: mode=Full.
```

Registered required features may be read generically:

```dsl
ctx.market.kospi_sma_slope_pct
ctx.market.kospi_regime_state
```

Binding policy:

```text
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
```

Backtest policy:

```text
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

Supplying context is not an implicit entry gate. Context affects tactic signals only when the DSL explicitly references `ctx.*`; the separate external `entry_gate` and common execution policy remain authoritative restrictions.

## 8. PCTX2A concrete MARKET provider — trusted

`core/market_parent_feature_provider.py` is the first concrete deterministic parent calculator.

Trusted checkpoint:

```text
6f6aef0b09354b1171ce3eccc78d4daa451fe183
Ran 7 tests in 0.013s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Construction requires explicit:

```text
SessionMarketProvider
benchmark_symbol
feature_namespace
source_authority
```

No source/table/benchmark/universe is guessed.

PCTX2A requires exact causal source evidence:

```text
as_of == knowledge_cutoff
last source bar == as_of
no future source bar
strict unique increasing timestamps
matching source instrument/timeframe
```

For a `kospi` namespace it publishes descriptive return, SMA slope, price-to-SMA, ATR, volume-ratio and three-state regime features. It publishes no ALLOW/BLOCK/PERMIT/GATE/allocation/order feature.

## 9. PCTX2C exact root-provider orchestration — current tranche

`core/parent_context_orchestrator.py` precomputes root provider results before tactic execution.

Policy:

```text
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

Input target timeline must explicitly identify:

```text
_meta.instrument
_meta.timeframe
_meta.source
strict exact YYYYMMDDHHMMSS time[]
```

For each target time `t`, every root provider is invoked before Backtest with:

```text
as_of=t
knowledge_cutoff=t
dependencies=None
```

Returned results must match exact time, declared manifest and root-only dependency semantics. The builder then creates PCTX1 assemblies and one PCTX2B frame covering every exact target bar.

Caller provider order must not change registry/frame/build identity.

PCTX2C can create OBSERVED or DEPLOYMENT frames. OBSERVED is evidence-only; DEPLOYMENT is executable-binding eligible but still not an automatic gate.

## 10. Root versus cascading providers

PCTX2C v1 is deliberately root-only.

Allowed now:

```text
independent MARKET provider(s)
 -> exact precomputed frame
```

Not yet implemented:

```text
MARKET result
 -> SECTOR provider dependency
 -> GROUP provider dependency
 -> exact dependency DAG orchestration
```

A child provider may not be silently discovered or smuggled into root orchestration. Cascading provider dependencies require an explicit later tranche with stable dependency identity, topology, point-in-time ordering and regression coverage.

## 11. Evidence before gate

The required progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED parent context
 -> E8 context attribution
 -> separate Validation/OOS evidence
 -> explicit DEPLOYMENT policy evidence
 -> separately validated operational integration
```

Context correlation is not entry authority. Macro intelligence remains an amplifier rather than life support for a weak micro tactic.

## 12. Interaction with Multi-Symbol Add-on

A future Multi-Symbol Add-on may implement Parent Feature Providers for registered outputs such as sector breadth, leader strength, follower alignment or cross-sectional relative strength.

This does not grant Instrument DSL arbitrary peer-symbol reads. Selection/ranking remains outside Instrument DSL and logically distinct from parent-context inheritance.

## 13. Backtest / live parity

Historical path:

```text
source data known by t
 -> provider calculation before tactic execution
 -> immutable result/context at t
 -> exact frame point t
 -> DSL evaluation t
```

Live target path:

```text
new confirmed source data
 -> provider calculation
 -> immutable current context
 -> exact current binding evidence
 -> next tactic evaluation
```

Provider operational mechanisms may differ, but feature semantics, versions, cutoffs, staleness and missing behavior must match.

## 14. Core promotion boundary

Only the generic read-only context reference mechanism belongs in Core. Calculation logic, source I/O, sector membership discovery, leader/follower detection, peer comparison, ranking, universe construction, allocation and model inference remain outside Core.

New Core context capabilities require deterministic causal semantics, exact Backtest/live behavior and repository-level regression coverage.

## 15. Current status / nonclaims

Trusted:

- immutable BattlefieldContext / ContextLayerSnapshot;
- PCTX1 manifest/registry/result/assembly;
- PCTX2B exact-time frame and binder;
- CTXDSL1 generic read-only `ctx.*`;
- CTXBT1 exact Backtest binding;
- PCTX2A concrete deterministic MARKET provider.

Implemented, awaiting validation:

- PCTX2C exact root-provider frame orchestration.

Still not implemented/validated:

- Sector/Group/Leader-Follower dependency DAG providers;
- validated macro OOS profitability benefit;
- automatic operational deployment authorization;
- arbitrary peer-symbol DSL reads;
- cross-symbol ranking/allocation deployment;
- Broker-side parent calculation;
- live-trading readiness.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 16. Immediate gate

Before dependency-DAG parent layers or operational deployment wiring, validate PCTX2C at an exact repository SHA with its focused regression and Tactical P1 Full verifier.
