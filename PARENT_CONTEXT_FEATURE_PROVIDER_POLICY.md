# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / CTXVAL1 + CTXDEP1 TRUSTED / CTXINT1 ACTIVE / 2026-08-28 KST**

## Governing rule

> **Parent features are computed outside Instrument DSL, frozen as point-in-time evidence, consumed through registered read-only binding, validated out-of-sample, and may only restrict an already-valid local tactic opportunity.**

Instrument DSL remains deterministic and single-instrument. It may read stable registered `ctx.*` values, but it must not calculate parent features, call providers, discover peers/universes, rank symbols, allocate capital or create trades from macro context alone.

## Trusted context path

```text
PCTX1 typed/versioned provider contract
 -> PCTX2B exact ParentContextFrame
 -> CTXDSL1 registered read-only ctx.*
 -> CTXBT1 exact Backtest binding
```

Trusted provider/publication path:

```text
PCTX2A MARKET
 -> PCTX2C exact root precomputation
 -> PCTX2D dependency DAG
 -> descriptive SECTOR
 -> MSA3 bounded aggregate GROUP publication
```

Trusted validation/policy-evidence path:

```text
registered OBSERVED context
 -> CTXVAL1 Train / Validation / OOS / Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
```

Trusted recent checkpoints:

```text
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
```

Each received focused regression PASS and Tactical P1 Full PASS at the exact SHA.

## Exact evidence rules

Parent context transport remains exact and fail-closed:

```text
target_time == assembly.knowledge_cutoff == context.as_of
NO nearest-time lookup
NO fill-forward
NO interpolation
NO silent default for required values
NO provider call from Parser / Runtime / Backtest / Broker
```

Feature IDs and provider manifests are versioned identities. Missing, stale, future or semantically mismatched evidence is rejected rather than guessed.

## GROUP publication boundary

MSA3 may publish only bounded aggregate GROUP context through PCTX1. It does not publish peer symbol identities, rankings, allowed/blocked symbol lists, allocation, entry gates or Broker instructions.

Publication itself remains research evidence and is not deployment authority.

## CTXVAL1 validation authority

A registered context condition must survive independent:

```text
TRAIN
VALIDATION
OOS
HARSH
```

checks under explicit no-hidden-score tolerances before it can become deployment-policy evidence.

A TRAIN-positive condition that regresses in OOS/HARSH is rejected. A passing slice receives a slice-specific validation evidence identity, but still has no execution authority.

Trusted checkpoint:

```text
db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
Ran 7 tests in 0.073s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## CTXDEP1 policy-evidence authority

CTXDEP1 may create an E8 deployment-policy document only from one independently validated CTXVAL1 PASS slice while preserving exact tactic, rule, feature, manifest, validation and partition-attribution identities.

Trusted checkpoint:

```text
804baea25f29d1c77f2984d67e37dbb5ebb1160e
Ran 6 tests in 0.028s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

The resulting policy remains non-operational. A validated policy document is not an installed gate.

## CTXINT1 active composition gate

Before any operational wiring, CTXINT1 must prove:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated parent-context permission
```

Therefore parent context may only remove an existing local opportunity. It may never:

```text
create an entry when the tactic has no trigger
bypass a failed local hard guard
bypass common execution policy
issue a Broker order directly
```

CTXINT1 uses exact DEPLOYMENT context and produces preview evidence only:

```text
operational_authority = false
execution_integration = PREVIEW_ONLY_NOT_INSTALLED_AS_BACKTEST_ENTRY_GATE_OR_BROKER
```

Operational entry-gate integration remains forbidden until CTXINT1 receives its own trusted exact Full checkpoint and a later separately authorized integration tranche is validated.

## Core boundary

Instrument DSL must not directly implement:

```text
provider/network/database calls
universe discovery
peer-symbol runtime reads
cross-sectional ranking
leader/follower selection
portfolio allocation
arbitrary dynamic context discovery
```

The only Core-facing parent seam remains already-frozen registered read-only context.

## Required progression

```text
robust NEUTRAL micro tactic
 -> causal OBSERVED parent evidence
 -> attribution
 -> Train / Validation / OOS / Harsh validation
 -> validated deployment-policy evidence
 -> preview-only AND-composition proof
 -> separately validated operational integration
 -> existing common execution policy
 -> BrokerEmulator
```

Parent allow is permission, never forced entry. Macro context must amplify a valid micro tactic rather than become life support for one.

## Current nonclaims

Do not claim yet operational parent-context gating, actual Broker suppression, empirical profitability/generalization of a real GROUP rule, automatic cross-symbol selection/allocation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
