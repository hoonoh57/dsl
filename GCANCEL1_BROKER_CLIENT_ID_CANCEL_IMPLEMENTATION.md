# GCANCEL1 Broker Client-Identity Cancel Primitive

Status: **REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / 2026-08-28 KST**

## Scope

This micro-tranche adds exactly one generic execution primitive: cancellation of one broker order by an explicit `client_order_id`.

It intentionally does **not** add DSL syntax, leader/follower semantics, sector semantics, peer-symbol reads, allocation logic, or orchestration policy.

## Implementation boundary

`BrokerEmulator.cancel_client_order(...)`:

- requires an explicit non-empty client identity;
- resolves the identity only against orders already owned by the broker;
- fails closed with `KeyError` when the identity is unknown;
- fails closed with `ValueError` when the identity is ambiguous;
- delegates the actual lifecycle transition to the existing authoritative `cancel(...)` path;
- therefore preserves the existing `ACCEPTED/TRIGGERED -> CANCELED` transition semantics.

No alternative cancellation state machine was introduced.

## Focused regression

`test_stage1_pending_order_cancel.py` covers:

- LIMIT cancellation before a fill;
- STOP cancellation before a trigger;
- STOP_LIMIT cancellation after `TRIGGERED` but before fill;
- unknown identity fail-closed behavior without history mutation;
- ambiguous identity fail-closed behavior.

## Change audit

Relative to pre-tranche HEAD `76134a4c565a52e965980799a76dcba127c00355`, executable head `583c5362ca5ea57e62353a963cd5a2cfb0addfad` changes only:

```text
core/broker.py
+ test_stage1_pending_order_cancel.py
```

No Parser, Runtime, Backtest, multi-symbol Add-on, parent-context provider, chart, or persistence code changed.

## CI classification

GitHub Actions runs for executable head `583c5362ca5ea57e62353a963cd5a2cfb0addfad` completed as failure before any job step was created/executed (`steps=[]`).

Classification: **environment issue**.

No assertion, guard, or product behavior was weakened in response.

## Trust boundary

This tranche is **not trusted yet**. Exact local focused + Full PASS is still required.

Recommended local validation after pull:

```powershell
python -m unittest test_stage1_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Only after both pass should this checkpoint be promoted to trusted and the next micro-tranche begin.

## Next micro-tranche after trust

Add generic Instrument DSL / Backtest integration that maps an explicit DSL cancellation intent to this broker primitive.

That later tranche must remain feature-blind: no `leader`, `follower`, `sector`, peer-symbol or learned-policy concepts may enter Parser/Runtime/Backtest cancellation semantics.
