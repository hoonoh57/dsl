# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / CTXVAL1-CTXINT3 TRUSTED / 2026-08-28 KST**

## Governing rule

> Parent features are computed outside Instrument DSL, frozen as point-in-time evidence, consumed through registered read-only binding, validated out-of-sample, and may only restrict an already-valid local tactic opportunity.

Instrument DSL remains deterministic and single-instrument. It may read stable registered `ctx.*` values, but it must not calculate parent features, call providers, discover peers/universes, rank symbols, allocate capital or create trades from macro context alone.

## Trusted context and evidence path

```text
PCTX1 typed/versioned provider contract
 -> PCTX2B exact ParentContextFrame
 -> CTXDSL1 registered read-only ctx.*
 -> CTXBT1 exact Backtest binding
 -> PCTX2A/PCTX2C/PCTX2D MARKET/SECTOR production
 -> MSA1/MSA2/MSA3 bounded GROUP evidence/publication
 -> CTXVAL1 Train/Validation/OOS/Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 block-only composition proof
 -> CTXINT2 bar_close Backtest entry suppression
 -> CTXINT3 next_open prior-completed-bar timing
```

Recent trusted checkpoints:

```text
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
CTXINT2 b3b547b9d2d0eaeee654790243f031a3bbb88198
CTXINT3 7f77694658d7155806e97bdafcc543e2c7bfeae8
```

CTXINT3 exact operator evidence:

```text
Ran 7 tests in 0.150s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## Exact evidence rules

Parent context remains exact and fail-closed:

```text
target_time == assembly.knowledge_cutoff == context.as_of
NO nearest-time lookup
NO fill-forward
NO interpolation
NO silent default for required values
NO provider call from Parser / Runtime / Backtest / Broker
```

Feature IDs and provider manifests are versioned identities. Missing, stale, future or semantically mismatched evidence is rejected rather than guessed.

## GROUP publication and leader/follower analysis boundary

MSA3 may publish only bounded aggregate GROUP context. It does not publish peer identities, rank lists, allowed/blocked symbol lists, allocation, entry gates or Broker instructions.

New leader/follower relation research such as LF1 remains a multi-symbol Add-on artifact. It may analyze exact peer snapshots and expose research identities, but those identities do not automatically become registered parent context or deployment authority.

If a later follower tactic needs a parent feature, only a separately validated bounded aggregate/frozen value may cross the provider/binder seam. Instrument DSL must never calculate the peer relationship itself.

## Validated composition rule

The trusted composition remains:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated parent-context permission
```

Parent context may only remove an existing local opportunity. It may never create entry or bypass a failed hard guard.

For `next_open`, only permission known at the prior completed bar may govern the next open. The fill bar's unfinished context is not usable.

## Deferred-order boundary

LIMIT/STOP/STOP_LIMIT pending orders have a separate signal-time/fill-time/cancellation authority problem. Trusted CTXINT2/CTXINT3 do not authorize parent-context pending-order orchestration.

A future generic DSL cancellation primitive must be validated independently as an order capability. Any later context- or leader/follower-driven cancellation must consume frozen validated evidence through orchestration rather than embedding peer analysis into DSL execution.

## Core and execution boundary

Instrument DSL must not directly implement provider/network/database calls, universe discovery, peer-symbol runtime reads, cross-sectional ranking, leader/follower selection, portfolio allocation or arbitrary dynamic context discovery.

A context policy may never force an entry, change exit/risk behavior or submit Broker orders directly. BrokerEmulator remains execution authority.

## Current nonclaims

Do not claim profitable GROUP/leader-follower edge, production peer selection, validated context-driven pending-order cancellation, portfolio allocation authority, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
