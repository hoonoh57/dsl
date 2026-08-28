# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1-MSA3 + CTXVAL1 + CTXDEP1 + CTXINT1 TRUSTED / CTXINT2 ACTIVE / 2026-08-28 KST**

## 1. Governing rule

> Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.

Instrument DSL remains single-instrument. Cross-symbol research may inform bounded registered parent context, but it must not directly read peers, discover universes, rank symbols, allocate capital or create orders.

## 2. Trusted evidence/publication chain

```text
MSA1 immutable per-symbol snapshots
 -> MSA2 bounded chronological GROUP evidence
 -> MSA3 bounded aggregate registered GROUP features
 -> CTXVAL1 Train / Validation / OOS / Harsh context validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 trusted block-only composition preview
 -> CTXINT2 blocking-only Backtest entry-gate integration (active)
```

Trusted exact checkpoints:

```text
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
```

Each received focused regression PASS and Tactical P1 Full PASS at its exact SHA.

## 3. Observation and publication boundary

MSA1 freezes exact per-symbol causal snapshots under an explicit universe. MSA2 derives bounded leader/follower/breadth/persistence evidence. Both remain observation-only.

MSA3 may publish only bounded aggregate GROUP values. It does not publish peer identities, rank lists, allowed/blocked symbols, slot counts, allocation, entry gates or Broker instructions.

## 4. Validation and policy evidence

CTXVAL1 requires explicit TRAIN / VALIDATION / OOS / HARSH survival with no hidden weighted score. CTXDEP1 converts only a validated PASS condition into a non-operational policy-evidence bundle while preserving tactic, rule, feature, manifest and holdout provenance.

## 5. CTXINT1 trusted pre-integration proof

Trusted checkpoint:

```text
81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
Ran 7 tests in 0.129s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

The proven composition is:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated context permission
```

Therefore Add-on-derived context may only remove an existing local opportunity. It may never create one or bypass a hard guard.

## 6. CTXINT2 active blocking-only integration

CTXINT2 uses the existing Backtest `entry_gate` seam rather than changing Instrument DSL or Broker semantics. It requires exact validated tactic identity, exact DEPLOYMENT context, exact market symbol/timeline and explicit local evidence.

V1 is `bar_close` only and declares:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

`next_open` and pending-order context semantics are not inferred from this tranche and require separate validation.

## 7. Universe and causality

Every cross-symbol run must declare its universe and source authority. Future-close information, later winner labels, revised future data, nearest-time substitution and fill-forward are prohibited as earlier inputs.

## 8. Default disabled and replaceable

The Add-on remains optional and disabled by default during neutral micro discovery. A neutral tactic must remain independently runnable without cross-symbol intelligence.

The Add-on must remain removable without changing Instrument DSL syntax, Parser/Runtime, indicator semantics, Backtest accounting, BrokerEmulator or historical single-instrument evidence.

## 9. Authority relationship

After validated integration, the only allowed relationship is:

```text
single-instrument tactic trigger
AND local hard guards
AND optional validated Add-on/context permission
AND common execution policy
 -> BrokerEmulator
```

The Add-on can never bypass local guards, execution settings, accounting or Broker authority.

## 10. Change control

If a cross-symbol requirement can be expressed as read-only analysis of immutable per-symbol snapshots, it stays in the Add-on. If a conclusion is needed by Instrument DSL, expose only a bounded registered point-in-time parent feature.

Direct peer-symbol syntax in Instrument DSL remains unauthorized.

## 11. Current nonclaims

Do not claim trusted Full PASS for CTXINT2, validated `next_open` or pending-order context semantics, production/live Add-on gating, portfolio allocation authority, empirical GROUP profitability/generalization, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
