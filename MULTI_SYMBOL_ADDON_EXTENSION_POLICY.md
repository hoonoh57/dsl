# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1-MSA3 + CTXVAL1 + CTXDEP1 TRUSTED / CTXINT1 ACTIVE / 2026-08-28 KST**

## 1. Governing rule

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

Instrument DSL remains single-instrument. Cross-symbol research may inform bounded registered parent context, but it must not directly read peers, discover universes, rank symbols, allocate capital or create orders.

## 2. Trusted evidence/publication chain

```text
MSA1 immutable per-symbol snapshots
 -> MSA2 bounded chronological GROUP evidence
 -> MSA3 bounded aggregate registered GROUP features
 -> CTXVAL1 Train / Validation / OOS / Harsh context validation
 -> CTXDEP1 validated deployment-policy evidence
```

Trusted exact checkpoints:

```text
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
```

Each received focused regression PASS and Tactical P1 Full PASS at its exact SHA.

## 3. MSA1/MSA2 observation boundary

MSA1 freezes exact per-symbol causal snapshots under an explicit universe. MSA2 derives bounded leader/follower/breadth/persistence observation evidence from those snapshots.

Both remain:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

Leader/follower labels are descriptive evidence, not symbol permission.

## 4. MSA3 GROUP publication boundary

MSA3 may publish only bounded aggregate GROUP values through the registered Parent Feature Provider seam. It does not publish peer identities, rank lists, allowed/blocked symbols, slot counts, allocation, entry gates or Broker instructions.

Publication remains research-only and exact-time. Missing follower evidence remains absent rather than being manufactured as zero.

## 5. CTXVAL1 usefulness validation

A published GROUP feature must survive explicit TRAIN / VALIDATION / OOS / HARSH checks before any deployment-policy evidence is allowed.

A condition that looks favorable only on TRAIN is rejected. There is no hidden weighted score.

CTXVAL1 is trusted at:

```text
db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
Ran 7 tests in 0.073s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## 6. CTXDEP1 policy evidence

CTXDEP1 converts only a validated CTXVAL1 PASS condition into a non-operational deployment-policy evidence bundle while preserving exact tactic, rule, feature, manifest and holdout provenance.

CTXDEP1 is trusted at:

```text
804baea25f29d1c77f2984d67e37dbb5ebb1160e
Ran 6 tests in 0.028s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

A validated policy document still does not have execution authority.

## 7. CTXINT1 active pre-integration proof

Before any Add-on-derived context may influence the existing entry gate, CTXINT1 must prove the composition rule:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated context permission
```

This means Add-on context may only remove an existing local opportunity. It may never create one or bypass a hard guard.

CTXINT1 remains preview-only and does not call or modify BacktestEngine or BrokerEmulator.

## 8. Universe and causality

Every cross-symbol run must declare its universe and source authority. Future-close information, later winner labels, revised future data, nearest-time substitution and fill-forward are prohibited as earlier inputs.

## 9. Default disabled and replaceable

The Add-on remains optional and disabled by default during neutral micro discovery. A neutral tactic must remain independently runnable without cross-symbol intelligence.

The Add-on must remain removable without changing Instrument DSL syntax, Parser/Runtime, indicator semantics, Backtest accounting, BrokerEmulator or historical single-instrument evidence.

## 10. Eventual authority relationship

Only after separately validated integration may the relationship become:

```text
single-instrument tactic trigger
AND local hard guards
AND optional validated Add-on/context permission
AND common execution policy
 -> BrokerEmulator
```

The Add-on can never bypass local guards, execution settings, accounting or Broker authority.

## 11. Change control

If a cross-symbol requirement can be expressed as read-only analysis of immutable per-symbol snapshots, it stays in the Add-on. If a conclusion is needed by Instrument DSL, expose only a bounded registered point-in-time parent feature.

Direct peer-symbol syntax in Instrument DSL remains unauthorized.

## 12. Current nonclaims

Do not claim operational Add-on selection, parent-context entry gating, portfolio allocation authority, empirical GROUP profitability/generalization, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
