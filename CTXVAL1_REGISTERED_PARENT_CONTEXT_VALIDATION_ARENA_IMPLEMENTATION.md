# CTXVAL1 Registered Parent Context Validation Arena — Implementation Checkpoint

Status: **TRUSTED FULL PASS / EVIDENCE_ONLY / 2026-08-28 KST**

## Trusted checkpoint

Operator validation at exact checkout:

```text
db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
Ran 7 tests in 0.073s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore CTXVAL1 is trusted Full-green at that exact SHA.

## Purpose

CTXVAL1 verifies whether a registered parent-context condition remains useful outside the data where it was first observed.

```text
trusted NEUTRAL micro profile
 + exact registered PCTX1 OBSERVED context
 + explicit context rule
 + TRAIN / VALIDATION / OOS / HARSH partitions
 -> independent evidence per partition
 -> slice-specific validation_evidence_hash
```

A condition that looks good on TRAIN but regresses on Validation, OOS or HARSH is rejected.

## Exact evidence requirements

Every validation case requires:

```text
mode == OBSERVED
context.as_of == case.knowledge_cutoff
parent_feature_contract == parent_context_assembly/v1
exact parent_feature_knowledge_cutoff
non-empty provider result/manifest identities
required registered manifest hash present
```

There is no nearest-time substitution, fill-forward, provider call or tactic replay.

CTXVAL1 requires exactly one TRAIN, VALIDATION and OOS partition and at least one HARSH partition with an explicit adverse reason. Case IDs are globally disjoint and all partitions use the same tactic candidate.

## Validation contract

The contract uses explicit independent tolerances for retained cases/activity, return, drawdown, profitable rate, cost and MFE giveback. There is no hidden weighted score.

A passing slice receives:

```text
status = PASS
evidence_status = VALIDATED
deployment_policy_evidence_eligible = true
validation_evidence_hash = <slice-specific hash>
operational_authority = false
```

CTXVAL1 itself remains:

```text
execution_integration = EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

## Initial validation incident

The first local attempt at `d2abaeedc4d464c1c3d27417980d93d202902b72` had one failing regression. It was classified as:

```text
test defect
```

The fixture accidentally made an internal context layer later than its enclosing context, so the trusted lower-level causality guard fired before the intended CTXVAL1 exact-time assertion. Only the test fixture was corrected; product code, tolerances and authority contracts were unchanged.

The corrected final checkout then received focused 7/7 PASS and Full PASS at `db9d9ddeeec55f2774d7a2d873ec2f19d77726b4`.

## Mutation boundary

CTXVAL1 did not modify Parser, Semantic, Runtime, BacktestEngine, BrokerEmulator, provider calculation, MSA1/MSA2 analysis, MSA3 publication, E8 attribution semantics, entry gates or Chart SSOT.

## What this proves and does not prove

It proves the validation machinery and evidence contract are executable and trusted. It does **not** prove that a real production GROUP rule is profitable, and it does not create operational trading authority.

The next authorized boundary is a non-operational bridge from a CTXVAL1 PASS slice to explicit E8 deployment-policy evidence. Actual entry-gate/Broker integration remains later and separately validated.

`REMEDIATION_REQUIRED` remains the broader repository status.
