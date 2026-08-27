# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1-MSA2 TRUSTED / MSA3 GROUP PUBLICATION ACTIVE / 2026-08-27 KST**

## 1. Governing rule

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

Instrument DSL remains single-instrument. Multi-symbol chart display, cohort analysis, leader/follower evidence or GROUP publication does not create peer-symbol execution authority.

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

It runs independent InstrumentTasks through the validated single-instrument Backtest/Broker kernel. MSA1-MSA3 do not rewrite or remove it.

New cross-symbol research should prefer immutable point-in-time snapshot evidence whenever the requirement can be represented without direct peer-symbol access from Instrument DSL.

## 3. MSA1 immutable snapshot seam — trusted

Trusted exact checkpoint:

```text
adaef963dce717b252f2575896a74462c8a277a2
Ran 6 tests in 0.003s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA1 provides exact immutable `InstrumentSignalSnapshot` evidence and an explicit `SnapshotUniverse`. Missing/extra symbols, time mismatch and missing comparison metrics fail closed. Analysis is deterministic per-axis/Pareto evidence with no hidden universal score.

MSA1 always remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

## 4. MSA2 bounded group evidence — trusted

Trusted exact checkpoint:

```text
3a5a2ece658ead28a1822ef7482a3d284d12e2d6
Ran 7 tests in 0.017s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA2 consumes bounded chronological exact MSA1 points under a stable explicit universe and stable tactic identity topology.

Policy declares:

```text
metric_id
direction = MAX | MIN
favorable_threshold
leader_count
lookback_points
max_symbols
max_points
```

MSA2 may describe eligible/favorable breadth, current leaders/followers, normalized leader/follower spread, follower favorable rate and bounded leader persistence.

Those values are observation evidence only. If follower evidence collapses, follower aggregates remain explicit null.

MSA2 also always remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

## 5. MSA3 bounded Parent Feature publication — active validation tranche

A useful cross-symbol conclusion may be published to Instrument DSL only through the Parent Feature Provider seam, never through peer-symbol syntax.

MSA3 implements the first narrow bridge:

```text
exact precomputed MSA2 evidence
 -> research-only aggregate GROUP ParentFeatureProviderResult
 -> PCTX1 / PCTX2D OBSERVED context
 -> generic registered read-only binder
```

Module:

```text
core/group_evidence_parent_feature_provider.py
```

Publication is deliberately limited to aggregate values:

```text
group.<namespace>_comparison_eligible_rate
group.<namespace>_favorable_breadth_rate
group.<namespace>_leader_persistence_rate
group.<namespace>_leader_follower_spread       optional
group.<namespace>_follower_favorable_rate      optional
```

MSA3 does not publish:

```text
leader/follower symbol identities
rank lists
allowed_symbols
blocked_symbols
max_slots
allocation
entry_gate
DeploymentDecision
Broker order
```

The MSA2 evidence timeline is exact only and verifies the MSA2 `result_hash`; no nearest-time or fill-forward behavior is permitted.

The GROUP result requires an exact configured SECTOR dependency and records that dependency `result_hash`, preserving `MARKET -> SECTOR -> GROUP` evidence lineage.

MSA3 remains:

```text
publication_state = RESEARCH_ONLY
operational_authority = false
```

## 6. Explicit universe and causality

Every cross-symbol research run must declare its opportunity set and source authority. The Add-on must never silently discover or guess the universe.

All compared evidence must be valid at the declared point in time. Future-close, later winner information, end-of-day labels or revised future data must not become earlier comparison inputs.

Missing, stale or mismatched evidence is explicit and fail-closed; it is never silently substituted.

## 7. Observation/publication is not deployment selection

Neither MSA1, MSA2 nor research-only MSA3 publication may be treated as operational symbol permission.

Before any Add-on conclusion can influence execution authority, the required progression is:

```text
observation evidence
 -> causal Train / Validation / OOS evidence
 -> explicit deployment policy
 -> separately validated execution integration
```

The eventual authority relationship remains:

```text
single-instrument tactic trigger
AND local hard guards
AND optional separately validated Add-on permission
AND common execution policy
 -> BrokerEmulator
```

An Add-on can never bypass local hard guards, execution settings, accounting or Broker authority.

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

If a later tactic explicitly requires a validated registered Add-on-derived parent feature and that feature is unavailable, required context fails closed rather than being guessed.

## 9. Change-control rule

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

## 10. Current nonclaims

Do not claim yet:

- trusted Full PASS for MSA3;
- production GROUP/leader-follower/breadth edge;
- validated Add-on deployment selection;
- GROUP parent-feature OOS benefit;
- GROUP feature DEPLOYMENT eligibility;
- portfolio allocation authority;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.
