# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1-PCTX2D + MSA3 TRUSTED / CTXVAL1 ACTIVE / 2026-08-27 KST**

## Governing rule

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, consumed only through registered read-only binding, and validated out-of-sample before deployment authority is considered.**

Instrument DSL remains deterministic and single-instrument. It may know stable registered `feature_id` values; it must not know provider algorithms, perform provider I/O, discover peers/universes, rank symbols or allocate capital.

## Trusted execution/binding chain

```text
PCTX1 typed/versioned Parent Feature Provider contract
 -> PCTX2B exact ParentContextFrame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 exact Backtest binding
 -> existing execution policy
 -> BrokerEmulator
```

Trusted exact checkpoints:

```text
PCTX1  866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
PCTX2C  7aee063932e0d70d38c2e7f876b140d049029771
PCTX2D  6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
```

Every listed executable checkpoint received Tactical P1 Full PASS at that exact SHA.

## PCTX1 typed evidence contract

`ParentFeatureSpec`, `ParentFeatureManifest`, `ParentFeatureRegistry`, `ParentFeatureProviderResult`, `ParentContextAssembly` and `ParentContextAssembler` define immutable typed evidence.

Future/stale data, missing required values, undeclared values, incompatible types, missing source authority and invalid dependency hashes fail closed. Optional values remain explicitly absent rather than silently defaulted. Provider/feature semantic changes require versioned identity changes.

## Exact context transport

Frame and binder resolution remain exact:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

No Parser/Semantic/Runtime/Backtest/Broker path calls a provider. Supplying a context does not itself authorize entry.

## Trusted parent calculation/publication path

```text
PCTX2A deterministic MARKET provider
 -> PCTX2C exact root precomputation
 -> PCTX2D explicit dependency DAG
 -> descriptive SECTOR provider
 -> MSA3 registered aggregate GROUP publication
```

PCTX2D enforces explicit provider dependencies, deterministic topological order and exact parent `result_hash` evidence.

MSA3 is trusted at:

```text
02904728cb0a39669e6809ba21c4e2dd8eb947e3
Ran 7 tests in 0.078s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA3 publishes only bounded aggregate GROUP values:

```text
group.<namespace>_comparison_eligible_rate
group.<namespace>_favorable_breadth_rate
group.<namespace>_leader_persistence_rate
group.<namespace>_leader_follower_spread       optional
group.<namespace>_follower_favorable_rate      optional
```

Publication remains `RESEARCH_ONLY` and `operational_authority=false`. Peer symbol identities, rank lists, allowed/blocked symbols, allocation, entry-gate fields and Broker instructions are not published.

## CTXVAL1 registered context validation — active gate

Technical publication is not deployment evidence. CTXVAL1 introduces the required registered-context holdout gate:

```text
trusted NEUTRAL tactical profile
 + exact PCTX1 OBSERVED context per case
 + registered feature_id + required manifest_hash
 + E8 ContextSliceRule
 -> TRAIN attribution
 -> VALIDATION attribution
 -> OOS attribution
 -> HARSH attribution
 -> slice-specific validation_evidence_hash
```

Module:

```text
core/tactical_context_validation.py
```

Policies:

```text
PARTITIONED_E8_ATTRIBUTION_TRAIN_VALIDATION_OOS_HARSH_DECLARED_AXES_NO_HIDDEN_SCORE
EXACT_REGISTERED_PCTX1_OBSERVED_CONTEXT_ONLY
```

Every case context must be exact to its neutral-profile knowledge cutoff and carry the PCTX1 assembly contract, provider result hashes and provider manifest hashes. A `RegisteredContextSlice` additionally pins the E8 rule to one public `feature_id` and exact manifest hash.

CTXVAL1 requires exactly one TRAIN, VALIDATION and OOS partition and at least one HARSH partition with `adverse_reason`. Case IDs are globally disjoint and the same tactic candidate is evaluated across all partitions.

The validation contract exposes independent retained-case, return, drawdown, profitable-rate, cost and MFE-giveback tolerances. There is no hidden universal score. TRAIN may require material improvement; Validation/OOS/HARSH must survive declared regression limits.

A passing slice may produce:

```text
evidence_status = VALIDATED
validation_evidence_hash = <slice-specific hash>
deployment_policy_evidence_eligible = true
```

but CTXVAL1 itself remains:

```text
operational_authority = false
execution_integration = EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

## Required progression before operational authority

```text
NEUTRAL micro baseline
 -> OBSERVED registered parent context
 -> E8 attribution
 -> CTXVAL1 TRAIN / VALIDATION / OOS / HARSH evidence
 -> separately declared E8 DEPLOYMENT policy evidence
 -> separately validated operational integration
```

A context slice must never become life support for a weak micro tactic. Parent allow is permission only, never forced entry.

## Prohibited boundaries

Instrument DSL must not directly implement provider/network/database calls, universe discovery, peer-symbol reads, cross-sectional ranking, leader/follower selection, portfolio allocation or arbitrary dynamic context discovery.

Cross-symbol conclusions remain Add-on evidence or bounded registered parent features.

## Current nonclaims

Do not claim yet:

- trusted Full PASS for CTXVAL1;
- empirical OOS benefit from real GROUP context;
- production GROUP deployment eligibility;
- automatic macro/group entry authority;
- cross-symbol allocation deployment;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate gate

Validate `test_stage1_tactical_context_validation.py` and Tactical P1 Full at one exact CTXVAL1 checkout before any GROUP DEPLOYMENT use or operational selection work. Any failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
