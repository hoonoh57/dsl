# CTXINT3 Validated Context Next-Open Timing Integration — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / NEXT_OPEN MARKET ONLY / 2026-08-28 KST**

## Trusted predecessor

CTXINT2 received operator validation at exact checkout:

```text
b3b547b9d2d0eaeee654790243f031a3bbb88198
Ran 7 tests in 0.106s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore blocking-only `bar_close` integration through the existing Backtest `entry_gate` seam is trusted at that exact SHA.

## Purpose

CTXINT3 defines the causal timing rule for `signal_mode=next_open` without modifying BacktestEngine or BrokerEmulator.

Human meaning:

```text
bar t closes
 -> tactic trigger / local guard / validated parent context are all known at t
 -> if all allow, that permission may be used for a MARKET entry at bar t+1 open
```

The not-yet-completed context of bar t+1 may not be used to decide the t+1 open entry.

## Executable

```text
core/tactical_context_integration_scope.py
core/tactical_context_next_open_integration.py
test_stage1_tactical_context_next_open_integration.py
```

CTXINT3 also hardens the current CTXINT2 source so validated-context integrations reject deferred entry orders until a later contract defines their signal-time/fill-time semantics.

## Next-open timing rule

CTXINT3 first builds the already-trusted CTXINT1 point-in-time eligibility sequence. It then shifts that evidence one bar forward before passing it to the existing Backtest entry gate.

Example:

```text
09:05 completed-bar permission
 -> may govern 09:10 MARKET open entry

09:10 bar context
 -> may NOT rescue or alter that 09:10 open decision
```

The first market bar has no prior completed-bar permission and is always closed to `next_open` entry through this adapter.

Output records both the applied gate and its source time:

```text
entry_gate[fill_bar]
gate_source_times[fill_bar] = prior completed bar time
context_timing = PRIOR_COMPLETED_BAR_ONLY
can_use_fill_bar_context_for_next_open = false
```

## Entry-only authority

CTXINT3 preserves the same narrow authority as CTXINT2:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

An allowed next-open entry still uses existing Backtest/Broker behavior. Exits are not gated by parent context.

## Deferred-order fail-closed boundary

`LIMIT`, `STOP` and `STOP_LIMIT` entry orders are deliberately rejected by the validated-context integration scope.

Reason: a deferred order may be submitted from one signal-time context and fill several bars later. The project has not yet authorized whether that order should:

- retain the original signal-time permission;
- require the latest completed context to remain allowed before fill;
- be canceled when context changes;
- or use another explicit policy.

Until that contract is separately validated, deferred orders are not accepted by CTXINT2 or CTXINT3.

This is a scope hardening, not a change to BrokerEmulator or the general DSL order capability.

## Exact identity requirements

CTXINT3 requires:

- exact validated tactic hash equal to CTXDEP1 policy tactic identity;
- exact DEPLOYMENT ParentContextFrame and matching registry;
- exact market instrument equal to frame target symbol;
- exact full market/frame timeline equality;
- explicit tactic-trigger and local-hard-guard evidence;
- `signal_mode=next_open`;
- MARKET entry orders only.

No nearest-time lookup, fill-forward, interpolation or fill-bar lookahead is allowed.

## Regression coverage

The focused regression verifies:

- prior completed signal-bar context governs the next open;
- fill-bar context cannot rescue a blocked signal-bar decision;
- a failed signal-bar local hard guard cannot be bypassed;
- first bar has no prior authority;
- deterministic gate/source-time identity;
- candidate/symbol/timeline/signal-mode mismatch fail-close;
- deferred entry orders fail closed in both CTXINT2 and CTXINT3;
- no direct Broker/Runtime/provider-calculation calls are added.

## Mutation boundary

CTXINT3 adds a sidecar adapter, shared order-scope guard and focused regression. It does not modify Parser grammar, Runtime semantics, BacktestEngine implementation, BrokerEmulator, PCTX provider calculation or CTXVAL1/CTXDEP1 adjudication.

The only CTXINT2 source change is the explicit MARKET-only deferred-order guard. The trusted CTXINT2 checkpoint remains `b3b547...`; the hardened current source must be revalidated with CTXINT3 before being treated as a new executable checkpoint.

## Nonclaims

Do not claim yet:

- trusted Full PASS for CTXINT3;
- validated deferred-order context semantics;
- production/live parent-context gating;
- empirical profitability of a real GROUP context policy;
- automatic cross-symbol selection/allocation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_next_open_integration.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
