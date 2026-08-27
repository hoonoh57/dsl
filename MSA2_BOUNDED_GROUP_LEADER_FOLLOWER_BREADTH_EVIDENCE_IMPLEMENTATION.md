# MSA2 Bounded Group Leader/Follower/Breadth Evidence — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## Trusted predecessor

MSA1 received operator validation at exact checkout:

```text
adaef963dce717b252f2575896a74462c8a277a2
Ran 6 tests in 0.003s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the immutable point-in-time multi-symbol snapshot seam is trusted Full-green at that SHA.

## Objective

MSA2 adds bounded GROUP-level descriptive evidence without turning cross-symbol research into execution authority.

```text
exact InstrumentSignalSnapshot points
 + explicit static SnapshotUniverse
 + explicit metric/direction/threshold policy
 -> bounded exact chronological group frame
 -> breadth / leader / follower / persistence evidence
 -> OBSERVATION_ONLY
```

It does not publish a ParentFeatureProvider result yet and does not create an entry gate, DeploymentDecision, allocation or Broker order.

## Executable

New module:

```text
core/multi_symbol_group_evidence.py
```

New regression:

```text
test_stage1_multi_symbol_group_evidence.py
```

Schemas/policies:

```text
multi_symbol_group_evidence/v1
multi_symbol_group_evidence_policy/v1
STATIC_EXPLICIT_UNIVERSE_EXACT_CHRONOLOGICAL_POINTS
OBSERVATION_ONLY_BOUNDED_STATIC_UNIVERSE_LEADER_FOLLOWER_BREADTH_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

## Explicit bounded policy

`GroupEvidencePolicy` declares:

```text
policy_id / policy_version
metric_id
direction = MAX | MIN
favorable_threshold
leader_count
lookback_points
max_symbols
max_points
require_tactic_trigger
require_hard_guards
require_local_admissibility
```

There is no weighted universal score. The single metric used for v1 leader/follower evidence is explicit and versioned.

## Exact frame contract

Each `GroupSnapshotPoint` contains exactly one MSA1 `SnapshotUniverse` and the exact snapshot set for that timestamp.

MSA2 v1 requires:

- at least two exact chronological points;
- unique strictly increasing `YYYYMMDDHHMMSS` timestamps;
- one stable `universe_id`;
- identical ordered symbol topology at every point;
- one stable universe source authority;
- explicit `max_symbols` and `max_points` bounds;
- exact point-in-time snapshot membership;
- stable candidate/family/generation identity per symbol across the frame;
- the declared metric present and finite on every snapshot.

There is no universe discovery, nearest-time substitution, interpolation or fill-forward.

## Descriptive group evidence

At every point MSA2 reuses MSA1 comparison eligibility and deterministic leaderboard semantics. The latest evidence contains:

```text
comparison_eligible_count / rate
favorable_count / favorable_breadth_rate
leader_symbols
follower_symbols
leader_metric_mean
follower_metric_mean
leader_follower_spread
follower_favorable_rate
leader_persistence over bounded lookback
```

For `MAX`, favorable means `value >= favorable_threshold`; for `MIN`, favorable means `value <= favorable_threshold`.

`leader_follower_spread` is direction-normalized so a positive value means the observed leaders are stronger on the declared axis:

```text
MAX: leader_mean - follower_mean
MIN: follower_mean - leader_mean
```

If comparison eligibility collapses so no follower remains, follower aggregates are explicitly `null`. They are never silently replaced with zero and the collapse remains research evidence.

## Leader/follower is not selection authority

`leader_symbols` means only "descriptively ranked at this exact point under this declared policy".

MSA2 always returns:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

It intentionally does not return:

```text
allowed_symbols
blocked_symbols
allocation
max_slots
entry_gate
DeploymentDecision
Broker order
```

## No execution/provider calls

`core/multi_symbol_group_evidence.py` consumes MSA1 snapshot contracts only. It does not invoke:

```text
DSLRuntime
BacktestEngine
BrokerEmulator
ParentFeatureProvider
DB/network source discovery
```

Instrument DSL remains single-instrument and receives no peer-symbol query capability.

## Regression coverage

The focused regression covers:

- breadth, leader/follower spread and leader persistence;
- deterministic result identity under snapshot input reordering;
- strict chronological point ordering;
- static universe topology enforcement;
- tactic identity drift rejection;
- explicit symbol/point bounds;
- MAX and MIN favorable semantics;
- observation-only/no-authority output;
- no execution/provider/network imports.

The Tactical P1 Full verifier discovers the regression through `test_stage1_*.py`.

## Mutation boundary

MSA2 adds only its sidecar evidence module, regression and checkpoint/status documentation. It does not modify:

```text
Parser / Semantic / Runtime
BacktestEngine
BrokerEmulator
core/multi_symbol.py
PCTX1-PCTX2D provider/context semantics
CTXDSL1 / CTXBT1
entry_gate
Chart SSOT
```

## What comes next only after trusted validation

The next decision is not automatic deployment selection. First determine whether a **small bounded subset** of MSA2 evidence deserves publication as registered GROUP parent features, for example breadth or leader persistence, under PCTX1/PCTX2D dependency evidence.

Any such publication must remain descriptive, causal and separately versioned. Train/Validation/OOS evidence is still required before any operational gate.

## Nonclaims

Do not claim yet:

- trusted Full PASS for MSA2;
- production GROUP/leader-follower edge;
- validated cross-symbol selection edge;
- registered GROUP parent features from MSA2;
- automatic symbol permission/allocation;
- OOS profitability improvement;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Validation gate

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_multi_symbol_group_evidence.py
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
