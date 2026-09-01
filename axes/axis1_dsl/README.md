# AXIS 1 — DSL Capability / Execution

Status: **ACTIVE IMPLEMENTATION ROOT / MIGRATION COMPLETE / ADDITIVE CAPABILITIES VALIDATED THROUGH STEP 14**

This directory owns deterministic single-instrument DSL expression and execution.

Current responsibilities:

```text
core/        Parser, Semantic, lowering, capability registry
indicators/  deterministic indicator kernels
runtime/     state, bar/intrabar lifecycle, MTF, exact read-only context
execution/   broker, partial execution, pyramiding, backtest, projection/parity
```

Rules:

- repository-root `core/` is immutable legacy reference and is never a development target;
- AXIS 1 must not import AXIS 2 or AXIS 3 internals;
- universe discovery, peer ranking and cross-symbol selection do not belong here;
- Condition/Strategy CRUD and promotion lifecycle do not belong here;
- parent/selection evidence enters only through an explicit exact read-only context binding;
- product capabilities are generic, deterministic and fail-closed; no symbol/venue/strategy shortcuts;
- current support truth is `core/capability_diagnostic_registry.py`, not old static feature-count documents.

Validated additive capabilities include multi-output lowering, generic projection, user functions, bounded loops, intrabar provisional lifecycle, partial fills/exits, same-direction pyramiding/multi-lot accounting, reference differential fixtures and batch/stream parity verification.

See:

- `DSL_THREE_AXIS_FINAL_TARGET.md`
- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
- `DSL_FROZEN_CORE_MIGRATION_POLICY.md`
- `DSL_DOCUMENT_AUTHORITY_INDEX.md`
