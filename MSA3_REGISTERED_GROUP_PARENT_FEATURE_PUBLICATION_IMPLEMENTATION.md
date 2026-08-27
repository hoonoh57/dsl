# MSA3 Registered GROUP Parent Feature Publication — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / RESEARCH_ONLY / 2026-08-27 KST**

## Trusted predecessor

MSA2 received operator validation at exact checkout:

```text
3a5a2ece658ead28a1822ef7482a3d284d12e2d6
Ran 7 tests in 0.017s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore bounded static-universe leader/follower/breadth observation evidence is trusted Full-green at that SHA.

## Objective

MSA3 publishes only a narrow aggregate subset of already-computed MSA2 evidence through the existing PCTX1/PCTX2D registered parent-feature seam.

```text
trusted MSA2 observation evidence @ exact t
 + exact immutable evidence timeline
 + explicit SECTOR parent result @ exact t
 -> research-only GROUP ParentFeatureProviderResult
 -> PCTX1 assembly
 -> PCTX2D OBSERVED frame
 -> registered read-only binder evidence
```

MSA3 does not run cross-symbol analysis itself and does not create deployment authority.

## Executable

New module:

```text
core/group_evidence_parent_feature_provider.py
```

Primary contracts:

```text
ImmutableGroupEvidenceTimeline
GroupEvidenceParentFeatureProvider
```

Provider calculation policy:

```text
EXACT_PRECOMPUTED_MSA2_EVIDENCE_PLUS_EXPLICIT_SECTOR_DEPENDENCY_NO_PEER_RUNTIME_READ_NO_DEPLOYMENT_AUTHORITY
```

Publication state:

```text
RESEARCH_ONLY
operational_authority = false
```

## Exact immutable evidence timeline

`ImmutableGroupEvidenceTimeline` accepts only valid `multi_symbol_group_evidence/v1` results with:

```text
mode = OBSERVATION_ONLY
operational_authority = false
latest.as_of == end_as_of
strictly increasing unique end_as_of values
```

It reconstructs the MSA2 result identity and requires the supplied `result_hash` to match the payload. Modified/tampered evidence therefore fails closed.

Resolution is exact only:

```text
EXACT_PRECOMPUTED_MSA2_EVIDENCE_NO_NEAREST_NO_FILL_FORWARD
```

No nearest-time substitution, interpolation or fill-forward is allowed.

## Registered GROUP feature set

For namespace `semiconductor`, MSA3 publishes only:

```text
group.semiconductor_comparison_eligible_rate
group.semiconductor_favorable_breadth_rate
group.semiconductor_leader_persistence_rate
group.semiconductor_leader_follower_spread       optional
group.semiconductor_follower_favorable_rate      optional
```

The first three are required finite NUMBER values. The last two are `OPTIONAL_ABSENT`; when follower evidence collapses, they are omitted rather than replaced with zero.

`leader_persistence_rate` is the mean persistence rate of the current observed leaders over the declared MSA2 bounded lookback.

MSA3 deliberately does **not** publish:

```text
leader symbol identities
follower symbol identities
allowed/blocked symbols
rank position
max slots
allocation
entry gate
DeploymentDecision
Broker order
```

Instrument DSL therefore receives only registered aggregate GROUP context, never arbitrary peer-symbol runtime state.

## Explicit SECTOR dependency

The provider requires exactly one configured SECTOR `ParentFeatureProviderResult` at the same exact timestamp.

The GROUP result records:

```text
dependency_result_hashes = (exact SECTOR result_hash,)
msa2_result_hash
msa2_policy_hash
msa2_point_hashes
timeline_hash
```

The dependency manifest must have layer `SECTOR`; extra or wrong dependencies fail closed.

This preserves the causal parent chain:

```text
MARKET -> SECTOR -> GROUP
```

while MSA2 peer analysis itself remains outside Instrument DSL and outside PCTX provider execution.

## Research-only integration boundary

MSA3 regression wires the provider through PCTX2D in `OBSERVED` mode and resolves the registered GROUP values through the generic PCTX2B binder.

It intentionally does **not** run CTXBT1/Backtest with the new GROUP features in this tranche.

Reason:

```text
registered context publication
!=
deployment validation
```

The authority order still requires causal attribution and Validation/OOS evidence before any GROUP feature is eligible for DEPLOYMENT use.

## Regression

New regression:

```text
test_stage1_group_evidence_parent_feature_provider.py
```

Coverage includes:

- five-feature descriptive manifest and no peer identity publication;
- exact MSA2 result-hash validation;
- exact-time lookup with no nearest/fill-forward;
- explicit MSA2 policy/universe/source/metric pinning;
- exact SECTOR dependency and result-hash evidence;
- optional follower aggregates preserved as absent rather than zero;
- PCTX2D MARKET -> SECTOR -> GROUP OBSERVED DAG publication;
- generic registered binder resolution;
- no MSA2 analyzer execution, DSLRuntime, BacktestEngine or BrokerEmulator calls in the provider module.

The Tactical P1 Full verifier discovers the regression through `test_stage1_*.py`.

## Mutation boundary

MSA3 adds only the GROUP publication adapter, focused regression and authority/checkpoint documentation.

It does not modify:

```text
Parser / Semantic / Runtime
BacktestEngine
BrokerEmulator
core/multi_symbol.py
MSA1/MSA2 analysis semantics
PCTX1/PCTX2B/PCTX2D core orchestration semantics
CTXDSL1 / CTXBT1
entry_gate
Chart SSOT
```

## Nonclaims

Do not claim yet:

- trusted Full PASS for MSA3;
- validated OOS benefit from GROUP features;
- GROUP feature DEPLOYMENT eligibility;
- automatic symbol selection or permission;
- portfolio allocation authority;
- operational macro gate;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_group_evidence_parent_feature_provider.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
