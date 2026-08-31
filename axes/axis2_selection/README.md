# AXIS 2 — Semi-Condition Selection

Status: **NEW IMPLEMENTATION ROOT / SNAPSHOT-FIRST**

This directory owns cross-sectional candidate selection, not Instrument DSL execution.

Core rule:

```text
precompute -> freeze point-in-time snapshot -> filter/rank/top-N -> CandidateSetResponse
```

Primary development targets include:

- market regime snapshots;
- beta/high-beta universe snapshots;
- sector strength and constituent snapshots;
- normalized MACD Histogram per-symbol snapshots;
- cross-symbol and within-sector Histogram rankings;
- relative-strength / turnover / capital-flow features;
- generic Condition CRUD and reproducible candidate evidence.

Do not calculate these by repeatedly invoking AXIS 1 DSL during a selection request. Do not import frozen repository-root `core/`.

Planned internal layout:

```text
providers/
snapshots/
engine/
conditions/
ranking/
tests/
```

See:

- `DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md`
- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
