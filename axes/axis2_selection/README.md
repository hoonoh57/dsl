# AXIS 2 — Exact-PIT Selection

Status: **ACTIVE IMPLEMENTATION ROOT / SNAPSHOT-FIRST / SELECTION ENGINE VALIDATED**

This directory owns cross-sectional selection semantics, not single-instrument DSL execution and not product artifact lifecycle.

Core flow:

```text
precompute
 -> immutable exact point-in-time snapshot
 -> filter / rank / top-N
 -> CandidateSet + evidence
```

Primary feature evidence may include market regime, beta/high-beta universe membership, sector/leader relations, EMA120 events, normalized MACD Histogram strength/rank, relative strength, turnover and capital-flow data.

Boundary:

- AXIS 2 owns Condition **selection semantics**: feature identities, exact snapshot requirements, filter/rank/top-N rules and candidate evidence.
- AXIS 3 owns Condition **artifact lifecycle**: immutable versions, lineage, promotion/rejection/archive state.
- AXIS 2 does not place orders or execute Strategy DSL.
- AXIS 2 must not import AXIS 1/3 internals or repository-root frozen `core/`.
- Selection consumes already-precomputed exact-PIT evidence; no future values, nearest-time lookup, fill-forward, interpolation or missing-value default synthesis.

Current layout:

```text
snapshots/
engine/
```

See:

- `DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md`
- `DSL_THREE_AXIS_FINAL_TARGET.md`
- `DSL_THREE_AXIS_MODULE_BOUNDARY.md`
- `DSL_DOCUMENT_AUTHORITY_INDEX.md`
