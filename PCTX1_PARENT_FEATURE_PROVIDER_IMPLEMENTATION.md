# PCTX1 Parent Feature Provider / Feature Manifest — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

E8 Macro Context Attribution / Deployment Evidence was operator-validated at exact DSL checkout:

```text
3256f1de6b9bb7e8b79342ea037edcd51125bcda
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E8 is trusted Full-green at that SHA.

## 2. Why PCTX1 is next

E8 can consume an exact:

```text
case_id -> BattlefieldContext
```

mapping, but until PCTX1 there was no generic executable contract describing how a parent-layer calculator publishes stable feature identities, provider/version provenance, causal cutoff, dependencies, staleness and typed values.

PCTX1 closes that production seam without changing Instrument DSL syntax or execution.

The flow is:

```text
source adapter / provider-specific calculator
        ↓
ParentFeatureManifest
        ↓
ParentFeatureProviderResult
        ↓
ParentContextAssembler
        ↓
immutable BattlefieldContext
        ↓
E8 attribution / future read-only binder
```

The DSL still does not call the provider.

## 3. New executable

```text
core/parent_feature_provider.py
```

Schemas:

```text
parent_feature_provider/v1
parent_feature_registry/v1
parent_context_assembly/v1
```

Primary contracts:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider (Protocol)
ParentContextAssembly
ParentContextAssembler
```

## 4. Feature manifest

A feature is public only when declared by a versioned manifest.

A manifest declares:

```text
provider_id
provider_version
layer
context_id
features[]
max_staleness_seconds
metadata
manifest_hash
```

Each `ParentFeatureSpec` declares:

```text
feature_id
feature_key
value_type = NUMBER | STRING | BOOLEAN
semantic_version
causality_policy = CONFIRMED_ONLY
required
missing_policy = FAIL_CLOSED | OPTIONAL_ABSENT
metadata
```

Feature IDs are namespaced by layer, for example:

```text
market.kospi_slope
market.regime_state
sector.relative_strength
group.follower_alignment
```

Adding a feature does not add a new Parser/Runtime function. It changes the manifest, not the DSL grammar.

## 5. Registry / discoverability

`ParentFeatureRegistry` provides deterministic discovery for later generators/binders.

It rejects:

- duplicate provider/version identities;
- duplicate public `feature_id` across manifests;
- unknown feature lookup.

`registry_hash` is independent of manifest input ordering.

This is the future seam through which an LLM or DSL binder may learn that a feature exists without knowing the provider algorithm.

## 6. Provider calculation seam

`ParentFeatureProvider` is a Protocol only:

```text
manifest
build(as_of, knowledge_cutoff, dependencies) -> ParentFeatureProviderResult
```

PCTX1 does not prescribe whether a concrete provider is in-process, reads a local snapshot, calls a source adapter before calculation, or is backed by a separate service.

The critical invariant is that by the time the result reaches the assembler it is already computed and immutable.

Instrument DSL execution never invokes this protocol.

## 7. Provider result contract

A `ParentFeatureProviderResult` records:

```text
manifest
as_of
knowledge_cutoff
source
features
dependency_result_hashes
metadata
snapshot_hash
result_hash
```

It fails closed when:

- `as_of > knowledge_cutoff`;
- manifest staleness limit is exceeded;
- a required feature is missing;
- an undeclared feature appears;
- a typed value is incompatible;
- a dependency hash is empty/duplicated;
- source authority is missing.

Optional features remain absent when unavailable. They are never converted silently to zero/false.

The provider result materializes a normal immutable `ContextLayerSnapshot` only after these checks pass.

## 8. Cascading parent dependencies

Provider results may reference other result hashes explicitly:

```text
MARKET result
   ↓ dependency hash
SECTOR result
   ↓ dependency hash
GROUP result
```

`ParentContextAssembler` requires every declared dependency to exist in the same assembly and rejects a dependency whose `as_of` is later than its child result.

This gives the parent cascade explicit immutable lineage without letting a child provider read a later revision.

## 9. Context assembly

`ParentContextAssembler` accepts only precomputed `ParentFeatureProviderResult` objects.

Supported modes:

```text
OBSERVED
DEPLOYMENT
```

`NEUTRAL` with parent results is rejected.

Every result must use the exact assembly `knowledge_cutoff`; every result `as_of` must be no later than the context `as_of`.

The assembler sorts provider results deterministically and emits a `BattlefieldContext` whose metadata contains:

```text
parent_feature_contract
parent_feature_result_hashes
parent_feature_manifest_hashes
parent_feature_knowledge_cutoff
assembly_policy = PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY
```

Because manifest/result hashes are embedded in context metadata, provider or semantic version changes change the resulting `context_hash` even when numeric feature values happen to be identical.

## 10. What PCTX1 does not implement

PCTX1 deliberately does not add:

- a production KOSPI/KOSDAQ regime calculator;
- a production sector membership source;
- leader/follower discovery;
- multi-symbol ranking;
- DSL `ctx.*` grammar;
- Runtime Context Binder;
- on-demand DB/network calls from DSL;
- entry-gate wiring;
- Broker authority;
- automatic context-policy selection.

Existing provider modules such as High-Beta/cohort providers are not silently reclassified as parent-feature providers. A future explicit adapter/implementation must declare a manifest and satisfy this contract.

## 11. Regression coverage

```text
test_stage1_parent_feature_provider.py
```

Coverage includes:

- typed manifest and deterministic registry;
- feature discoverability by stable `feature_id`;
- future/stale result fail-close;
- required/unknown/type mismatch fail-close;
- explicit optional absence without defaulting;
- deterministic cascading assembly independent of caller ordering;
- provenance hashes embedded into `BattlefieldContext`;
- missing/future dependency fail-close;
- provider version changing context identity;
- rejection of NEUTRAL assembly with parent features.

The Tactical P1 Full verifier discovers this regression through `test_stage1_*.py`.

## 12. Mutation boundary

PCTX1 adds no changes to:

```text
Parser
Semantic
Runtime
TA/indicator authority
Backtest
BrokerEmulator
BattleCase provider
E3-E8 adjudication/evidence semantics
Chart SSOT
```

It is parent-context production infrastructure only.

## 13. Next boundary

Do not implement the Core-facing DSL `ctx.*` binding or operational deployment gate before this exact PCTX1 boundary receives trusted Full validation.

If PCTX1 becomes trusted, the next design decision is intentionally split:

```text
PCTX2A concrete deterministic Parent Feature Provider(s)
PCTX2B causal context timeline/frame + read-only binder contract
```

Only after repeated tactic-family need and promotion criteria are proven should a generic read-only context reference be promoted into Core DSL grammar/runtime.
