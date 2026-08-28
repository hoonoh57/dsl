# CTXINT2 Validated Context Backtest Entry Gate Integration — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / BACKTEST ENTRY-SUPPRESSION ONLY / 2026-08-28 KST**

## Trusted predecessor

CTXINT1 received operator validation at exact checkout:

```text
81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
Ran 7 tests in 0.129s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the non-operational composition rule is trusted: parent context may only remove an existing local entry opportunity.

## Purpose

CTXINT2 is the first executable connection of validated parent-context permission to the existing Backtest entry restriction seam.

Human meaning:

```text
validated tactic
 + exact DEPLOYMENT context
 + local tactic-trigger evidence
 + local hard-guard evidence
 -> CTXINT1 block-only preview
 -> existing Backtest entry_gate
 -> BrokerEmulator remains execution authority
```

No new order engine or execution semantics are introduced.

## Executable

```text
core/tactical_context_backtest_integration.py
test_stage1_tactical_context_backtest_integration.py
```

Schema/policy:

```text
validated_context_backtest_entry_gate/v1
VALIDATED_CONTEXT_BLOCK_ONLY_EXISTING_BACKTEST_ENTRY_GATE_BAR_CLOSE_V1
```

## Identity and causal requirements

CTXINT2 requires:

- a validated `TacticCandidate` whose exact candidate hash equals the CTXDEP1 policy tactic identity;
- trusted CTXDEP1 policy evidence;
- exact DEPLOYMENT ParentContextFrame and matching registry;
- market instrument equal to frame target symbol;
- market timeline exactly equal to the entire frame timeline;
- explicit tactic-trigger and local hard-guard evidence;
- `signal_mode=bar_close` in v1.

`next_open` is deliberately rejected until its signal-time/fill-time context semantics receive a separate validated tranche.

## Entry-only authority

The adapter derives the Backtest gate only from CTXINT1 effective-entry eligibility.

It declares:

```text
gate_authority = ENTRY_SUPPRESSION_ONLY
can_create_entry = false
can_bypass_local_hard_guard = false
can_block_exit = false
broker_order_authority = false
execution_authority = BrokerEmulator
```

The adapter calls the already-trusted `BacktestEngine.run(..., entry_gate=...)` seam. It does not call Broker APIs directly and does not modify Backtest, Runtime, Parser, Semantic or Broker code.

## Regression coverage

The focused regression verifies:

- a validated context miss suppresses an entry that exists in the ungated baseline;
- an allowed entry still exits normally even when the context gate is false on the exit bar;
- a failed local hard guard cannot be bypassed by context allow;
- exact candidate/symbol/timeline identity fail-close;
- v1 rejects `next_open`;
- deterministic gate and Backtest result identity;
- the Backtest diagnostic confirms the existing higher-layer gate was supplied;
- execution authority remains BrokerEmulator;
- the integration module has no direct Broker/provider calculation calls.

## Mutation boundary

CTXINT2 adds a new integration sidecar and regression. It does **not** modify:

```text
Parser / Semantic / Runtime
BacktestEngine implementation
BrokerEmulator
PCTX provider/orchestration
MSA publication/analysis
CTXVAL1 adjudication
CTXDEP1 promotion semantics
CTXINT1 preview semantics
```

## Nonclaims

Do not claim yet:

- trusted Full PASS for CTXINT2;
- production/live parent-context gating;
- validated `next_open` or pending-order context semantics;
- empirical profitability of real GROUP context;
- automatic cross-symbol allocation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_backtest_integration.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
