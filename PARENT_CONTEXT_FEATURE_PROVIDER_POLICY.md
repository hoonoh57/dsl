# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / 2026-08-26 KST**

## 1. Purpose

The Instrument DSL must remain a deterministic single-instrument tactical language while still being able to inherit verified parent-layer battlefield intelligence such as market regime, KOSPI/KOSDAQ state, sector leadership, group structure and leader/follower evidence.

The governing rule is:

> **Parent features are computed outside the Instrument DSL, frozen as point-in-time context snapshots, and consumed inside the DSL only through a narrow read-only binding contract.**

The DSL may consume a parent feature without knowing or executing the algorithm that produced it.

## 2. Responsibility split

### Parent Feature Provider

A provider owns the calculation logic for one context domain.

Examples:

```text
MarketFeatureProvider
SectorFeatureProvider
GroupFeatureProvider
LeaderFollowerFeatureProvider
```

A provider may read the authoritative data required for its domain and may depend on already-frozen parent-layer snapshots when the cascade is explicit and causal.

A provider outputs immutable `ContextLayerSnapshot` evidence. It does not emit broker orders and does not mutate Instrument DSL runtime state.

### Context snapshot / assembler

Provider outputs are combined into a `BattlefieldContext` envelope.

Current repository contracts in `core/battlefield_context.py` already define:

```text
ContextLayerSnapshot
  layer
  context_id
  as_of
  source
  features
  snapshot_hash

BattlefieldContext
  as_of
  mode
  layers[]
  context_hash
```

Every layer must be valid at or before the battle `knowledge_cutoff`. Future context is invalid and must fail closed.

### Instrument DSL

The Instrument DSL owns only local tactical computation plus consumption of explicitly registered parent-context values.

The intended future semantic form is conceptually:

```text
ctx.market.kospi_slope
ctx.market.regime_strength
ctx.sector.strength
ctx.sector.leader_strength
ctx.group.follower_alignment
```

The exact syntax is a future validated Core capability. This policy does not add executable grammar yet.

## 3. No provider calls from DSL execution

The DSL must not execute provider logic through function calls such as:

```text
market.get_kospi_slope()
sector.find_current_leader()
request_symbol(...)
rank_symbols(...)
```

The DSL runtime must not perform network calls, database discovery, universe selection, peer-symbol scans or provider-side calculations while evaluating a tactic.

Instead the runtime receives an already-frozen `BattlefieldContext` and resolves registered context references to supplied values.

Conceptually:

```text
Provider calculation
 -> ContextLayerSnapshot
 -> BattlefieldContext
 -> Context Binder
 -> DSL ctx.* read
```

This preserves deterministic replay and allows the provider implementation to evolve independently of the DSL language.

## 4. Parent Feature Manifest

A parent feature exposed to DSL consumption requires an explicit manifest contract.

Recommended fields:

```text
feature_id
layer
value_type
provider_id / provider_version
causality_policy
missing_policy
semantic_version
```

Example:

```text
feature_id: market.kospi_slope
layer: MARKET
value_type: series<number> or point-in-time number according to binding contract
provider_id: market_feature_provider/v1
causality_policy: CONFIRMED_ONLY
missing_policy: FAIL_CLOSED
```

A provider may change its internal implementation only when feature semantics remain compatible with the declared version. A semantic change requires a new feature/provider version and must not silently reinterpret historical evidence.

## 5. Cascading parent inheritance

Parent-layer computation may itself be cascading, but every dependency must be explicit and point-in-time.

Recommended hierarchy:

```text
raw market/index data
 -> MARKET snapshot
 -> sector data + MARKET snapshot
 -> SECTOR snapshot
 -> group/leader-follower data + parent snapshots
 -> GROUP snapshot
 -> Instrument DSL local tactic + inherited context
```

A lower provider may consume a frozen higher-layer snapshot, but it must never read a future revision of that snapshot.

The resulting lineage must remain auditable through snapshot hashes and provider/version identity.

## 6. Evidence mode before gate mode

A new parent feature should first be attached as observation/evidence rather than immediately becoming entry authority.

Recommended progression:

```text
NEUTRAL baseline
 -> OBSERVED parent context
 -> context attribution
 -> Validation / OOS evidence
 -> explicit DEPLOYMENT gate only if justified
```

This preserves the distinction between:

```text
context explains performance
```

and

```text
context is allowed to block/permit entry
```

A weak micro tactic must not be made to appear robust solely because a parent filter removed difficult battles.

## 7. Interaction with multi-symbol Add-on

A future Multi-Symbol Add-on may act as one Parent Feature Provider.

For example it may compute, from explicit point-in-time snapshots:

```text
sector breadth
leader strength
follower alignment
cross-sectional relative strength
leader/follower dispersion
```

and emit those as a GROUP or SECTOR `ContextLayerSnapshot`.

This does not grant the Instrument DSL arbitrary peer-symbol access. The DSL receives only the registered output features.

Thus:

```text
Multi-Symbol Add-on
 -> registered parent features
 -> ContextLayerSnapshot
 -> BattlefieldContext
 -> read-only DSL context binding
```

is allowed, while direct peer-symbol query syntax remains prohibited.

## 8. Missing / stale / mismatched context

No context value may be guessed.

For a DSL candidate that declares a required parent feature:

- missing feature -> fail closed or candidate ineligible according to explicit policy;
- stale `as_of` -> fail closed;
- snapshot later than `knowledge_cutoff` -> fail closed;
- incompatible feature/provider version -> fail closed;
- missing source authority -> fail closed.

Optional context features must be explicitly declared optional. Missing optional context must not silently become zero, false or another plausible value.

## 9. Backtest / live parity

Backtest and live execution must consume the same logical parent-feature contract.

Backtest:

```text
historical data available by time t
 -> provider snapshot at t
 -> frozen BattlefieldContext at t
 -> DSL evaluation at t
```

Live:

```text
new confirmed source data
 -> provider snapshot
 -> current BattlefieldContext
 -> next DSL evaluation
```

The provider may be implemented differently operationally, but feature semantics, cutoff rules and missing behavior must match.

## 10. Core DSL promotion boundary

Only the read-only context-reference mechanism is a candidate for a future Core DSL capability.

The following remain outside Core:

- market-regime calculation logic;
- sector membership discovery;
- leader/follower detection;
- peer-symbol comparison;
- ranking;
- universe construction;
- database/network access;
- model inference used to produce context.

Therefore the Core remains:

```text
local series / state / signals / orders
+ read-only registered parent-context values
```

not a general market-analysis runtime.

## 11. Current implementation status

Already present:

- immutable `ContextLayerSnapshot`;
- immutable `BattlefieldContext`;
- causal `as_of <= knowledge_cutoff` validation;
- context hashes;
- `NEUTRAL / OBSERVED / DEPLOYMENT` modes;
- `DeploymentDecision` command-layer contract.

Not implemented yet:

- general Parent Feature Provider framework;
- Parent Feature Manifest registry;
- Instrument DSL `ctx.*` grammar/type binding;
- runtime Context Binder;
- production market/sector/group provider implementations.

These are future extension seams and must not be implemented before the current executable verification boundary is trusted green.

## 12. Success criterion

The architecture is correct when all of these can be true simultaneously:

```text
Provider knows how to calculate the parent feature.
DSL does not know how it was calculated.
DSL can consume the registered value deterministically.
Historical replay receives the exact point-in-time value.
Provider/Add-on can be replaced without rewriting tactic DSL logic.
Missing/future/stale parent evidence fails closed.
```

This preserves cascading battlefield inheritance without turning Instrument DSL into a multi-market data engine.
