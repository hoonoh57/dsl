# CTXDEP1 Validated Context Deployment Policy Evidence — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / NON-OPERATIONAL / 2026-08-28 KST**

## Trusted predecessor

CTXVAL1 received operator validation at exact checkout:

```text
db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
Ran 7 tests in 0.073s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the registered parent-context Validation/OOS/Harsh evidence gate is trusted Full-green at that SHA.

## Purpose

CTXDEP1 converts one independently validated CTXVAL1 context condition into explicit E8 deployment-policy **evidence** without connecting it to live execution.

```text
CTXVAL1 PASS slice
 + exact validation arena identity
 + exact registered feature/manifest identity
 + TRAIN/VALIDATION/OOS/HARSH attribution evidence
 -> validated E8 ContextDeploymentPolicy evidence
```

This closes the gap where a caller could otherwise copy an arbitrary `validation_evidence_hash` into a policy without proving that the policy rule, tactic and validation evidence belong together.

## Executable

```text
core/tactical_context_deployment_evidence.py
test_stage1_tactical_context_deployment_evidence.py
```

Schema/policies:

```text
validated_context_deployment_policy_evidence/v1
CTXVAL1_VALIDATED_SLICE_TO_E8_DEPLOYMENT_POLICY_EVIDENCE_NO_ENTRY_GATE_NO_BROKER_AUTHORITY
POLICY_EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

## Promotion rules

CTXDEP1 accepts only a valid CTXVAL1 arena with:

- the trusted CTXVAL1 schema/policies;
- `operational_authority=false`;
- intact `arena_hash` over the validation payload;
- complete TRAIN / VALIDATION / OOS / HARSH evidence;
- internally consistent validated/rejected slice lists and arena status.

The requested slice must independently be:

```text
status = PASS
evidence_status = VALIDATED
deployment_policy_evidence_eligible = true
operational_authority = false
```

Its feature ID, manifest hash, rule and validation evidence hash are carried into the resulting policy evidence.

Every selected partition's role and attribution hash must match the top-level CTXVAL1 arena record. Failed or incomplete holdout evidence cannot be promoted.

## Resulting policy evidence

CTXDEP1 creates the existing E8 `ContextDeploymentPolicy` with:

```text
tactic_id = validated CTXVAL1 candidate_hash
rule = exact validated slice rule
attribution_hash = exact TRAIN attribution hash
evidence_status = VALIDATED
validation_evidence_hash = exact CTXVAL1 slice hash
```

The wrapper additionally retains:

```text
feature_id
required_manifest_hash
validation_arena_hash
validation_contract_hash
all partition attribution hashes
policy_hash
evidence_hash
```

## No operational authority

The resulting bundle always remains:

```text
policy_evidence_validated = true
operational_authority = false
execution_integration = POLICY_EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

CTXDEP1 does not call or modify:

```text
DSLRuntime
BacktestEngine
BrokerEmulator
ParentFeatureProvider calculation
entry_gate
symbol selection/allocation
```

A validated policy document is not yet an operational gate.

## Regression coverage

The focused regression covers:

- PASS slice promotion into deterministic E8 policy evidence;
- exact tactic/rule/manifest/validation identity preservation;
- OOS-failing slice promotion rejection;
- tampered CTXVAL1 arena evidence rejection;
- unknown slice and invalid priority fail-close;
- deterministic policy/evidence identity;
- absence of execution/provider/selection wiring.

The Tactical P1 Full verifier discovers the new `test_stage1_*.py` regression automatically.

## Mutation boundary

CTXDEP1 adds only a policy-evidence sidecar, focused regression and checkpoint/status documentation. It does not change Parser, Semantic, Runtime, Backtest, Broker, PCTX provider semantics, MSA analysis/publication, CTXVAL1 adjudication or existing E8 decision semantics.

## Nonclaims

Do not claim yet:

- trusted Full PASS for CTXDEP1;
- empirical profitability of a real GROUP deployment rule;
- operational parent-context entry gate;
- cross-symbol allocation authority;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_deployment_evidence.py
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
