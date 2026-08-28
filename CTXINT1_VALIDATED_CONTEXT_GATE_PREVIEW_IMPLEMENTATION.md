# CTXINT1 Validated Context Gate Preview — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / PREVIEW_ONLY / 2026-08-28 KST**

## Trusted predecessor

CTXDEP1 received operator validation at exact checkout:

```text
804baea25f29d1c77f2984d67e37dbb5ebb1160e
Ran 6 tests in 0.028s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore validated context deployment-policy evidence is trusted Full-green at that SHA.

## Purpose

CTXINT1 verifies the final composition rule **before** any operational entry-gate wiring is allowed.

Human meaning:

```text
The tactic must already want to enter,
and its local hard safety rules must already pass,
and the separately validated parent-context policy must allow it.
Only then may the preview say that entry remains eligible.
```

A parent-context policy can remove an existing local opportunity. It cannot create one.

## Executable

```text
core/tactical_context_gate_preview.py
test_stage1_tactical_context_gate_preview.py
```

Schema/policies:

```text
validated_context_entry_gate_preview/v1
TACTIC_TRIGGER_AND_LOCAL_HARD_GUARD_AND_VALIDATED_CONTEXT_PERMISSION_NO_ENTRY_CREATION
PREVIEW_ONLY_NOT_INSTALLED_AS_BACKTEST_ENTRY_GATE_OR_BROKER
```

## Inputs

CTXINT1 requires:

- one validated CTXDEP1 policy-evidence object;
- one exact `DEPLOYMENT` `ParentContextFrame`;
- the matching registered parent-feature registry;
- the exact validated tactic identity;
- the exact full frame timeline;
- explicit per-time tactic-trigger evidence;
- explicit per-time local hard-guard pass evidence.

The validated feature ID and manifest hash must exist in the frame/registry and must describe the same layer, context and feature key used by the validated policy rule.

## Composition rule

For every exact target time:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated context permission
```

CTXINT1 records all three inputs and the resulting eligibility. The output explicitly states:

```text
can_create_entry_without_local_opportunity = false
operational_authority = false
```

This is evidence of composition semantics, not an installed gate.

## Exact-time / identity rules

The requested timeline must exactly equal the entire DEPLOYMENT frame timeline. No nearest-time, fill-forward, interpolation or partial timeline is accepted.

For each point CTXINT1 retains:

```text
context_hash
binding_hash
deployment decision_hash
```

The top-level preview retains:

```text
frame_hash
registry_hash
policy_hash
policy_evidence_hash
feature_id
required_manifest_hash
preview_hash
```

## What CTXINT1 deliberately does not do

CTXINT1 does not modify or call the execution path. It does not install an entry gate and does not submit orders.

It does not change:

```text
Parser / Semantic / Runtime
BacktestEngine
BrokerEmulator
PCTX provider calculation
CTXVAL1 validation adjudication
CTXDEP1 promotion semantics
existing E8 deployment-policy decision semantics
```

## Regression coverage

The focused regression verifies:

- exact AND-composition of tactic trigger, local hard guard and validated context permission;
- context permission cannot create an entry when the tactic trigger is false;
- context permission cannot bypass a failed local hard guard;
- context miss only removes an existing local opportunity;
- OBSERVED frame rejection;
- tactic / manifest / timeline / boolean-evidence mismatch fail-close;
- deterministic preview identity;
- absence of Backtest/Runtime/Broker/provider-calculation imports in the preview module.

## Nonclaims

Do not claim yet:

- trusted Full PASS for CTXINT1;
- operational parent-context entry gating;
- actual Broker order suppression by CTXINT1;
- empirical profitability of a real GROUP context policy;
- automatic cross-symbol selection/allocation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_gate_preview.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
