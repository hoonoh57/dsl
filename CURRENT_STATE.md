# Quant DSL Current State

Status: **GCANCEL1_TRUSTED_FULL_PASS / GCANCEL2_TRUSTED_FULL_PASS / VSLICE1_REMOTE_UNVALIDATED_TEST_ONLY / REMEDIATION_REQUIRED**  
Updated: 2026-08-28 KST

## Recovery

`SESSION_HANDOFF.md` is the primary human-readable handoff. Exact user-local focused + Full PASS evidence outranks stale validation text; newer remote executable/test commits without local PASS remain untrusted.

## Governing architecture

Core DSL stays deterministic and single-instrument. Cross-symbol/leader/follower intelligence remains external Add-on/context evidence.

```text
single-instrument causal snapshots
 -> bounded external evidence
 -> local deterministic setup + hard guards
 -> generic pending order
 -> generic cancel by stable client identity
 -> BrokerEmulator
```

Hard equipment/guards remain authoritative before optional adaptive intelligence. No peer discovery, ranking, allocation, provider calls, or learning authority belongs in Parser/Runtime/Backtest/Broker.

## Trusted exact checkpoints relevant to current boundary

```text
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
CTXINT3           7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1               5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
GCANCEL1          583c5362ca5ea57e62353a963cd5a2cfb0addfad
GCANCEL2          3cd5731a1702f7bfb11878dfd6e34339baa5f163
```

Recent operator evidence:

```text
LF1:      Ran 7 tests in 0.058s / OK / Full PASS
GCANCEL1: Ran 5 tests in 0.000s / OK / Full PASS
GCANCEL2: Ran 5 tests in 0.004s / OK / Full PASS
```

## Trusted generic capabilities

1. Registered exact DEPLOYMENT parent context can enter Instrument DSL only through read-only `ctx.*` binding.
2. Parent context cannot create trades or bypass a failed local hard guard.
3. Generic pending LIMIT/STOP/STOP_LIMIT orders use stable client identities and Broker-owned lifecycle.
4. `order.cancel(id="...")` is trusted and routes only to BrokerEmulator cancellation.
5. `next_open` cancellation uses prior completed-bar evidence before next-bar matching; `bar_close` cancellation acts after current-bar matching.

## VSLICE1 review conclusion

The minimal vertical slice does **not** currently demonstrate a missing Core primitive. The missing proof was composition evidence:

```text
exact registered ctx.* permission
 + follower-local deterministic setup
 -> pending LIMIT with stable id
 -> later exact ctx.* invalidation
 -> order.cancel(id=...)
 -> BrokerEmulator
```

This is consistent with `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`: pending-order context orchestration required a separate validation contract, not peer-analysis logic inside DSL.

## VSLICE1 remote-unvalidated test-only tranche

Executable validation checkpoint:

```text
72445456e86b695dc7288ab3a48856fa560463dd
```

Only new executable file:

```text
test_stage1_context_pending_order_cancel.py
```

No product source file changed.

Focused cases:

- `bar_close`: valid local setup + context creates one pending LIMIT; later context invalidation cancels before a later fill-eligible bar;
- `next_open`: prior completed-bar context invalidation cancels before the next fill-eligible bar is matched;
- both retain `BrokerEmulator` as execution authority and produce zero fills after cancellation.

## Immediate trust gate

```powershell
python -m unittest test_stage1_context_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not mark VSLICE1 trusted until both pass locally.

If VSLICE1 passes, consider the generic mechanical vertical slice closed. The next work should move outward to one deterministic external evidence/tactic experiment; do not add adaptive learning, ranking expansion, allocation, or new Core grammar without a separately demonstrated need.

## Remote CI environment

GitHub Actions failures that occur before executable job steps receive a runner remain classified as `environment issue`; do not weaken guards or tests.

## Nonclaims

No profitable leader/follower edge, production leader selection, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
