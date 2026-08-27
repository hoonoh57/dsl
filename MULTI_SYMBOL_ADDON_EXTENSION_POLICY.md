# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1 ACTIVE / 2026-08-27 KST**

## 1. Governing rule

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

The Instrument DSL remains single-instrument. Multi-symbol chart display does not create peer-symbol execution authority.

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

`core/multi_symbol.py` remains the existing deterministic multi-symbol tactical scenario engine described by `MULTI_LAYER_DSL_ARCHITECTURE.md`.

It runs independent InstrumentTasks through the validated single-instrument Backtest/Broker kernel and provides the earlier P0 scenario/cohort analysis boundary. MSA1 does not rewrite or remove that functionality.

New cross-symbol capabilities added after this policy checkpoint should prefer the immutable snapshot seam below whenever the requirement can be represented as read-only analysis of already-evaluated single-instrument evidence.

## 3. MSA1 safe Add-on seam — active validation tranche

New module:

```text
core/multi_symbol_snapshot.py
```

Schemas:

```text
instrument_signal_snapshot/v1
multi_symbol_snapshot_universe/v1
multi_symbol_snapshot_policy/v1
multi_symbol_snapshot_analysis/v1
```

Causality/analysis policies:

```text
POINT_IN_TIME_ONLY
OBSERVATION_ONLY_PER_AXIS_LEADERBOARDS_AND_PARETO_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

### InstrumentSignalSnapshot

A snapshot is an immutable export from one already-evaluated single-instrument tactic at one exact point in time:

```text
symbol
as_of == knowledge_cutoff
candidate_hash
family_id / generation_hash
tactic_trigger
hard_guards_pass
locally_admissible
declared finite comparison_metrics
source / evidence_hash
snapshot_hash
```

Only explicitly exported point-in-time metrics are visible to the Add-on. Full-future Backtest outcomes, later MFE labels, end-of-day winners or revised future information must not be smuggled into a snapshot used at an earlier timestamp.

MSA1 does not infer causal metrics from complete Backtest outcomes.

## 4. Explicit universe and time alignment

Every snapshot analysis declares:

```text
universe_id
ordered symbols[]
as_of == knowledge_cutoff
source_authority
universe_hash
```

The Add-on must not silently discover or guess the universe.

Snapshot membership must equal the declared universe exactly. Missing/extra symbols, duplicate symbols, mismatched timestamps and missing declared comparison metrics fail closed.

There is no nearest-time substitution, interpolation or fill-forward.

## 5. Deterministic comparison

`SnapshotAnalysisPolicy` declares explicit metric axes:

```text
metric_id
direction = MAX | MIN
```

The same universe, snapshots and policy must always produce the same result.

MSA1 produces:

- one deterministic leaderboard per metric axis;
- symbol-ascending deterministic tie breaking;
- a Pareto frontier over all declared axes.

No hidden weighted universal score is used.

Local comparison eligibility may require:

```text
tactic_trigger
hard_guards_pass
locally_admissible
```

A failed local condition is recorded as evidence such as `TACTIC_NOT_TRIGGERED`, `HARD_GUARD_FAILED` or `LOCAL_NOT_ADMISSIBLE`. These are comparison-status reasons, not Broker/deployment decisions.

## 6. Observation before deployment

MSA1 output is deliberately observation-only:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

It may return rows, per-axis leaderboards, Pareto symbols, comparison-eligible symbols and immutable hashes.

MSA1 does not return or create:

```text
allowed_symbols
blocked_symbols
max_slots
portfolio allocation
entry_gate
DeploymentDecision
Broker orders
```

Cross-symbol selection or permission requires a later separately validated policy/evidence tranche.

## 7. No Core/execution/provider dependency

The MSA1 module does not call or import:

```text
DSLRuntime
BacktestEngine
BrokerEmulator
ParentFeatureProvider
```

It performs no database/network/provider discovery and does not mutate the originating tactic.

Removing the Add-on must not change Instrument DSL syntax, Parser/Runtime semantics, indicator semantics, Backtest accounting, BrokerEmulator or historical single-instrument TacticalProfiles.

## 8. Optional Parent Feature Provider role — future

After causal Train/Validation/OOS evidence, a separately versioned Add-on component may publish bounded registered context features such as:

```text
sector.breadth
sector.leader_strength
group.follower_alignment
group.relative_strength
```

Allowed flow:

```text
immutable InstrumentSignalSnapshot[]
 -> validated Multi-Symbol Add-on analysis
 -> separately versioned registered Parent Feature Provider output
 -> PCTX1 result / BattlefieldContext
 -> exact read-only ctx.* binding
```

This never grants Instrument DSL arbitrary peer-symbol access.

MSA1 itself does not publish parent features.

## 9. Relationship to MARKET/SECTOR context

Trusted parent-context work currently provides explicit MARKET and SECTOR descriptive context independently of the Add-on.

A future hierarchy may be:

```text
MARKET / SECTOR parent context
 -> Instrument DSL local tactic
 -> immutable per-instrument signal snapshots
 -> optional multi-symbol Add-on analysis
 -> later validated deployment policy and/or bounded parent feature publication
 -> common execution policy
 -> BrokerEmulator
```

No layer rewrites lower-layer historical evidence.

## 10. Research-before-deployment rule

Cross-symbol capabilities must progress through:

```text
point-in-time single-instrument evidence
 -> immutable snapshots
 -> observation-only Add-on analysis
 -> Train/Validation/OOS evidence
 -> explicit deployment/parent-feature policy if justified
```

An attractive leader/follower or relative-strength pattern is not immediately live order authority.

## 11. Change-control questions

Before implementing any new cross-symbol feature:

```text
Can it be expressed as read-only analysis of immutable per-symbol snapshots?
```

If yes, keep it in the Add-on.

If an analysis conclusion is intended for DSL consumption:

```text
Can it be published as a bounded registered point-in-time parent feature?
```

If yes, use the PCTX provider/context seam instead of peer-symbol DSL syntax.

Direct cross-symbol syntax in Instrument DSL remains prohibited unless a future authority change proves that the Add-on/context representation is insufficient and separately satisfies Core promotion criteria.

## 12. Current status / nonclaims

Trusted predecessor relevant to this transition:

```text
PCTX2D 6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
Ran 6 tests in 0.174s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Implemented, awaiting validation:

```text
MSA1 immutable InstrumentSignalSnapshot contract
explicit SnapshotUniverse
explicit multi-axis observation policy
per-axis leaderboards + Pareto evidence
```

Not yet claimed:

```text
trusted MSA1 Full PASS
production GROUP/Leader-Follower/breadth intelligence
Add-on-derived registered parent features
validated cross-symbol selection edge
allowed/blocked symbol authority
portfolio allocation authority
live-trading readiness
repository-wide compliance PASS
```

`REMEDIATION_REQUIRED` remains broader repository status.

## 13. Immediate gate

Validate MSA1 at one exact repository SHA before leader/follower/group parent-feature publication or deployment-selection wiring.

Any verifier failure must first be classified exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
