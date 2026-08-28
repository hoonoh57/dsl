# LF1 Leader / Follower Relation Evidence — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / OBSERVATION_ONLY / 2026-08-28 KST**

## Trusted predecessor

CTXINT3 received operator validation at exact checkout:

```text
7f77694658d7155806e97bdafcc543e2c7bfeae8
Ran 7 tests in 0.150s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore `next_open` MARKET gating from prior-completed-bar context is trusted at that exact SHA.

## Purpose

LF1 is the first deliberately narrow implementation of reusable leader/follower intelligence for the multi-symbol Add-on.

Human meaning:

```text
static explicit sector/group universe
 -> MSA1 point-in-time symbol evidence
 -> MSA2 current leader + persistence/spread evidence
 -> identify one qualified leader
 -> measure which followers react after that leader
 -> report follow rate and lag separately
```

This is designed to support later stories such as:

```text
leading sector
 -> leader stock rebounds
 -> historically reliable follower begins its lagged response
 -> create conditional pending intent
 -> cancel if leader/group reverses before fill
```

LF1 itself does not create or cancel orders.

## Executable

```text
core/multi_symbol_leader_follower_relation.py
test_stage1_multi_symbol_leader_follower_relation.py
```

Schemas/policy:

```text
multi_symbol_leader_follower_relation/v1
multi_symbol_leader_follower_relation_policy/v1
OBSERVATION_ONLY_EXPLICIT_LEADER_PERSISTENCE_LAGGED_FOLLOW_RATE_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

## V1 leader rule

V1 intentionally allows one explicit leader only.

The current MSA2 metric leader becomes a qualified leader only when both are satisfied:

- leader persistence across the declared MSA2 lookback is at least the declared minimum;
- the current leader/follower metric spread is at least the declared minimum.

There is no hidden universal leader score.

## V1 follower rule

A leader impulse is an explicit direction-normalized metric change above `leader_impulse_threshold`.

For every follower, LF1 searches the next `1..max_lag_points` transitions for a direction-normalized response above `follower_response_threshold`.

It records separately:

```text
observable_impulse_count
matched_response_count
follow_rate
mean_lag_points
mean_response_oriented_delta
```

Missing/ineligible response windows are not silently counted as failures. A leader impulse too close to the end of the available timeline is marked censored and excluded from the follow-rate denominator.

## Explicit selection axes

LF1 exposes independent orderings for:

```text
follow_rate
mean_lag_points
current group metric
```

For the first minimal operating slice, `top_follow_rate_follower` means exactly the highest qualified follower on the explicit follow-rate axis, with deterministic symbol tie-break. It is not an opaque weighted score and it has no deployment authority.

## Authority boundary

LF1 declares:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

It does not:

- publish `allowed_symbols` / `blocked_symbols`;
- allocate capital;
- create an entry gate;
- publish parent context;
- call Backtest/Runtime/Broker/provider/network/database code;
- submit or cancel orders.

Leader/follower intelligence remains an optional multi-symbol Add-on concern, not Instrument DSL grammar.

## Regression coverage

Focused regression covers:

- stable leader qualification by persistence and spread;
- one-bar and two-bar lagged follower response rates;
- explicit top follower on follow-rate axis;
- no hidden universal score or execution authority;
- censored tail impulses excluded from follower failure counts;
- snapshot input order determinism;
- MAX and MIN metric direction normalization;
- single-leader/minimum-history fail-closed boundary;
- no execution/provider/network imports.

## Next tranche after trust

After LF1 focused + Full validation, the next independent tranche is generic DSL pending-order cancellation. The intended boundary is a small reusable order primitive such as cancel-by-explicit-client-id, not leader/follower concepts inside DSL.

Only after both LF1 relation evidence and generic cancel semantics are trusted should a later orchestration tranche compose:

```text
leader/follower evidence
 + local follower setup
 + pending order intent
 + leader/group invalidation
 -> explicit cancellation
```

## Nonclaims

Do not claim yet:

- trusted Full PASS for LF1;
- validated profitable leader/follower edge;
- production leader/follower stock selection;
- pending-order cancellation semantics in DSL;
- live trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_multi_symbol_leader_follower_relation.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
