# LF2 Follower Pending Intent Orchestration — Implementation Checkpoint

Status: **REMOTE_UNVALIDATED_AFTER_FIX / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / 2026-08-28 KST**

## Purpose

LF2 is the first deliberately narrow orchestration layer after trusted LF1 relation evidence and trusted generic pending-order cancellation.

It remains an optional multi-symbol Add-on concern. It does not add Instrument DSL grammar, change Backtest/Broker execution semantics, publish parent context, or gain execution authority.

## Inputs

LF2 consumes only already-frozen evidence/state:

```text
LF1 OBSERVATION_ONLY relation result
+ explicit local follower symbol
+ deterministic local setup pass/fail
+ deterministic local hard-guard pass/fail
+ explicit relation_still_valid boolean
+ pending active state / stable client identity when already armed
```

LF2 requires the LF1 result to remain `mode=OBSERVATION_ONLY` and `operational_authority=false`.

## Output contract

LF2 emits one observation-only intent evidence state:

```text
ARM_PENDING
HOLD
HOLD_PENDING
CANCEL_PENDING
```

It never submits or cancels an order itself.

When no pending order exists, ARM is allowed only when all are true:

```text
LF1 selected follower is qualified
AND local symbol == selected follower
AND local setup passes
AND hard guard passes
AND relation_still_valid
```

When a pending order already exists, any of the following produces `CANCEL_PENDING` evidence:

```text
relation selection invalid
OR local setup invalid
OR hard guard failed
OR relation invalidated
```

Hard guard therefore has deterministic veto authority over ARM and produces cancellation intent for a still-live pending order. Learning/adaptive authority is not involved.

## Stable identity

ARM produces a deterministic client identity from:

```text
relation_result_hash
+ LF2 policy_hash
+ decision as_of
+ selected follower symbol
```

CANCEL never invents a new identity; an already-active pending order must provide its explicit existing client identity or LF2 fails closed.

## Authority boundary

The module declares:

```text
mode = OBSERVATION_ONLY
operational_authority = false
execution_authority = false
```

It has no execution, provider, network, database or persistence calls and emits no `broker_order`, `entry_gate`, `allocation`, `allowed_symbols` or `blocked_symbols` field.

## Initial executable checkpoint and local failure

Initial executable checkpoint:

```text
14bf03f1f9473a607d4330e4d06f9d0ef9bdd219
```

User-local focused result:

```text
Ran 6 tests in 0.002s
FAILED (failures=1)
```

Full verification also failed because the same focused contract test was included in the Full boundary.

Failure classification: **product defect (source-level contract defect)**.

The authority-boundary regression intentionally rejects forbidden execution/provider tokens anywhere in the Add-on source. The module docstring named concrete forbidden execution classes while explaining that it did not call them. Runtime behavior had no execution-authority path, but the source still violated the explicit source-level boundary contract. The test was therefore correct and was not weakened.

## Fix checkpoint

Fixed executable checkpoint:

```text
5a6e6e53c089ed108d19fa729cba84874e856388
```

Fix scope:

```text
core/multi_symbol_follower_pending_orchestration.py
```

Only the module docstring was neutralized to describe the boundary generically. No orchestration logic, policy, hashing, identity, intent decision, Parser, Semantic, Runtime, Backtest, Broker or provider behavior changed.

Executable files in LF2 remain:

```text
core/multi_symbol_follower_pending_orchestration.py
test_stage1_multi_symbol_follower_pending_orchestration.py
```

## Focused regression

The focused test covers:

- qualified selected follower -> stable deterministic `ARM_PENDING` identity;
- explicit relation invalidation -> `CANCEL_PENDING` with the existing identity;
- hard guard failure -> blocks new ARM and cancels active pending intent;
- unselected/unqualified follower cannot ARM;
- authority/identity mismatches fail closed;
- no execution/provider/network/persistence authority in the module.

## Remote CI classification

GitHub Actions for the pre-fix LF2 executable checkpoint failed before job steps were created (`steps=null`).

Classification: **environment issue**.

That remote infrastructure failure is independent from the later user-local source-contract failure above.

## Local trust gate after fix

```powershell
python -m unittest test_stage1_multi_symbol_follower_pending_orchestration.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Only after both pass locally at or after fix checkpoint `5a6e6e53c089ed108d19fa729cba84874e856388` may LF2 become trusted.

## Nonclaims

LF2 does not establish profitable leader/follower edge, production stock selection, validated deployment gating, automatic allocation, live broker behavior or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.
