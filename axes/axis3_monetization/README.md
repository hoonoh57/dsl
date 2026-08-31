# AXIS 3 — Strategy Monetization

Status: **ACTIVE IMPLEMENTATION ROOT / VERSIONED ARTIFACTS**

This directory owns product-level Condition/Strategy artifact CRUD, lineage, comparison, promotion/rejection/archive state, and deterministic strategy-run orchestration.

Boundary clarification:

- AXIS 2 still owns Condition **selection semantics**: immutable snapshot consumption, filter/rank/top-N, and CandidateSet production.
- AXIS 3 owns Condition **artifact lifecycle**: immutable versioned copies of approved/research `axis2_selection_spec/v1` data, lineage and promotion state.
- AXIS 3 owns Strategy CRUD and strategy version lineage.
- AXIS 3 does not parse/execute DSL and does not re-run AXIS 2 selection logic.
- Cross-axis execution is performed only through versioned Bridge contracts; Step 10 creates execution intents only, while Step 11 owns the actual E2E Bridge routing.
- Feature Catalog remains separate and immutable.

Current layout:

```text
crud/
  versioned_store.py
  condition_version.v1.schema.json
  strategy_version.v1.schema.json
orchestration/
  run_plan.py
  strategy_run_plan.v1.schema.json
```

Storage policy:

```text
content update = new immutable version
lifecycle state = separate audited state
hard delete = not used for product lineage; archive preserves history
```

Do not import AXIS 1/2 internal modules or frozen repository-root `core/` from this package.

See:

- `DSL_THREE_AXIS_FINAL_TARGET.md`
- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
- `DSL_FROZEN_CORE_MIGRATION_POLICY.md`
