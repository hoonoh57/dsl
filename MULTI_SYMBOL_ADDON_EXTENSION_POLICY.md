# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / CTXINT2 TRUSTED / CTXINT3 ACTIVE / 2026-08-28 KST**

## 1. Governing rule

> Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.

Instrument DSL remains single-instrument. Cross-symbol research may inform bounded registered parent context, but it must not directly read peers, discover universes, rank symbols, allocate capital or create orders.

## 2. Trusted evidence path

```text
MSA1 immutable per-symbol snapshots
 -> MSA2 bounded chronological GROUP evidence
 -> MSA3 bounded aggregate registered GROUP features
 -> CTXVAL1 Train / Validation / OOS / Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 block-only composition proof
 -> CTXINT2 trusted bar_close Backtest entry suppression
 -> CTXINT3 next_open causal timing validation (active)
```

Recent trusted checkpoints:

```text
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
CTXINT2 b3b547b9d2d0eaeee654790243f031a3bbb88198
```

## 3. Observation/publication boundary

MSA1 and MSA2 remain observation-only. MSA3 publishes only bounded aggregate GROUP values and does not publish peer identities, rank lists, allowed/blocked symbols, allocation, entry gates or Broker instructions.

Cross-symbol evidence does not become execution authority merely because it is available as registered context.

## 4. Validation and policy evidence

CTXVAL1 requires explicit TRAIN / VALIDATION / OOS / HARSH survival with no hidden weighted score. CTXDEP1 creates policy evidence only from a validated PASS condition while preserving tactic/rule/feature/manifest/holdout provenance.

CTXINT1 proves the only allowed composition:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated context permission
```

The Add-on may only remove an existing local opportunity.

## 5. CTXINT2 trusted blocking-only integration

Trusted exact checkout:

```text
b3b547b9d2d0eaeee654790243f031a3bbb88198
Ran 7 tests in 0.106s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXINT2 uses the existing Backtest `entry_gate`; BrokerEmulator remains execution authority. This trusted checkpoint covers the validated `bar_close` MARKET-entry path exercised by its regression.

The current source is additionally hardened to reject deferred entry orders until their timing contract is validated.

## 6. CTXINT3 active next-open timing

For `next_open`, Add-on/context permission must come only from the prior completed bar. The next bar's unfinished context cannot influence its own open.

```text
completed bar t context
 -> shifted gate
 -> bar t+1 MARKET open
```

This remains entry suppression only. It cannot create entry, bypass local guards, block exits or submit Broker orders.

## 7. Deferred-order boundary

LIMIT/STOP/STOP_LIMIT context gating is not inferred from bar-close or next-open MARKET semantics. A pending order can survive across multiple context changes, so original-signal permission and later fill permission require a separate explicit contract.

Until then validated-context integration rejects deferred entry orders. Generic Broker support for pending orders remains unchanged.

## 8. Universe and causality

Every cross-symbol run must declare its universe and source authority. Future-close information, later winner labels, revised future data, nearest-time substitution and fill-forward are prohibited as earlier inputs.

## 9. Default disabled and replaceable

The Add-on remains optional and disabled by default during neutral micro discovery. A neutral tactic must remain independently runnable without cross-symbol intelligence.

The Add-on must remain removable without changing Instrument DSL syntax, Parser/Runtime, indicator semantics, Backtest accounting, BrokerEmulator or historical single-instrument evidence.

## 10. Current nonclaims

Do not claim trusted Full PASS for CTXINT3, validated pending-order context semantics, production/live Add-on gating, portfolio allocation authority, empirical GROUP profitability/generalization, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
