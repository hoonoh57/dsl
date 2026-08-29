# Quant DSL Current State

Status: **DSL_LIVE_STUDIO_DIRECT_CORE_TRUSTED / FEATURE_CATALOG_V1_TRUSTED / FEATURE_CATALOG_V2_TRUSTED / V2_UI_INTEGRATION_TRUSTED / FEATURE_CATALOG_V3_REMOTE_UNVALIDATED / REMEDIATION_REQUIRED**  
Updated: 2026-08-29 KST

## Recovery

`SESSION_HANDOFF.md` is the primary human-readable recovery authority for abrupt session changes. On `세션복구`, read it first, then reconcile with newer project conversation evidence and the current GitHub branch head.

Exact user-local focused + Full PASS evidence outranks stale validation text. New remote executable/test commits without local PASS remain `REMOTE_UNVALIDATED`.

## Main product direction

The current main product axis is:

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

Legacy `app_ui.py` is not the product-performance authority. `ux-max-ui` is preserved as a workflow/UI experiment. Current product work is on branch:

```text
dsl-live-studio
```

## Governing architecture

Core DSL remains generic, deterministic, single-instrument and feature-blind where possible. Hard equipment/guards outrank optional adaptive intelligence. Leader/follower, sector/market orchestration and learning remain sidecar/context concerns and must not repeatedly reshape Core grammar/runtime/execution/accounting.

Research assets LF1/LF2/LFVAL/LFOUT/LFREAL remain preserved but are not the active main development axis unless explicitly requested.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Live Studio direct Core path

```text
submitted DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime.compile
 -> BacktestEngine.run
 -> BrokerEmulator
 -> executions / closed trades / diagnostics / metrics
```

The Live Studio must not silently substitute a fixed legacy demo strategy.

Data claims remain explicit:

```text
SYNTHETIC_ENGINE_FIXTURE = deterministic engine verification only
CALLER_SUPPLIED_MARKET   = caller-supplied OHLCV evaluated by Core
```

Caller-supplied does not itself prove real-market authenticity.

## Trusted Live Studio checkpoints

### Direct Core + Feature Catalog v1

```text
c9c5122d799d6c0cb30d45eb37890d16b582d322
```

User-local evidence:

```text
test_live_studio_core_path.py
Ran 5 tests in 0.019s
OK

test_live_studio_feature_catalog.py
Ran 5 tests in 1.198s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

v1 verifies registered `FUNCTION_SPECS` plus core grammar/order examples through real Parser/Semantic/Backtest.

### Feature Catalog v2 invariant harness

Trusted executable baseline:

```text
5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
```

User-local evidence:

```text
test_live_studio_feature_invariants.py
Ran 5 tests in 0.039s
OK

test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

test_live_studio_feature_catalog.py
Ran 5 tests in 1.249s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

Trusted v2 invariants:

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

### v2 invariant UI integration

Trusted checkpoint:

```text
089b727204088f5ac5dbd6ac041e470f4df2a8c4
```

User-local evidence:

```text
test_live_studio_invariant_ui.py
Ran 4 tests in 0.025s
OK

test_live_studio_feature_invariants.py
Ran 5 tests in 0.038s
OK

test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

test_live_studio_feature_catalog.py
Ran 5 tests in 1.258s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

## Current work — Feature Catalog v3

Status:

```text
REMOTE_UNVALIDATED
```

Executable checkpoint created before recovery-doc updates:

```text
72013531fca28ea832808a0d3a89f12da3607762
```

The branch head may be newer because documentation commits can follow. Do not treat newer remote executable/test changes as trusted without local PASS.

v3 invariant set:

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

`risk_exit_precedence` is intentionally precise. Current Core directly exposes STOP/TP/trailing-before-strategy-exit priority; do not overclaim a generic hard-guard precedence contract unless separately demonstrated.

## Immediate next gate

```powershell
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_feature_invariants_v3.py
python -m unittest test_live_studio_feature_invariants.py
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If all PASS:

```text
promote v3 trusted
 -> optionally integrate v3 into Live Studio invariant UI
 -> continue closing the DSL execution-contract matrix
 -> only then advance to production historical adapter/provenance and richer product UI/LLM authoring
```

If any fail, classify first:

```text
test defect
product defect
contract mismatch / authority drift
environment issue
unknown
```

Do not weaken guards, semantic rules, or assertions merely to make tests pass.

## Preserved trusted sidecar checkpoints

These remain valid assets but are secondary to current Live Studio work:

```text
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
CTXINT3           7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1               5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
GCANCEL1          583c5362ca5ea57e62353a963cd5a2cfb0addfad
GCANCEL2          3cd5731a1702f7bfb11878dfd6e34339baa5f163
VSLICE1           72445456e86b695dc7288ab3a48856fa560463dd
LF2               5a6e6e53c089ed108d19fa729cba84874e856388
LFVAL1            283af6e8ed046324698b9ff49e95f5044131f453
LFOUT1            ca4d5309a658de02f970e341bbf86ad87ab327ae
LFREAL1           5aa1da3268f1f3e031aa6d607a4d3a5921f03e58
LFREAL2           10861c232d03937c5ae77e2be32cd1873a5ff977
LFREAL3           ab4d798c6648ee382e779af81e759cd11bf1cb13
```

Do not resume LFREAL architecture expansion merely because these docs exist.

## Nonclaims

No synthetic fixture proves profitability. Caller-supplied data does not automatically prove vendor/source authenticity. No live trading readiness, automatic leader selection/allocation, validated deployment gating, or repository-wide compliance PASS is claimed.
