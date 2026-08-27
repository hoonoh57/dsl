# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1 TRUSTED / MSA2 ACTIVE / 2026-08-27 KST**

## 1. Governing rule

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

Instrument DSL remains single-instrument. Multi-symbol chart display, cohort analysis or group evidence does not create peer-symbol execution authority.

Instrument DSL must not directly perform:

```text
arbitrary cross-symbol requests
peer-symbol runtime reads
universe enumeration
cross-symbol ranking
capital/slot allocation
leader/follower selection
hidden dependency on displayed chart panes
```

These remain orchestration/evidence/deployment responsibilities.

## 2. Existing scenario vertical slice

`core/multi_symbol.py` remains the earlier deterministic scenario/cohort vertical slice described by `MULTI_LAYER_DSL_ARCHITECTURE.md`.

It runs independent InstrumentTasks through the validated single-instrument Backtest/Broker kernel. MSA1/MSA2 do not rewrite or remove it.

New cross-symbol research should prefer immutable point-in-time snapshot evidence whenever it can be represented without direct peer-symbol access from Instrument DSL.

## 3. MSA1 immutable snapshot seam — trusted

Trusted exact checkpoint:

```text
adaef963dce717b252f2575896a74462c8a277a2
Ran 6 tests in 0.003s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA1 contracts:

```text
InstrumentSignalSnapshot
SnapshotUniverse
SnapshotComparisonAxis
SnapshotAnalysisPolicy
MultiSymbolSnapshotAnalyzer
```

Every snapshot is exact point-in-time evidence:

```text
symbol
as_of == knowledge_cutoff
candidate_hash
family_id / generation_hash
tactic_trigger
hard_guards_pass
locally_admissible
finite declared comparison_metrics
source / evidence_hash
snapshot_hash
```

The Add-on reads snapshots. It does not call Parser/Runtime private state, Backtest, Broker, providers, DB/network or mutate the originating tactic.

The universe is explicit and exact. Missing/extra symbols, mismatched times and missing declared metrics fail closed. No nearest-time or fill-forward behavior is permitted.

MSA1 comparison is multi-axis and deterministic, with explicit MAX/MIN axes, per-axis leaderboards and Pareto evidence. There is no hidden weighted universal score.

MSA1 always remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

## 4. MSA2 bounded group evidence — active validation tranche

MSA2 consumes a chronological sequence of exact MSA1 snapshot points under a stable explicit universe.

Module:

```text
core/multi_symbol_group_evidence.py
```

Policy:

```text
STATIC_EXPLICIT_UNIVERSE_EXACT_CHRONOLOGICAL_POINTS
OBSERVATION_ONLY_BOUNDED_STATIC_UNIVERSE_LEADER_FOLLOWER_BREADTH_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

MSA2 requires explicit bounds and semantics:

```text
metric_id
direction = MAX | MIN
favorable_threshold
leader_count
lookback_points
max_symbols
max_points
```

Across one MSA2 frame, universe ID, ordered symbol topology, source authority and per-symbol candidate/family/generation identity remain stable. Timestamps are exact, unique and strictly increasing.

MSA2 may describe:

```text
comparison eligible breadth
favorable breadth
current leaders/followers
leader/follower metric spread
follower favorable rate
leader persistence
```

Those values are evidence, not selection authority. A symbol called a `leader` is only descriptively ranked under the declared policy at that exact time.

If comparison eligibility collapses, missing follower aggregate evidence remains explicit null rather than being fabricated as zero.

MSA2 also always remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

## 5. Explicit universe and causality

Every cross-symbol research run must declare its opportunity set and source authority. The Add-on must never silently discover or guess the universe.

All compared evidence must be valid at the declared point in time. Future-close, later winner information, end-of-day labels or revised future data must not become an earlier comparison input.

Missing, stale or mismatched evidence is explicit and fail-closed according to the declared contract; it is never silently substituted.

## 6. Observation is not deployment selection

Observation-only evidence must not be confused with `allowed_symbols` or portfolio selection.

Neither MSA1 nor MSA2 may emit:

```text
allowed_symbols
blocked_symbols
max_slots
capital allocation
entry_gate
DeploymentDecision
Broker order
```

A later deployment-selection tranche requires separate causal Train/Validation/OOS evidence and an explicit authority contract.

The eventual authority relationship remains:

```text
single-instrument tactic trigger
AND local hard guards
AND optional separately validated Add-on permission
AND common execution policy
 -> BrokerEmulator
```

An Add-on can never bypass local hard guards, execution settings, accounting or Broker authority.

## 7. Optional Parent Feature Provider publication

A validated Add-on may later publish a **bounded registered parent feature** rather than expose peer-symbol state directly to Instrument DSL.

Potential examples:

```text
group.breadth
group.leader_persistence
group.leader_follower_spread
group.follower_confirmation
```

Publication is a separate contract from MSA1/MSA2 observation. Any published feature must use PCTX1 manifest/version semantics, exact causality, dependency evidence and PCTX2D orchestration.

Allowed conceptual flow:

```text
immutable single-instrument snapshots
 -> MSA observation evidence
 -> separately versioned bounded Parent Feature Provider
 -> ContextLayerSnapshot / BattlefieldContext
 -> read-only ctx.*
```

Direct peer-symbol query syntax in Instrument DSL remains prohibited.

## 8. Default disabled and replaceable

The Add-on is optional and disabled by default during neutral micro-tactic discovery.

A tactic's neutral baseline must remain independently runnable without cross-symbol Add-on intelligence.

The Add-on must be replaceable or removable without changing:

```text
Instrument DSL syntax
Parser / Runtime
indicator semantics
Backtest accounting
BrokerEmulator
historical single-instrument TacticalProfiles
```

If a later tactic explicitly requires a registered Add-on-derived parent feature and that feature is unavailable, missing required context must fail closed rather than be guessed.

## 9. Research before deployment

Required order:

```text
single-instrument evidence
 -> immutable snapshots
 -> observation-only MSA evidence
 -> Train / Validation / OOS evaluation
 -> optional bounded registered parent feature or selection policy
 -> separate deployment validation
```

Cross-sectional attractiveness is not entry authority.

## 10. Change-control rule

Before implementing any cross-symbol capability, ask:

```text
Can it be expressed as read-only analysis of immutable per-symbol snapshots?
```

If yes, keep it in the Add-on.

If a conclusion is intended for Instrument DSL consumption, ask:

```text
Can it be published as a bounded registered point-in-time parent feature?
```

If yes, use the Parent Feature Provider / Context seam.

Direct cross-symbol syntax in Instrument DSL requires a future explicit authority change and independent Core-promotion evidence; it is not authorized now.

## 11. Current nonclaims

Do not claim yet:

- trusted Full PASS for MSA2;
- production GROUP/leader-follower/breadth edge;
- MSA2-derived registered GROUP parent features;
- validated Add-on deployment selection;
- portfolio allocation authority;
- OOS profitability improvement from cross-symbol context;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.
