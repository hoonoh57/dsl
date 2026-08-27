# PCTX2B Causal Parent Context Frame / Read-Only Binder — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

PCTX1 Parent Feature Provider / Feature Manifest was operator-validated at exact DSL checkout:

```text
866bf0a5a25bf6759d1b264d62efcf9f1f277446
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore PCTX1 is trusted Full-green at that SHA.

## 2. Why PCTX2B precedes a concrete provider

PCTX1 defines one immutable parent-provider result and one assembled `BattlefieldContext` at a point in time. Intraday backtest/live parity requires a stronger contract:

```text
for each tactical decision timestamp t
 -> exactly which parent context was knowable at t?
```

Implementing a concrete KOSPI/Sector calculator before fixing that time-axis contract would risk coupling production provider logic to an insufficient one-snapshot-per-case abstraction.

PCTX2B therefore defines exact-time transport/consumption first. Concrete deterministic provider implementations remain PCTX2A work after this boundary is trusted.

## 3. New executable

```text
core/parent_context_frame.py
```

Schemas:

```text
parent_context_frame/v1
parent_context_binding/v1
```

Primary contracts:

```text
ParentContextPoint
ParentContextFrame
BoundParentFeature
ParentContextBinding
ParentContextBinder
```

## 4. Exact target-time frame

A `ParentContextFrame` represents immutable precomputed parent context for one target instrument.

```text
frame_id
target_symbol
mode = OBSERVED | DEPLOYMENT
registry_hash
manifest_hashes
points[]
metadata
frame_hash
```

Each `ParentContextPoint` contains one PCTX1 `ParentContextAssembly` and requires:

```text
point.target_time
 == assembly.knowledge_cutoff
 == assembly.context.as_of
```

This is deliberate. The orchestration layer must precompute the context intended for the exact tactic evaluation timestamp rather than asking the binder to guess which older snapshot should be reused.

## 5. No nearest-time / no hidden fill-forward

Resolution policy is fixed:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
```

`resolve_exact(t)` succeeds only when an exact frame point for `t` exists.

If a 09:30 and 09:35 context exist, a 09:32 request fails closed. The frame does not:

- choose the nearest point;
- automatically carry 09:30 forward;
- interpolate numeric features;
- substitute zero/false/default values;
- invoke a provider on demand.

A future performance optimization may compress repeated context internally, but externally observable semantics must remain equivalent to exact precomputed point resolution.

## 6. Stable manifest topology inside one frame

One frame has one semantic parent-feature topology.

Every point must carry the same sorted `manifest_hashes`. A provider or semantic version change inside the frame fails closed rather than silently changing the meaning of `market.*`, `sector.*` or `group.*` halfway through a backtest.

All frame manifests must exist in the declared PCTX1 `ParentFeatureRegistry`.

The frame records the exact `registry_hash`, so later binding with a different registry fails closed.

## 7. Deterministic frame identity

Caller assembly ordering does not define semantics. `ParentContextFrame.create(...)` normalizes points by exact target timestamp.

`frame_hash` includes:

```text
frame_id
target_symbol
mode
registry_hash
manifest_hashes
ordered target points
assembly hashes
context hashes
metadata
```

Changing a provider/version/result/context at any timestamp therefore changes frame identity.

## 8. Generic read-only binder

`ParentContextBinder` is a sidecar contract, not a Core DSL Runtime feature.

Input:

```text
frozen ParentContextFrame
matching ParentFeatureRegistry
exact target_time
explicit feature_ids[]
```

Output:

```text
ParentContextBinding
  target_time
  target_symbol
  frame_hash
  registry_hash
  context_hash
  BoundParentFeature[]
  binding_hash
```

Binding policy:

```text
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

The binder resolves each stable `feature_id` through the registry to:

```text
manifest
layer
context_id
feature_key
value_type
semantic_version
required/missing policy
```

It then reads that value from the already-frozen exact-time `BattlefieldContext`.

The binder does not know how the value was calculated.

## 9. Optional absence remains explicit

For a required feature, absence fails closed.

For a feature declared:

```text
required = false
missing_policy = OPTIONAL_ABSENT
```

binding returns explicit evidence:

```text
present = false
value = null
```

This is not a numeric/boolean default and must not be treated as zero or false by a future DSL binding.

## 10. Type safety

The binder re-checks the declared public value type at the consumption boundary:

```text
NUMBER
STRING
BOOLEAN
```

This provides a second fail-closed boundary between provider evidence and any future Core-facing reference mechanism.

## 11. What remains outside PCTX2B

PCTX2B does not implement:

- production KOSPI/KOSDAQ regime calculation;
- production Sector/Group/Leader-Follower calculation;
- source/database acquisition for parent features;
- Instrument DSL `ctx.*` grammar;
- Parser/Semantic support for parent references;
- Runtime Context Binder integration;
- Backtest entry-gate integration;
- Broker authority;
- multi-symbol universe/ranking/allocation;
- automatic fill-forward or resampling policy.

The current `ParentContextBinder` is intentionally an external deterministic consumer contract that can be validated before any Core promotion.

## 12. Regression coverage

```text
test_stage1_parent_context_frame.py
```

Coverage includes:

- frame identity independent of input assembly ordering;
- strict chronological exact target points;
- exact target-time resolution;
- explicit rejection of nearest/fill-forward lookup;
- exact `target_time == knowledge_cutoff == context.as_of` requirement;
- provider/manifest version drift rejected inside a frame;
- registered typed feature binding;
- optional absence preserved as `present=false` / null evidence;
- binding identity independent of requested feature ordering;
- unknown feature fail-close;
- registry mismatch fail-close;
- missing exact target point fail-close.

The Tactical P1 Full verifier discovers the regression through `test_stage1_*.py`.

## 13. Mutation boundary

PCTX2B changes none of:

```text
Parser
Semantic
Runtime
TA/indicator authority
Backtest
BrokerEmulator
BattleCase provider
E3-E8 evidence/adjudication
PCTX1 provider semantics
Chart SSOT
```

It adds causal context transport and generic read-only sidecar binding only.

## 14. Next boundary

Do not implement a production concrete parent provider, Core-facing `ctx.*` grammar/runtime binding, or operational deployment gate before this exact PCTX2B boundary receives trusted Full validation.

If PCTX2B becomes trusted, the next preferred tranche is:

```text
PCTX2A — one concrete deterministic Market Parent Feature Provider
```

That provider should publish through PCTX1 and populate PCTX2B exact-time frames without changing their contracts.
