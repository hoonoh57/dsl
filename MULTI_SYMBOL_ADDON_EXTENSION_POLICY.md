# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / CTXINT3 TRUSTED / LF1 TRUSTED / NEXT GENERIC CANCEL / 2026-08-28 KST**

## 1. Governing rule

> Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.

Instrument DSL remains single-instrument. Cross-symbol analysis may calculate sector, leader/follower and lag relationships outside DSL, but Instrument DSL must not discover peers, rank symbols, allocate capital or calculate leader/follower roles itself.

## 2. Trusted evidence path

```text
MSA1 immutable per-symbol snapshots
 -> MSA2 bounded chronological GROUP evidence
 -> MSA3 bounded aggregate registered GROUP features
 -> CTXVAL1 Train / Validation / OOS / Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 block-only composition proof
 -> CTXINT2 trusted bar_close entry suppression
 -> CTXINT3 trusted next_open prior-completed-bar timing
 -> LF1 trusted leader/follower relation evidence
```

Trusted recent checkpoints:

```text
MSA1    adaef963dce717b252f2575896a74462c8a277a2
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
CTXINT2 b3b547b9d2d0eaeee654790243f031a3bbb88198
CTXINT3 7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1     5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
```

LF1 operator evidence:

```text
Ran 7 tests in 0.058s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## 3. Observation/publication boundary

MSA1/MSA2/LF1 remain observation-only. MSA3 publishes only bounded aggregate GROUP values and does not publish peer identities, allocation, entry gates or Broker instructions.

Cross-symbol evidence does not become execution authority merely because it exists.

## 4. LF1 trusted leader/follower relation evidence

LF1 is the first trusted reusable leader/follower evidence branch over exact MSA1/MSA2 inputs.

Its first version deliberately supports:

- one explicit current leader;
- leader qualification from minimum persistence and minimum leader/follower spread;
- explicit leader impulse threshold;
- follower reaction search over a declared `1..N` point lag window;
- separate follow-rate, mean-lag, response-strength and current-metric evidence;
- explicit follow-rate ordering with deterministic tie-break;
- censored trailing impulses rather than silently treating unavailable response windows as failures;
- no hidden universal score.

LF1 may expose leader/follower symbol identities because it is an Add-on research artifact, but it declares `operational_authority=false` and cannot create allowed/blocked lists, allocation, entry gates or Broker actions.

## 5. Core DSL relationship

The intended product boundary is:

```text
Add-on decides/describes market relationship
 -> generic frozen evidence / later validated orchestration
 -> Instrument DSL uses ordinary local signals and generic order primitives
```

Leader/follower, sector ranking or peer-symbol syntax must not be added to Instrument DSL merely to make one story convenient.

The next planned Core tranche is a generic pending-order cancellation primitive by explicit stable order/client identity. It must be independently useful without any multi-symbol Add-on and must have deterministic Backtest/Broker semantics.

## 6. Existing validated context integration

CTXINT2/CTXINT3 context permission can only suppress an existing local opportunity. It cannot create entry, bypass local hard guards, block exits or submit Broker orders.

For `next_open`, only the prior completed bar's validated context may govern the next open.

## 7. Deferred-order boundary

Generic LIMIT/STOP/STOP_LIMIT support exists in the Broker/Backtest engine, but cross-symbol/context pending-order orchestration is not yet authorized.

The planned progression is:

```text
LF1 relation evidence trusted
 -> generic DSL cancel semantics trusted
 -> conditional pending-intent orchestration
 -> separate Train/Validation/OOS/Harsh evidence
 -> only then consider operational selection/gating
```

A later orchestration may tell a story such as leader rebound -> follower setup -> pending follower order -> leader/group invalidation -> cancel, but only after generic cancellation is independently trusted.

## 8. Universe and causality

Every cross-symbol run must declare its universe and source authority. Future-close information, later winner labels, revised future data, nearest-time substitution and fill-forward are prohibited as earlier inputs.

## 9. Default disabled and replaceable

The Add-on remains optional and disabled by default during neutral micro discovery. A neutral tactic must remain independently runnable without cross-symbol intelligence.

The Add-on must remain removable without changing Instrument DSL syntax, indicator semantics, Backtest accounting or BrokerEmulator.

## 10. Current nonclaims

Do not claim profitable leader/follower selection, validated pending-order cancellation/orchestration, portfolio allocation authority, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
