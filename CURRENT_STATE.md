# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / REMEDIATION_REQUIRED**  
Updated: 2026-08-28 KST

## Recovery

`SESSION_HANDOFF.md` is the primary human-readable handoff. Exact user-local focused + Full PASS evidence outranks stale validation text; newer remote executable/test commits without local PASS remain untrusted.

## Governing architecture

Core DSL stays deterministic and single-instrument. Cross-symbol/leader/follower intelligence remains optional Add-on evidence/orchestration.

```text
single-instrument causal snapshots
 -> bounded external LF1 evidence
 -> local deterministic setup + hard guards
 -> LF2 observation-only ARM/CANCEL/HOLD intent evidence
 -> existing generic DSL pending/cancel machinery
 -> BrokerEmulator
```

Hard equipment/guards remain authoritative before optional adaptive intelligence. No peer discovery, ranking, allocation, provider calls, learning authority or leader/follower semantics belongs in Parser/Runtime/Backtest/Broker.

## Trusted exact checkpoints relevant to current boundary

```text
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
CTXINT3           7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1               5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
GCANCEL1          583c5362ca5ea57e62353a963cd5a2cfb0addfad
GCANCEL2          3cd5731a1702f7bfb11878dfd6e34339baa5f163
VSLICE1           72445456e86b695dc7288ab3a48856fa560463dd
```

Recent operator evidence:

```text
LF1:      Ran 7 tests in 0.058s / OK / Full PASS
GCANCEL1: Ran 5 tests in 0.000s / OK / Full PASS
GCANCEL2: Ran 5 tests in 0.004s / OK / Full PASS
VSLICE1:  Ran 2 tests in 0.039s / OK / Full PASS
```

## Generic mechanical vertical slice — closed

VSLICE1 trusted proof:

```text
exact registered ctx.* permission
 + follower-local deterministic setup
 -> pending LIMIT with stable id
 -> later exact ctx.* invalidation
 -> order.cancel(id=...)
 -> BrokerEmulator
```

No missing Core primitive was demonstrated. Do not expand Core merely to support leader/follower convenience.

## LF2 remote-unvalidated Add-on tranche

Executable checkpoint:

```text
14bf03f1f9473a607d4330e4d06f9d0ef9bdd219
```

Executable files added:

```text
core/multi_symbol_follower_pending_orchestration.py
test_stage1_multi_symbol_follower_pending_orchestration.py
```

LF2 consumes only frozen evidence/state:

```text
LF1 OBSERVATION_ONLY relation result
+ selected/local follower identity
+ local setup pass/fail
+ local hard-guard pass/fail
+ explicit relation_still_valid
+ existing pending identity when active
```

It emits observation-only intent evidence:

```text
ARM_PENDING
HOLD
HOLD_PENDING
CANCEL_PENDING
```

It has `operational_authority=false` and `execution_authority=false`. It does not call DSLRuntime, BacktestEngine, BrokerEmulator, ParentFeatureProvider, network or persistence.

Deterministic priority:

- hard guard failure blocks a new ARM;
- hard guard failure cancels an already-active pending intent;
- explicit relation invalidation cancels an already-active pending intent;
- only the LF1-qualified selected follower with passing local setup + hard guard + valid relation may ARM;
- active cancellation reuses the explicit existing client identity and fails closed when missing.

## LF2 trust gate

```powershell
python -m unittest test_stage1_multi_symbol_follower_pending_orchestration.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not mark LF2 trusted until both pass locally.

After LF2 trust, do not immediately grant deployment authority. The next boundary is to decide whether this observation-only orchestration should enter a separate Train/Validation/OOS/Harsh evidence tranche. No automatic allocation, live selection or adaptive autonomy.

## Remote CI environment

GitHub Actions for LF2 failed before executable job steps were created (`steps=null`). Classification: `environment issue`. Do not weaken guards or tests.

## Nonclaims

No profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
