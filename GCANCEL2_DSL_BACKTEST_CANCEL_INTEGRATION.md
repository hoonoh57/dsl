# GCANCEL2 Generic DSL / Backtest Pending-Order Cancel Integration

Status: **TRUSTED FULL PASS / 2026-08-28 KST**

## Purpose

Expose the trusted Broker client-identity cancellation primitive through the Instrument DSL without adding market-, sector-, leader-, follower-, peer-symbol-, or learned-policy semantics.

## Trusted executable checkpoint

```text
3cd5731a1702f7bfb11878dfd6e34339baa5f163
Ran 5 tests in 0.004s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## Scope

Generic DSL form:

```text
order.cancel(id="stable-client-order-id")
```

Parser rules are fail-closed:

- `id` is mandatory;
- it must be one non-empty string literal;
- `order.cancel` cannot mix with entry/exit commands in the same `on` block;
- there is no feature-specific cancellation syntax.

Backtest timing is causal:

- `next_open`: prior completed-bar cancel intent is applied at the next bar before pending-order price matching;
- `bar_close`: current close-confirmed cancel intent is applied after that bar's matching and before newly submitted close-confirmed deferred orders.

The lifecycle transition remains owned by:

```text
BrokerEmulator.cancel_client_order(...)
 -> BrokerEmulator.cancel(...)
 -> ACCEPTED/TRIGGERED -> CANCELED
```

Unknown or ambiguous client identity remains fail-closed.

## Executable change boundary

Since trusted GCANCEL1, executable changes are only:

```text
core/dsl_parser.py
core/backtest.py
test_stage1_dsl_pending_order_cancel.py
```

No multi-symbol Add-on, parent-context provider, sector/leader/follower implementation, allocation logic, or learned-policy code changed.

## Next boundary

Do not expand Core automatically. First validate the existing composition:

```text
registered exact ctx.* evidence
 + follower-local setup
 -> generic pending order with stable id
 -> later ctx.* invalidation
 -> order.cancel(id=...)
 -> BrokerEmulator
```

This next boundary should be test-only unless a real generic gap is demonstrated.

## Nonclaims

GCANCEL2 does not validate a profitable leader/follower edge, production cross-symbol orchestration, live broker cancellation, live readiness, or repository-wide compliance.

Broader repository status remains `REMEDIATION_REQUIRED`.
