# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1-PCTX2D TRUSTED / MSA3 GROUP PUBLICATION ACTIVE / 2026-08-27 KST**

## Governing rule

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, and consumed inside DSL only through a narrow registered read-only binding contract.**

Instrument DSL remains deterministic and single-instrument. It may know stable registered `feature_id` values; it must not know provider algorithms, perform provider I/O, discover peers/universes or rank symbols.

## Trusted chain

```text
PCTX1 typed/versioned Parent Feature Provider contract
 -> PCTX2B exact ParentContextFrame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 exact Backtest binding
 -> existing execution policy
 -> BrokerEmulator
```

Trusted exact checkpoints include:

```text
PCTX1  866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
PCTX2C  7aee063932e0d70d38c2e7f876b140d049029771
PCTX2D  6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
```

Every listed executable checkpoint received Tactical P1 Full PASS at the exact SHA.

## PCTX1 typed contract

`ParentFeatureSpec`, `ParentFeatureManifest`, `ParentFeatureRegistry`, `ParentFeatureProviderResult`, `ParentContextAssembly` and `ParentContextAssembler` define immutable typed evidence.

Required behavior is fail-closed for future/stale data, missing required values, undeclared values, incompatible types, missing source authority and invalid dependency hashes. Optional values are explicitly absent rather than silently defaulted.

Provider/feature semantic changes require versioned identity changes.

## Exact frame / binding policy

Frame points require:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
```

Resolution/binding remains exact:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

No Parser/Semantic/Runtime/Backtest/Broker path calls a provider. Supplying context does not itself authorize an entry.

## Trusted MARKET / SECTOR provider path

```text
explicit benchmark source
 -> PCTX2A deterministic MARKET result
 -> PCTX2C exact root precomputation
 -> PCTX2D explicit dependency DAG
 -> descriptive SECTOR result
```

PCTX2D requires explicit provider dependencies, deterministic topological order, exact-time child/parent results and equality between declared parent result hashes and each child `dependency_result_hashes`.

Trusted PCTX2D checkpoint:

```text
6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
Ran 6 tests in 0.174s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MARKET and SECTOR features remain descriptive; they do not perform universe discovery, peer ranking, selection, allocation or Broker actions.

## Multi-symbol evidence before GROUP publication

Cross-symbol/group intelligence belongs to the optional Add-on sidecar.

Trusted sequence:

```text
MSA1 immutable per-symbol exact snapshots
 -> MSA2 bounded exact chronological group evidence
```

MSA2 is trusted at:

```text
3a5a2ece658ead28a1822ef7482a3d284d12e2d6
Ran 7 tests in 0.017s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA1/MSA2 remain `OBSERVATION_ONLY` with `operational_authority=false`.

## MSA3 registered GROUP publication — active validation tranche

MSA3 is the allowed bridge from already-computed Add-on evidence into PCTX1/PCTX2D.

```text
exact immutable MSA2 result @ t
 + exact SECTOR ParentFeatureProviderResult @ t
 -> registered GROUP ParentFeatureProviderResult
 -> PCTX1 assembly
 -> PCTX2D OBSERVED frame
 -> generic read-only binder
```

Module:

```text
core/group_evidence_parent_feature_provider.py
```

Publication policy:

```text
EXACT_PRECOMPUTED_MSA2_EVIDENCE_PLUS_EXPLICIT_SECTOR_DEPENDENCY_NO_PEER_RUNTIME_READ_NO_DEPLOYMENT_AUTHORITY
publication_state = RESEARCH_ONLY
operational_authority = false
```

The evidence timeline accepts only exact `multi_symbol_group_evidence/v1` payloads, verifies their `result_hash`, and forbids nearest-time/fill-forward substitution.

The first bounded GROUP manifest publishes only aggregate numeric context:

```text
group.<namespace>_comparison_eligible_rate
group.<namespace>_favorable_breadth_rate
group.<namespace>_leader_persistence_rate
group.<namespace>_leader_follower_spread       optional
group.<namespace>_follower_favorable_rate      optional
```

It does not publish peer symbol identities, rank lists, allowed/blocked symbols, allocation, entry-gate fields or Broker instructions.

Follower-dependent aggregates remain `OPTIONAL_ABSENT` when no follower evidence exists.

The GROUP result must depend on exactly one configured SECTOR result at the same exact timestamp and carry that SECTOR `result_hash` in `dependency_result_hashes`.

## Research publication is not deployment authority

Required progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED parent context
 -> E8 attribution
 -> Validation/OOS evidence
 -> explicit DEPLOYMENT policy evidence
 -> separately validated operational integration
```

MSA3 regression intentionally stops at an OBSERVED PCTX2D frame and read-only binder. A registered GROUP feature does not become CTXBT1/Backtest deployment input merely because publication is technically possible.

Macro/group context must amplify a valid micro tactic rather than become life support for one.

## Prohibited boundaries

Instrument DSL must not directly implement:

```text
provider/network/database calls
universe discovery
peer-symbol reads
cross-sectional ranking
leader/follower selection
portfolio allocation
arbitrary dynamic context discovery
```

Cross-symbol conclusions must remain Add-on evidence or bounded registered parent features.

## Current nonclaims

Do not claim yet:

- trusted Full PASS for MSA3;
- validated GROUP-feature OOS benefit;
- GROUP feature DEPLOYMENT eligibility;
- automatic macro/group entry authority;
- cross-symbol allocation deployment;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate gate

Validate MSA3 focused regression and Tactical P1 Full at one exact checkout before any GROUP DEPLOYMENT use or operational selection work. Any failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
