# CTXVAL1 Registered Parent Context Validation Arena — Implementation Checkpoint

Status: **IMPLEMENTED / INITIAL TEST DEFECT FIXED / AWAITING LOCAL REVALIDATION / EVIDENCE_ONLY / 2026-08-28 KST**

## Trusted predecessor

MSA3 received operator validation at exact checkout:

```text
02904728cb0a39669e6809ba21c4e2dd8eb947e3
Ran 7 tests in 0.078s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore registered research-only GROUP parent-feature publication is trusted Full-green at that SHA.

## Objective

CTXVAL1 fills the missing evidence gate between registered parent-context publication and any future deployment policy.

```text
trusted NEUTRAL micro profile
 + exact registered PCTX1 OBSERVED context per case
 + explicit E8 ContextSliceRule
 + TRAIN / VALIDATION / OOS / HARSH partitions
        ↓
partitioned E8 attribution
        ↓
declared no-score survival / improvement contract
        ↓
per-slice validation_evidence_hash
```

CTXVAL1 does not rerun tactics, call providers, create a DeploymentDecision, install an entry gate or call BrokerEmulator.

## Executable

New module:

```text
core/tactical_context_validation.py
```

New regression:

```text
test_stage1_tactical_context_validation.py
```

Schemas/policies:

```text
tactical_context_validation_arena/v1
tactical_context_validation_contract/v1
registered_context_validation_slice/v1
PARTITIONED_E8_ATTRIBUTION_TRAIN_VALIDATION_OOS_HARSH_DECLARED_AXES_NO_HIDDEN_SCORE
EXACT_REGISTERED_PCTX1_OBSERVED_CONTEXT_ONLY
```

Execution integration remains:

```text
EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

## Registered slice identity

`RegisteredContextSlice` binds one E8 `ContextSliceRule` to:

```text
feature_id
required_manifest_hash
rule
```

The feature ID must match the rule layer namespace. Every case context in every partition must carry the required manifest hash inside its PCTX1 assembly metadata.

This prevents an unregistered or semantically different context value from borrowing validation evidence from another provider version.

## Exact PCTX1 context requirement

Every case context must satisfy:

```text
mode == OBSERVED
context.as_of == case.knowledge_cutoff
context.metadata.parent_feature_contract == parent_context_assembly/v1
context.metadata.parent_feature_knowledge_cutoff == case.knowledge_cutoff
non-empty unique provider result hashes
non-empty unique provider manifest hashes
required registered manifest hash present
```

No nearest-time lookup, stale substitution, fill-forward or direct provider call is performed.

## Partition authority

CTXVAL1 requires exactly:

```text
1 TRAIN
1 VALIDATION
1 OOS
>= 1 HARSH
```

HARSH partitions require explicit `adverse_reason`. Case IDs are globally disjoint across partitions and every partition must evaluate the same candidate hash.

Each partition is itself a frozen `tactical_discovery/v1` NEUTRAL profile plus exact OBSERVED contexts. CTXVAL1 delegates slice attribution to the trusted E8 `TacticalContextAttributor`; historical micro results remain read-only.

## Declared validation contract

`ContextSliceValidationContract` exposes explicit tolerances rather than a hidden universal score:

```text
min_retained_case_rate
min_retained_active_case_rate
max_average_return_regression_pct
max_median_return_regression_pct
max_profitable_rate_regression
max_worst_case_regression_pct
max_worst_mdd_regression_pct
max_cost_per_case_regression
max_mfe_giveback_regression_pct
require_train_material_improvement
min_material_improvement
```

Positive-return / survival axes may not regress beyond the declared tolerance. Cost and MFE-giveback may not increase beyond their declared tolerance. TRAIN can require at least one material improvement; holdouts primarily enforce survival unless a future authority explicitly tightens the contract.

No weighted aggregate score is computed.

## Per-slice evidence

Every registered slice is judged independently across all partitions.

A passing slice receives:

```text
status = PASS
evidence_status = VALIDATED
deployment_policy_evidence_eligible = true
validation_evidence_hash = <slice-specific hash>
operational_authority = false
```

A failing slice receives its own rejected evidence and cannot inherit another slice's hash.

Top-level arena status may be `PASS`, `MIXED` or `FAIL`, while `validated_slice_ids` and `rejected_slice_ids` preserve independent-slice semantics.

A passing `validation_evidence_hash` may later satisfy the existing E8 `ContextDeploymentPolicy` evidence field, but CTXVAL1 does not instantiate or execute that policy.

## GROUP context usage

The focused regression validates an MSA3-style registered GROUP feature:

```text
group.semiconductor_favorable_breadth_rate
```

through explicit TRAIN / VALIDATION / OOS / HARSH neutral profiles. It also verifies that a TRAIN-positive rule is rejected when the OOS slice regresses.

This is a contract test. It is not empirical evidence that the real semiconductor GROUP feature improves profitability.

## Regression coverage

The focused regression covers:

- registered GROUP slice PASS across TRAIN/VALIDATION/OOS/HARSH;
- slice-specific validation evidence identity;
- E8 validated-policy evidence compatibility without execution wiring;
- OOS regression rejection despite positive TRAIN evidence;
- required HARSH adverse reason and role completeness;
- exact registered PCTX1 OBSERVED context enforcement;
- manifest mismatch rejection;
- same-candidate and globally disjoint case requirements;
- deterministic identity under partition/context input reordering;
- explicit validation contract identity;
- no Backtest/Broker/Runtime/provider/entry-gate calls in the validation module.

The Tactical P1 Full verifier discovers the regression through `test_stage1_*.py`.

## Mutation boundary

CTXVAL1 adds only:

```text
core/tactical_context_validation.py
test_stage1_tactical_context_validation.py
CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_ARENA_IMPLEMENTATION.md
```

plus authority/checkpoint documentation updates.

It does not modify:

```text
Parser / Semantic / Runtime
BacktestEngine
BrokerEmulator
PCTX provider/orchestration semantics
MSA1 / MSA2 analysis semantics
MSA3 GROUP publication semantics
E8 attribution semantics
entry_gate
Chart SSOT
```

## Initial local validation incident

The first local CTXVAL1 validation ran at exact checkout:

```text
d2abaeedc4d464c1c3d27417980d93d202902b72
```

Result:

```text
Ran 7 tests in 0.068s
FAILED (failures=1)
[FAIL] Tactical P1 Full boundary failed from the same regression
```

The first failure was classified exactly as:

```text
test defect
```

The intended regression expected the CTXVAL1-specific error `exact context.as_of`, but its fixture changed only the `BattlefieldContext.as_of` to `20260801092959` while retaining the GROUP layer at `20260801093000`. The trusted lower-level `BattlefieldContext` causality guard correctly rejected that malformed envelope first because a layer was later than its envelope.

Correction:

- no product module changed;
- no validation tolerance or authority contract changed;
- the regression now verifies the malformed envelope guard separately;
- the exact-time fixture also moves the layer to `20260801092959`, allowing base causality validation to pass so CTXVAL1's stronger `context.as_of == case.knowledge_cutoff` guard is tested directly.

The test-only correction was committed as:

```text
f09b7fee673940f96c0f176cd048089161154d9a
```

A new focused + Full local validation at the final post-documentation checkout is required before CTXVAL1 becomes trusted.

## Nonclaims

Do not claim yet:

- trusted Full PASS for CTXVAL1;
- empirical OOS benefit from real GROUP context;
- validated production GROUP deployment policy;
- automatic symbol selection or allocation;
- operational parent-context gate;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_validation.py
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