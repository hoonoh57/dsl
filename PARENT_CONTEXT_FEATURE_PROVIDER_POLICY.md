# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / CTXINT2 TRUSTED / CTXINT3 ACTIVE / 2026-08-28 KST**

## Governing rule

> Parent features are computed outside Instrument DSL, frozen as point-in-time evidence, validated out-of-sample, and may only restrict an already-valid local tactic opportunity.

Instrument DSL remains deterministic and single-instrument. Parent context may never create an entry, bypass a local hard guard, change exit authority or submit Broker orders directly.

## Trusted evidence and integration path

```text
PCTX provider / exact frame / registered binding
 -> MSA bounded GROUP publication
 -> CTXVAL1 Train / Validation / OOS / Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 block-only composition proof
 -> CTXINT2 trusted bar_close Backtest entry suppression
 -> CTXINT3 next_open causal timing validation (active)
```

Recent trusted checkpoints:

```text
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
CTXINT2 b3b547b9d2d0eaeee654790243f031a3bbb88198
```

Each received focused regression PASS and Tactical P1 Full PASS at its exact SHA.

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

## CTXINT2 trusted bar-close integration

Trusted checkpoint:

```text
b3b547b9d2d0eaeee654790243f031a3bbb88198
Ran 7 tests in 0.106s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXINT2 reuses the existing Backtest `entry_gate` and proves blocking-only `bar_close` integration. BrokerEmulator remains execution authority and exits are not controlled by parent context.

During subsequent timing review, deferred entry orders were identified as a separate authority problem. Current CTXINT2 source is therefore narrowed to MARKET entries only; that post-trust hardening is revalidated with CTXINT3.

## CTXINT3 active next-open timing rule

`next_open` may use only evidence already known at the prior completed bar:

```text
bar t completes
 -> tactic trigger / local hard guard / validated context permission are known
 -> permission is shifted forward
 -> may gate an existing MARKET entry at bar t+1 open
```

The unfinished context of bar t+1 may not be used to rescue or alter the t+1 open decision. The first bar has no prior completed-bar authority.

CTXINT3 retains the same narrow authority:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

## Deferred-order boundary

LIMIT/STOP/STOP_LIMIT validated-context integration remains fail-closed.

A deferred order may live beyond its originating signal bar, so a separate contract must decide whether fill authority comes from the original signal-time context, the latest completed pre-fill context, continuous permission, explicit cancellation on context change, or another declared rule.

Until that contract is independently validated, generic DSL/Broker deferred-order capability does not imply validated parent-context authority for those orders.

## Core boundary

Instrument DSL must not directly implement provider/network/database calls, universe discovery, peer-symbol runtime reads, ranking, leader/follower selection, allocation or arbitrary dynamic context discovery.

Parent allow is permission only, never forced entry. Macro context must amplify a valid micro tactic rather than become life support for one.

## Current nonclaims

Do not claim trusted Full PASS for CTXINT3, validated pending-order context semantics, production/live parent-context gating, empirical GROUP profitability/generalization, automatic cross-symbol allocation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
