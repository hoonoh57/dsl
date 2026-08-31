# Three-Axis Bridge Contracts

Status: **CONTRACT ROOT / V1 DESIGN PENDING**

Only versioned Request -> Response contracts may cross axis boundaries.

Planned contract families:

```text
three_axis.common/v1
axis1.execution/v1
axis2.selection/v1
axis3.monetization/v1
```

Expected flow:

```text
AXIS 2 -> CandidateSetResponse
AXIS 3 -> StrategyExecutionRequest
AXIS 1 -> ExecutionResponse + projections
AXIS 3 -> Monetization/ValidationResponse
```

No contract may expose an axis's private DB/state/runtime object.

AXIS 2 selection inputs should refer to immutable point-in-time feature snapshots rather than request-time Instrument DSL calculations.

See:

- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
- `DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md`
- `DSL_FROZEN_CORE_MIGRATION_POLICY.md`
