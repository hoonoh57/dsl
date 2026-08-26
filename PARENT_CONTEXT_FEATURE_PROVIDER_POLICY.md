# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1 ACTIVE / 2026-08-27 KST**

## 1. Governing rule

The Instrument DSL remains a deterministic single-instrument tactical language while being able, later, to inherit verified parent-layer battlefield intelligence.

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, and consumed inside DSL only through a narrow read-only binding contract.**

The DSL may know a stable `feature_id`; it must not know or execute the algorithm that produced the value.

## 2. Responsibility split

```text
source adapter / provider-specific calculator
 -> Parent Feature Provider
 -> ParentFeatureProviderResult
 -> ContextLayerSnapshot
 -> BattlefieldContext
 -> future Context Binder
 -> future registered ctx.* read
 -> Instrument DSL local tactic
```

Providers may use authoritative market/index/sector/group data and already-frozen parent results. They do not emit Broker orders or mutate DSL runtime state.

## 3. No provider calls from DSL execution

Prohibited inside Parser/Runtime evaluation:

```text
market.get_kospi_slope()
sector.find_current_leader()
request_symbol(...)
rank_symbols(...)
network/database discovery
peer-symbol scans
```

Runtime must receive precomputed immutable context. No on-demand external behavior is permitted during tactic evaluation.

## 4. PCTX1 executable contract

`core/parent_feature_provider.py` implements the first generic production seam.

Schemas:

```text
parent_feature_provider/v1
parent_feature_registry/v1
parent_context_assembly/v1
```

Contracts:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider (Protocol)
ParentContextAssembly
ParentContextAssembler
```

PCTX1 is infrastructure, not a production market/sector calculator and not DSL binding.

## 5. Parent Feature Manifest

Every public parent feature requires explicit identity and semantics.

Manifest identity:

```text
provider_id
provider_version
layer
context_id
max_staleness_seconds
manifest_hash
```

Feature identity:

```text
feature_id
feature_key
value_type = NUMBER | STRING | BOOLEAN
semantic_version
causality_policy = CONFIRMED_ONLY
required
missing_policy = FAIL_CLOSED | OPTIONAL_ABSENT
```

Examples:

```text
market.kospi_slope
market.regime_state
sector.relative_strength
group.follower_alignment
```

Semantic changes require a manifest/version identity change. Historical evidence must never be silently reinterpreted.

## 6. Discoverability without implementation knowledge

`ParentFeatureRegistry` is the discoverability seam for later generators and binders.

It maps a stable `feature_id` to manifest/spec metadata and rejects duplicate public identities. A future strategy generator can therefore learn that `market.kospi_slope` exists without seeing provider code or external API details.

Adding a new registered feature must not require a feature-specific Parser/Runtime function.

## 7. Cascading parent inheritance

Cascading calculation is explicit and causal:

```text
raw market/index data
 -> MARKET provider result
 -> SECTOR provider result + MARKET result hash
 -> GROUP provider result + parent result hashes
 -> ParentContextAssembler
 -> BattlefieldContext
```

Every dependency uses immutable provider `result_hash` evidence. The assembler rejects missing dependencies and any dependency whose `as_of` is later than the child provider result.

## 8. Missing / stale / future behavior

No context value may be guessed.

- future `as_of` -> fail closed;
- manifest staleness limit exceeded -> fail closed;
- missing required feature -> fail closed;
- undeclared feature -> fail closed;
- incompatible type -> fail closed;
- missing source -> fail closed;
- optional feature -> explicitly absent, never silently zero/false;
- missing dependency -> fail closed.

## 9. Context assembly

`ParentContextAssembler` consumes only already-computed `ParentFeatureProviderResult` objects.

Supported modes:

```text
OBSERVED
DEPLOYMENT
```

`NEUTRAL` with parent layers is prohibited.

The resulting `BattlefieldContext.metadata` carries provider result hashes, manifest hashes, knowledge cutoff and the policy:

```text
PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY
```

Thus provider/version provenance participates in context identity even if raw feature values happen to match.

## 10. Evidence before gate

The progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED parent context
 -> E8 context attribution
 -> separate Validation/OOS evidence
 -> explicit DEPLOYMENT policy evidence
 -> separately validated operational integration
```

Context correlation is not entry authority. Macro intelligence must remain an amplifier rather than life support for a weak micro tactic.

## 11. Interaction with Multi-Symbol Add-on

A future Multi-Symbol Add-on may implement a Parent Feature Provider for registered outputs such as sector breadth, leader strength, follower alignment or cross-sectional relative strength.

This does not grant Instrument DSL arbitrary peer-symbol reads. The DSL can eventually consume only registered immutable outputs.

Selection/ranking remains logically distinct from parent-context inheritance.

## 12. Backtest / live parity

Backtest:

```text
source data known by t
 -> provider calculation
 -> immutable provider result/context at t
 -> later tactic evaluation at t
```

Live:

```text
new confirmed source data
 -> provider calculation
 -> immutable current context
 -> next tactic evaluation
```

Provider operational deployment may differ, but feature semantics, version, cutoff, staleness and missing behavior must match.

## 13. Core DSL promotion boundary

Only a **generic read-only context reference mechanism** may later qualify for Core promotion.

Still outside Core:

- market/sector/group calculation logic;
- provider I/O;
- sector membership discovery;
- leader/follower detection;
- peer-symbol comparison/ranking;
- universe construction;
- portfolio allocation;
- adaptive/model inference producing context.

Before Core promotion, repeated need across tactic families, deterministic batch/stream parity, causal semantics, exact backtest/live semantics, regression coverage and permanent complexity justification are required.

## 14. Current implementation status

Implemented, awaiting trusted PCTX1 Full validation:

- versioned Feature Manifest;
- deterministic Feature Registry;
- typed immutable Provider Result;
- source/cutoff/staleness/missing validation;
- explicit cascading dependency hashes;
- deterministic `ParentContextAssembler`;
- provider/manifest provenance inside `BattlefieldContext` identity.

Already trusted from earlier phases:

- immutable `ContextLayerSnapshot` / `BattlefieldContext`;
- cutoff validation and context hashes;
- `NEUTRAL / OBSERVED / DEPLOYMENT` modes;
- E8 context attribution / deployment evidence.

Still not implemented:

- production Market/Sector/Group provider algorithms;
- causal intraday context timeline/frame abstraction;
- Runtime Context Binder;
- Instrument DSL `ctx.*` grammar/type binding;
- operational deployment entry-gate integration.

## 15. Immediate gate

Do not implement Core-facing `ctx.*` syntax/runtime behavior or wire deployment decisions into Broker authorization before PCTX1 receives trusted Full validation at an exact repository SHA.
