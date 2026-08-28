# GCANCEL2 Generic DSL / Backtest Pending-Order Cancel Integration

Status: **REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / 2026-08-28 KST**

## Purpose

Expose the already-trusted Broker client-identity cancellation primitive through the Instrument DSL without adding any market-, sector-, leader-, follower-, peer-symbol-, or learned-policy semantics.

## Trusted prerequisite

GCANCEL1 executable checkpoint:

```text
583c5362ca5ea57e62353a963cd5a2cfb0addfad
Ran 5 tests in 0.000s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

GCANCEL1 is therefore trusted.

## Scope

The new generic DSL form is:

```text
order.cancel(id="stable-client-order-id")
```

Parser rules are fail-closed:

- `id` is mandatory;
- it must be one non-empty string literal;
- `order.cancel` cannot be mixed with entry/exit commands in the same `on` block;
- no feature-specific cancellation syntax exists.

Backtest timing remains causal:

- `next_open`: a cancel intent confirmed on the prior completed bar is applied at the next bar before pending-order price matching;
- `bar_close`: a cancel intent is applied at the current bar close, after that bar's intrabar matching and before new close-confirmed deferred orders are submitted.

The actual lifecycle transition still delegates to:

```text
BrokerEmulator.cancel_client_order(...)
 -> BrokerEmulator.cancel(...)
 -> ACCEPTED/TRIGGERED -> CANCELED
```

Unknown or ambiguous client identity remains fail-closed through the trusted Broker primitive.

## Executable remote checkpoint

```text
3cd5731a1702f7bfb11878dfd6e34339baa5f163
```

Relevant executable changes since trusted GCANCEL1:

```text
core/dsl_parser.py
core/backtest.py
test_stage1_dsl_pending_order_cancel.py
```

No multi-symbol Add-on, parent-context provider, sector/leader/follower implementation, allocation logic, or learned-policy code is modified.

## Focused validation

```powershell
python -m unittest test_stage1_dsl_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

GCANCEL2 must remain `REMOTE_UNVALIDATED` until exact user-local focused + Full PASS evidence is reported.

## Nonclaims

This checkpoint does not validate any leader/follower trading edge, cross-symbol orchestration, live broker cancellation, profitability, or repository-wide compliance.

Broader repository status remains `REMEDIATION_REQUIRED`.
