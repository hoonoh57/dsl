# AXIS 3 — Strategy Monetization

Status: **NEW IMPLEMENTATION ROOT / NOT YET MIGRATED**

This directory owns Strategy CRUD, lineage, comparison, validation and promotion/rejection workflows.

Rules:

- Do not implement DSL Parser/Runtime here.
- Do not implement cross-sectional selection here.
- Do not calculate chart-native values here.
- Consume AXIS 2 `CandidateSetResponse` and invoke AXIS 1 only through versioned bridge contracts.
- Preserve immutable strategy baselines and separate Strategy CRUD from Feature Catalog and Condition CRUD.

Planned internal layout:

```text
strategies/
crud/
evaluation/
tests/
```

See:

- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
- `DSL_FROZEN_CORE_MIGRATION_POLICY.md`
