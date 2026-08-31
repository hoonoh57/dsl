# Step 5-6 Intrabar Lifecycle Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

Scope:

```text
on_tick / on_fill provisional state lifecycle
begin_bar -> ordered provisional events -> commit_bar | rollback_bar
```

User-local validation:

```text
test_axis1_intrabar_lifecycle.py = OK
test_axis1_bounded_loops.py = OK
test_axis1_user_functions.py = OK
test_axis1_multi_output.py = OK
test_axis1_generic_projection.py = OK
test_frozen_legacy_core_guard.py = OK
```

Accepted contract:

```text
on_tick/on_fill state mutation is provisional until commit
committed state is unchanged before commit
rollback restores the last committed snapshot exactly
commit alone advances revision
failed event rolls back atomically to the pre-event provisional snapshot
handler may mutate declared state only
handler function/order/provider/context/loop access remains prohibited
batch backtest without an intrabar event tape remains fail-closed
```

Protection evidence:

```text
frozen legacy core unchanged
migrated Parser/Semantic/Runtime/Broker not directly modified for this feature
no partial-fill or pyramiding behavior was pulled forward into Step 5-6
```

Next authority:

```text
Step 5-7 partial fills / partial exits
```
