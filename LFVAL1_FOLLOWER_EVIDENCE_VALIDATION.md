# LFVAL1 Follower Evidence Validation — Implementation Checkpoint

Status: **TRUSTED FULL PASS / EVIDENCE_ONLY / 2026-08-28 KST**

## Purpose

LFVAL1 validates frozen LF2 observation-only evidence across explicit TRAIN / VALIDATION / OOS / HARSH partitions.

It does not replay tactics, calculate profitability, submit/cancel orders, publish deployment gates, or acquire operational authority.

## Trusted checkpoint

Executable checkpoint:

```text
283af6e8ed046324698b9ff49e95f5044131f453
```

Exact user-local trust evidence:

```text
Ran 7 tests in 0.002s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore LFVAL1 is trusted Full-green at that executable checkpoint.

## Validation axes

Explicit no-hidden-score axes:

- selection qualified rate;
- ARM rate;
- hard-guard pass rate;
- relation-valid rate;
- invalid active pending cancellation safety.

Every partition must pass declared independent tolerances. TRAIN, VALIDATION and OOS are required exactly once; at least one HARSH partition is required with `adverse_reason`.

Unsafe ARM evidence fails closed. An active pending state that is invalidated by relation/setup/hard-guard failure must already be `CANCEL_PENDING` evidence or validation fails closed.

All partitions must use one LF2 `policy_hash`, and evidence identities must be globally disjoint.

## Authority boundary

```text
mode = EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
```

A PASS means only that the declared observation-evidence contract remains stable across the supplied partitions. It does not prove a profitable edge or authorize trading.

## Executable files

```text
core/multi_symbol_follower_validation.py
test_stage1_multi_symbol_follower_validation.py
```

No Parser, Semantic, Runtime, Backtest, Broker, provider or Chart product source was changed.

## Focused regression

Seven tests cover:

1. partitioned PASS remains evidence-only;
2. explicit holdout regression rejection;
3. invalid active pending requires CANCEL_PENDING;
4. unsafe ARM rejection;
5. TRAIN/VALIDATION/OOS/HARSH partition contract;
6. partition order does not alter validation identity;
7. LF2 policy mismatch fails closed.

## Next boundary

LFVAL1 being trusted does not grant deployment authority.

The next authorized question is whether a separate, bounded outcome/backtest evidence tranche should be attached to this already-trusted observation-only evidence. That tranche must remain separate from Core DSL and must not infer deployment permission merely from LFVAL1 PASS.

Do not open automatic stock selection, allocation, adaptive learning, new DSL grammar, or live execution authority as a consequence of this checkpoint.

## Nonclaims

LFVAL1 does not establish profitable leader/follower edge, deployment authority, automatic stock selection, allocation, adaptive learning authority, or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative.
