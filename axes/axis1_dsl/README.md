# AXIS 1 — DSL Capability Engine

Status: **NEW IMPLEMENTATION ROOT / MIGRATION NOT YET STARTED**

This directory is the only location for future DSL capability development after frozen-core migration begins.

Authoritative rules:

- `core/` at repository root is immutable legacy reference and must not be modified.
- Do not import frozen `core/` as a permanent runtime dependency.
- Migrate one boundary at a time and prove parity against the frozen reference.
- After parity, resume DSL-native capability development here without delay.
- First-priority capability after parity: typed tuple/multi-output returns and destructuring.

Planned internal layout:

```text
core/
indicators/
runtime/
execution/
tests/
```

See:

- `DSL_FROZEN_CORE_MIGRATION_POLICY.md`
- `DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md`
- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
