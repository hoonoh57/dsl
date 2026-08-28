# CTXINT3 Validated Context Next-Open Timing Integration — Implementation Checkpoint

Status: **TRUSTED FULL PASS / NEXT_OPEN MARKET ONLY / 2026-08-28 KST**

## Exact trusted checkpoint

Operator validation completed at exact checkout:

```text
7f77694658d7155806e97bdafcc543e2c7bfeae8
Ran 7 tests in 0.150s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

This exact checkout is the trusted CTXINT3 executable checkpoint.

## Proven boundary

CTXINT3 defines causal `signal_mode=next_open` timing without changing BacktestEngine or BrokerEmulator:

```text
completed bar t trigger
 + local hard guard
 + validated parent-context permission known at t
 -> shifted one bar
 -> may suppress/allow the already-existing MARKET entry at bar t+1 open
```

The not-yet-completed context of bar `t+1` cannot rescue or alter its own open decision. The first bar has no prior completed-bar authority.

Authority remains narrow:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

## Deferred-order boundary

`LIMIT`, `STOP` and `STOP_LIMIT` entry orders remain deliberately outside CTXINT3. A pending order may survive across several context changes, so signal-time permission, later fill-time permission and cancellation require a separate contract.

The current validated-context integration scope therefore rejects deferred entry orders. Generic Broker pending-order support itself remains unchanged.

## Mutation boundary

CTXINT3 added only the next-open sidecar adapter, shared validated-context order-scope guard and focused regression. Parser grammar, Runtime semantics, BacktestEngine implementation, BrokerEmulator, provider calculation and CTXVAL1/CTXDEP1 adjudication were not changed.

## Nonclaims

Trusted CTXINT3 does not imply validated deferred-order context semantics, profitable GROUP context, production/live parent-context gating, automatic cross-symbol allocation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
