# Quant DSL Current State

Status: **DSL_CORE_PHASE1_TRUSTED / LIVE_STUDIO_75_FEATURES_TRUSTED / 23_INVARIANTS_TRUSTED / V2_V3_V4_UI_TRUSTED / REMEDIATION_REQUIRED**  
Updated: 2026-08-30 KST

## Recovery

`SESSION_HANDOFF.md` is the primary human-readable recovery authority. Exact user-local PASS evidence and the current `dsl-live-studio` branch outrank stale validation text.

## Main product direction

```text
UI
 -> natural-language / LLM request prompt
 -> human-mediated LLM output
 -> local DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime
 -> BacktestEngine
 -> BrokerEmulator
 -> chart / diagnostics / validation
 -> UI feedback
```

LLM authors DSL text only. Deterministic Parser/Semantic/Runtime/Backtest/Broker remain authoritative.

Current product branch:

```text
dsl-live-studio
```

## Governing architecture

Core DSL remains generic, deterministic, single-instrument and feature-blind where possible. Hard equipment/guards outrank optional adaptive intelligence. Leader/follower, orchestration and learning remain optional sidecars and must not repeatedly reshape Core grammar/runtime/execution/accounting.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Live Studio direct Core path

```text
submitted DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime.compile
 -> BacktestEngine.run
 -> BrokerEmulator
 -> trades / closed trades / diagnostics / metrics
```

Data claims remain explicit:

```text
SYNTHETIC_ENGINE_FIXTURE = deterministic engine verification only
CALLER_SUPPLIED_MARKET   = caller-supplied OHLCV evaluated by Core
```

Caller-supplied does not itself prove real-market authenticity.

## DSL Core Phase 1 completion checkpoint

User-visible Live Studio evidence:

```text
Feature mode
75 total
75 PASS
0 FAIL

Execution-contract mode
23 total
23 PASS
0 FAIL
```

The execution-contract UI initially exposed a JSON serialization defect because `mtf.confirmed_only` correctly produced NaN for the unconfirmed first bucket. The invariant calculation remained valid; the reporting boundary was corrected so non-finite diagnostic values are represented JSON-safely. After that correction, the Live Studio showed 23 / 23 PASS and 0 FAIL.

Therefore the current Phase 1 completion claim is:

```text
registered DSL feature catalog      75 / 75 PASS
registered execution invariants     23 / 23 PASS
Live Studio direct-Core path        TRUSTED
v2 + v3 + v4 invariant UI           TRUSTED
DSL Core Phase 1                     TRUSTED
```

This checkpoint means the currently defined Phase 1 DSL feature surface and its major deterministic execution contracts are complete and verified through the executable catalog. It does not mean every future DSL 2.0 capability is implemented.

## Trusted invariant coverage

### v2

```text
context.exact_binding
context.missing_fail_closed
execution.entry_gate_suppression
execution.next_open_timing
execution.entry_time_window
execution.max_entries_per_day
order.stop_fill
order.stop_limit_fill
order.day_expiry
order.stable_client_cancel
mtf.confirmed_only
```

### v3

```text
order.oco_sibling_cancel
order.gtc_persistence
order.close_long
order.close_short
order.close_position
execution.pending_suppressed_position_occupied
execution.same_bar_reentry
execution.risk_exit_precedence
```

`risk_exit_precedence` is intentionally narrow: current Core demonstrates risk-exit precedence over strategy exit; this is not a generic adaptive hard-guard authority claim.

### v4

```text
order.limit_fill
order.cancel_unknown_fail_closed
execution.take_profit_precedence
execution.trailing_stop
```

## Phase 2 / deferred expansion scope

The following remain outside the Phase 1 completion claim:

```text
partial fills
pyramiding
multi-position accounting
on_tick / on_fill with rollback semantics
tuple / multi-output indicators
bounded loops
user-defined functions
full TA-Lib differential fixture coverage
```

These are Phase 2 expansion items, not reasons to keep reopening the Phase 1 deterministic Core unless explicitly prioritized.

## Immediate next direction

Do not keep adding invariants merely for count growth. The preferred next sequence is:

```text
freeze Phase 1 scope
 -> visually/manual verify representative feature semantics where useful
 -> connect production historical-data adapter/provenance
 -> enrich evaluation UI / chart diagnostics
 -> then decide which Phase 2 language features are actually required
```

New Core grammar/runtime features must be justified by a concrete product need and added in micro-tranches.

## Preserved sidecar assets

Historical CTX/LF/LFREAL research remains preserved but secondary. Do not resume adaptive/leader-follower expansion automatically and do not let sidecar concerns contaminate Core.

## Nonclaims

No synthetic fixture proves profitability. No real-market authenticity is claimed without verified provenance. No live trading readiness, automatic leader selection/allocation, validated deployment gating, or repository-wide compliance PASS is claimed.
