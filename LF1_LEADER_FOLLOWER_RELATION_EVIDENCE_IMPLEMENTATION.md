# LF1 Leader / Follower Relation Evidence — Implementation Checkpoint

Status: **TRUSTED FULL PASS / OBSERVATION_ONLY / 2026-08-28 KST**

## Trusted exact checkpoint

LF1 received operator validation at exact checkout:

```text
5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
Ran 7 tests in 0.058s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

This exact SHA is the trusted LF1 executable checkpoint.

## Purpose

LF1 is the first deliberately narrow implementation of reusable leader/follower intelligence for the multi-symbol Add-on.

Human meaning:

```text
static explicit sector/group universe
 -> point-in-time symbol evidence
 -> identify one qualified leader
 -> measure which followers react after that leader
 -> report follow rate and lag separately
```

This supports later stories such as:

```text
leading sector
 -> leader stock rebounds
 -> historically reliable follower begins its lagged response
 -> create conditional pending intent
 -> cancel if leader/group reverses before fill
```

LF1 itself does not create or cancel orders.

## V1 leader rule

V1 intentionally allows one explicit leader only. The current group metric leader is qualified only when both are satisfied:

- leader persistence across the declared lookback exceeds the declared minimum;
- current leader/follower metric spread exceeds the declared minimum.

There is no hidden universal leader score.

## V1 follower rule

A leader impulse is a declared direction-normalized metric change above a threshold. For every follower, LF1 searches the next `1..N` points for a same-direction response above its declared threshold.

It records separately:

```text
observable_impulse_count
matched_response_count
follow_rate
mean_lag_points
mean_response_oriented_delta
```

Unavailable trailing response windows are censored rather than counted as follower failures.

## Explicit selection axes

LF1 exposes separate orderings for:

```text
follow_rate
mean_lag_points
current group metric
```

`top_follow_rate_follower` means only the highest qualified follower on the explicit follow-rate axis with deterministic tie-break. It is observation evidence, not deployment authority.

## Authority boundary

LF1 remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

It does not publish allowed/blocked symbols, allocate capital, create entry gates, publish parent context, call execution/provider/network/database code, or submit/cancel orders.

Leader/follower intelligence remains an optional multi-symbol Add-on concern, not Instrument DSL grammar.

## Regression coverage

The trusted focused regression covers stable leader qualification, lagged follower response rates, explicit top-follower selection, censored tail handling, deterministic ordering, MAX/MIN normalization, fail-closed minimum-history boundaries and the no-execution/provider/network boundary.

## Next tranche after trust

The next independent tranche is **generic DSL pending-order cancellation** by explicit order/client identity with deterministic Backtest/Broker semantics.

Only after both LF1 relation evidence and generic cancel semantics are independently trusted should a later orchestration tranche compose:

```text
leader/follower evidence
 + local follower setup
 + pending order intent
 + leader/group invalidation
 -> explicit cancellation
```

## Nonclaims

LF1 trust does **not** establish profitable leader/follower edge, production stock-selection authority, pending-order cancellation semantics, live-trading readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
