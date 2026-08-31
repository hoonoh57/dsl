# Step 5-5 Bounded Loops Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## Result

Bounded-loop v1 is accepted.

User-local evidence:

```text
tests/test_axis1_bounded_loops.py = Ran 7 / OK
tests/test_axis1_multi_output.py = Ran 8 / OK
tests/test_frozen_legacy_core_guard.py = Ran 1 / OK
```

Earlier regression evidence in the same Step 5-5 validation tranche:

```text
test_axis1_user_functions.py = OK
test_axis1_generic_projection.py = OK
test_axis1_capability_metadata.py = OK
```

## Accepted contract

```text
compile-time integer range only
maximum 64 iterations
user-function local accumulator scope only
no runtime loop authority
no while/break/continue/dynamic bound
no nested control block in loop v1
source line count preserved
expansion size fail-closed
```

## Defect discovered during validation

The first validation exposed a pre-existing Step 5-1 `ta.bbands` multi-output lowering mismatch for input series with warmup NaNs.

Root cause was classified as `FEATURE_DEFECT`, not a bounded-loop defect.  The final correction preserves the existing `CoreTALib.bbands` component-specific behavior:

```text
middle -> existing SMA semantics
upper/lower deviation -> NaN while the direct std window contains NaN
```

Assertions and expected values were not weakened. Frozen legacy `core/` was not modified.

## Gate

Step 5-5 is complete. Step 5-6 `on_tick / on_fill commit/rollback` may begin.
