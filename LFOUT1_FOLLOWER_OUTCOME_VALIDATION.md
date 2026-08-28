# LFOUT1 Follower Outcome Validation — Implementation Checkpoint

Status: **TRUSTED FULL PASS / EVIDENCE_ONLY / 2026-08-29 KST**

## Trusted checkpoint

Executable checkpoint after the MAE-direction fix:

```text
ca4d5309a658de02f970e341bbf86ad87ab327ae
```

User-local validation at that checkout:

```text
Ran 7 tests in 0.003s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

LFOUT1 is therefore trusted Full-green at that exact executable checkpoint.

## Purpose

LFOUT1 measures whether trusted LF2 observation-only intent evidence is associated with bounded frozen outcomes across explicit TRAIN / VALIDATION / OOS / HARSH partitions.

It does not replay tactics, call the execution engine, submit/cancel orders, publish a deployment gate, select stocks, allocate capital, or acquire operational authority.

## Exact join boundary

LFOUT1 consumes:

```text
trusted LF2 frozen evidence
+ separately frozen outcome rows
-> exact evidence_hash join
```

Coverage must match exactly. There is no nearest match, fill-forward, interpolation, silent default, or provider call.

## Explicit outcome axes

No hidden score is used. The declared axes are:

- ARM forward-return edge versus non-ARM evidence;
- ARM MFE edge versus non-ARM evidence;
- ARM MAE regression versus non-ARM evidence;
- CANCEL avoided-loss magnitude when cancel evidence exists;
- holdout ARM return-edge regression versus TRAIN.

TRAIN, VALIDATION and OOS are required exactly once; at least one HARSH partition is required with an explicit `adverse_reason`.

All partitions must use one LF2 `policy_hash`, and evidence identities must be globally disjoint.

## Initial validation defect

The initial executable checkpoint:

```text
f95d15f2f66533a616db5a86df9cbe9e1f7c418b
```

failed two focused tests because `mae_pct` sign direction was interpreted backwards.

Classification:

```text
product defect — signed MAE direction bug
```

`mae_pct` is represented as a signed adverse excursion where a more negative value is worse. The initial implementation computed regression as:

```text
max(0, arm_mae - non_arm_mae)
```

which incorrectly treated a less-negative ARM MAE as worse. The correct regression is:

```text
max(0, non_arm_mae - arm_mae)
```

Only product logic was corrected. The tests and validation thresholds were not weakened.

## Authority boundary

```text
mode = EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
```

A PASS means only that the supplied frozen outcome evidence satisfies the declared comparison contract. It does not prove production profitability or authorize live trading.

## Focused regression

Seven tests cover:

1. partitioned PASS remains evidence-only;
2. exact outcome coverage is mandatory;
3. holdout return-edge regression rejects;
4. cancel avoided-loss is an explicit axis;
5. TRAIN/VALIDATION/OOS/HARSH contract;
6. partition order does not alter identity;
7. LF2 policy mismatch fails closed.

## Mutation boundary

LFOUT1 did not modify Parser, Semantic, Runtime, Backtest, Broker, provider, Chart product source, DSL grammar, allocation, ranking, or adaptive-learning authority.

## Nonclaims

LFOUT1 does not establish a profitable leader/follower edge, deployment authority, automatic selection, allocation, adaptive learning authority, or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative.
