# MSA1 Immutable Multi-Symbol Snapshot Evidence — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## Trusted predecessor

PCTX2D received operator validation at exact checkout:

```text
6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
Ran 6 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the explicit MARKET -> SECTOR dependency-DAG parent-context boundary is trusted Full-green at that SHA.

## Why MSA1 comes before GROUP / Leader-Follower

The authoritative `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md` requires cross-symbol research to consume immutable point-in-time single-instrument snapshots rather than giving Instrument DSL arbitrary peer access.

The repository already contains `core/multi_symbol.py`, an earlier deterministic multi-symbol scenario vertical slice that runs independent Backtests and computes relative evidence. That engine remains useful and is not rewritten here. However, the newer policy's explicit `InstrumentSignalSnapshot` seam did not yet exist.

MSA1 fills that gap before adding leader/follower or group intelligence:

```text
already-evaluated single-instrument tactic state at exact t
 -> immutable InstrumentSignalSnapshot
 -> explicit point-in-time SnapshotUniverse
 -> observation-only multi-axis Add-on analysis
 -> per-axis leaderboards + Pareto evidence
```

No deployment authority is created.

## Executable

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

Analysis policy:

```text
OBSERVATION_ONLY_PER_AXIS_LEADERBOARDS_AND_PARETO_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

Causality policy:

```text
POINT_IN_TIME_ONLY
```

## InstrumentSignalSnapshot

Each snapshot explicitly carries:

```text
symbol
as_of
knowledge_cutoff
candidate_hash
family_id
generation_hash
tactic_trigger
hard_guards_pass
locally_admissible
comparison_metrics
source
evidence_hash
metadata
snapshot_hash
```

MSA1 v1 requires exact:

```text
as_of == knowledge_cutoff
```

Comparison metrics are finite numeric values only. The contract is deliberately causal: post-outcome labels such as later MFE/winner status are not valid point-in-time comparison inputs merely because they can be represented numerically.

Changing candidate/evidence/state/metric identity changes `snapshot_hash`.

## Explicit universe authority

`SnapshotUniverse` requires:

```text
universe_id
symbols[]
as_of
knowledge_cutoff
source_authority
metadata
universe_hash
```

The analyzer does not discover or guess symbols. Snapshot membership must equal the declared universe exactly; missing and extra symbols fail closed.

Every snapshot must match the universe's exact timestamp. There is no nearest-time, stale substitution or fill-forward behavior.

## Explicit multi-axis comparison

`SnapshotAnalysisPolicy` declares one or more `SnapshotComparisonAxis` objects:

```text
metric_id
direction = MAX | MIN
```

Eligibility for comparison can require:

```text
tactic_trigger
hard_guards_pass
locally_admissible
```

Failure of those local conditions is recorded as descriptive comparison reasons such as:

```text
TACTIC_NOT_TRIGGERED
HARD_GUARD_FAILED
LOCAL_NOT_ADMISSIBLE
```

These are **not** Broker/deployment block decisions.

For comparison-eligible snapshots MSA1 produces:

- one deterministic leaderboard per declared metric axis;
- symbol-ascending tie breaking;
- a deterministic Pareto frontier across the declared axes.

There is no weighted aggregate score and no hidden universal ranking.

## Observation-only output

`MultiSymbolSnapshotAnalyzer.analyze(...)` returns:

```text
mode = OBSERVATION_ONLY
operational_authority = false
universe / universe_hash
policy / policy_hash
input_snapshot_hashes
rows
leaderboards
pareto_symbols
comparison_eligible_symbols
result_hash
```

MSA1 intentionally does **not** return:

```text
allowed_symbols
blocked_symbols
max_slots
allocation
entry_gate
Broker orders
DeploymentDecision
```

A later separately validated tranche may translate sufficiently validated Add-on evidence into a parent feature or deployment decision. MSA1 itself cannot.

## No execution/provider dependency

`core/multi_symbol_snapshot.py` imports none of:

```text
DSLRuntime
BacktestEngine
BrokerEmulator
ParentFeatureProvider
```

It performs no provider call, DB/network access, universe discovery or DSL mutation.

The existing single-instrument and parent-context execution boundaries are unchanged.

## Relationship to existing core/multi_symbol.py

`core/multi_symbol.py` remains the existing scenario/cohort orchestration vertical slice and its historical tests remain authoritative for that boundary.

MSA1 is a new safe Add-on evidence seam for future work. New leader/follower, breadth, peer comparison and parent-feature publication should be built from immutable snapshots rather than introducing peer-symbol syntax into Instrument DSL.

A later compatibility tranche may export appropriate causal per-symbol state from existing scenario execution into `InstrumentSignalSnapshot`; MSA1 deliberately does not infer causal snapshot metrics from full-future Backtest outcomes.

## Regression

New regression:

```text
test_stage1_multi_symbol_snapshot.py
```

Coverage includes:

- deterministic snapshot identity;
- snapshot identity changes with causal evidence/metric mutation;
- explicit universe membership and exact-time validation;
- finite declared metric requirements;
- local trigger/guard/admissibility comparison eligibility;
- deterministic per-axis leaderboards;
- deterministic Pareto frontier;
- input snapshot order invariance;
- no allowed/blocked/score deployment fields;
- no Backtest/Broker/DSL/provider imports in the Add-on module.

The standard Tactical P1 Full verifier discovers this file through `test_stage1_*.py`.

## Mutation boundary

MSA1 adds only:

```text
core/multi_symbol_snapshot.py
test_stage1_multi_symbol_snapshot.py
MSA1_IMMUTABLE_MULTI_SYMBOL_SNAPSHOT_EVIDENCE_IMPLEMENTATION.md
```

plus authority/checkpoint documentation updates.

It does not modify:

```text
Parser / Semantic / Runtime
BacktestEngine
BrokerEmulator
core/multi_symbol.py existing execution semantics
PCTX1-PCTX2D provider/context semantics
entry_gate
Chart SSOT
```

## Nonclaims

Do not claim yet:

- trusted Full PASS for MSA1;
- production leader/follower/group intelligence;
- validated cross-symbol selection edge;
- automatic allowed/blocked symbol authority;
- portfolio slot/allocation authority;
- Add-on-derived registered parent features;
- OOS profitability benefit;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Validation gate

Validate this observation-only evidence seam at one exact checkout before implementing leader/follower/group parent features or deployment selection:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_multi_symbol_snapshot.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
