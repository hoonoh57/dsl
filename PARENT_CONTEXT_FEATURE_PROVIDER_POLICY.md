# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / CTXVAL1 + CTXDEP1 + CTXINT1 TRUSTED / CTXINT2 ACTIVE / 2026-08-28 KST**

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
 -> CTXINT1 trusted block-only composition preview
 -> CTXINT2 blocking-only Backtest entry-gate integration (active)
```

Recent trusted checkpoints:

```text
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
```

Each received focused regression PASS and Tactical P1 Full PASS at the exact SHA.

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

## GROUP publication and validation

MSA3 may publish only bounded aggregate GROUP context. It does not publish peer identities, rankings, allowed/blocked symbol lists, allocation, entry gates or Broker instructions.

CTXVAL1 requires independent TRAIN, VALIDATION, OOS and HARSH survival under explicit no-hidden-score tolerances. CTXDEP1 may create a policy document only from a validated PASS slice while preserving exact tactic, rule, feature, manifest and holdout identities.

## CTXINT1 trusted composition rule

Trusted checkpoint:

```text
81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
Ran 7 tests in 0.129s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXINT1 proves:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated parent-context permission
```

Parent context may only remove an existing local opportunity. It may never create entry or bypass a failed hard guard.

## CTXINT2 active integration boundary

CTXINT2 is the first blocking-only Backtest integration. It reuses the existing `BacktestEngine.run(..., entry_gate=...)` seam instead of adding execution semantics.

V1 requires exact validated tactic identity, exact DEPLOYMENT frame/registry, exact market symbol/full timeline, explicit tactic-trigger/local-hard-guard evidence, and `signal_mode=bar_close`.

Authority is deliberately narrow:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

`next_open` is rejected in v1 until signal-time/fill-time context semantics receive separate validation.

## Core and execution boundary

Instrument DSL must not directly implement provider/network/database calls, universe discovery, peer-symbol runtime reads, cross-sectional ranking, leader/follower selection, portfolio allocation or arbitrary dynamic context discovery.

A context policy may never force an entry, change exit/risk behavior or submit Broker orders directly. BrokerEmulator remains execution authority.

## Required progression

```text
robust NEUTRAL micro tactic
 -> causal OBSERVED parent evidence
 -> attribution
 -> Train/Validation/OOS/Harsh validation
 -> validated deployment-policy evidence
 -> trusted block-only composition proof
 -> blocking-only Backtest integration
 -> separately validated additional execution modes / production integration
```

## Current nonclaims

Do not claim yet trusted Full PASS for CTXINT2, validated `next_open` or pending-order context semantics, production/live parent-context gating, empirical GROUP profitability, automatic cross-symbol allocation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
