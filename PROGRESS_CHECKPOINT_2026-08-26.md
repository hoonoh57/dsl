# Quant DSL Progress Checkpoint — 2026-08-26 KST

Status: **E3A_TRUSTED_FULL_PASS / E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

## Trusted Full checkpoints

### Earlier E0 / initial E1-E2 foundation

Trusted executable checkpoint:

```text
ac01525223f897f155de63f02529b0a6429a0882
[PASS] Tactical P1 verification completed: mode=Full.
```

### E1 Korean regular-session contract

Trusted executable checkpoint:

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

The first E2 Full failure was classified as a **test defect** because a 5m JMA regression used the default deterministic 1d synthetic fixture. Product timeframe fail-close behavior was correct and was not weakened.

Trusted executable checkpoint after remediation:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3A causal TacticalObservation sidecar

E3A introduced `core/tactical_observation.py` and its regression contract. Feature calculation is prefix-only and observation identity was additionally hardened so future-only market mutations may change full `BattleCase.case_hash` provenance but cannot change the earlier observation's `market_prefix_hash`, feature values or `observation_hash`.

The operator verified exact checkout:

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
```

with:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E3A is trusted Full-validated at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`.**

## Stability architecture now authoritative

The project continues under:

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
```

Key rules remain:

- Core Instrument DSL stays deterministic and narrow;
- adaptive learning/memory remains optional sidecar research;
- arbitrary cross-symbol reads/ranking remain outside Instrument DSL;
- parent/cascading features are preserved through Provider -> immutable Context snapshot -> future read-only `ctx.*` binding;
- parent calculations do not execute inside DSL Runtime;
- hard guards/common execution authority cannot be bypassed by learned/add-on/context evidence without an explicit future authority change.

## E3 executable boundary now added

`core/tactical_parameter_seeker.py` adds the first **Multi-Battle Parameter Seeker**.

The E3 contract is:

```text
base TacticCandidate
 + numeric DSL input parameter space
 + one frozen BattleCase set
        ↓
deterministic grid/random plan
        ↓
DSL input substitution only
        ↓
TacticalDiscoveryEngine on the same BattleCases
        ↓
profile per parameter candidate
        ↓
TacticalCompetitionEngine
        ↓
metric leaderboards + Pareto frontier
```

Important boundaries:

- E3 v1 accepts `ParameterSpec(target="dsl")` only;
- execution-setting tuning is rejected so frozen `BattleCase` identity/settings do not drift between candidates;
- candidate DSL structure is unchanged except declared numeric `input` values;
- every profile must keep the same `case_set_hash` and context policy;
- no `MAX_RETURN`/`ROBUST_SCORE`-style hidden universal score is introduced;
- no automatic promotion occurs;
- worker count may not change seek identity or comparison evidence.

`test_stage1_tactical_parameter_seeker.py` covers frozen-case identity, Pareto selection policy, worker invariance, seeded random determinism and setting-parameter rejection. The existing Full verifier discovers this test through `test_stage1_*.py`.

Detailed implementation checkpoint:

```text
E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md
```

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- Core DSL Freeze / sidecar/provider/Add-on boundaries are authoritative;
- E3 Multi-Battle Parameter Seeker source/tests are implemented.

Do not claim yet:

- trusted Full PASS for E3;
- a strongest/profitable parameter set;
- automatic parameter promotion;
- E4 Failure Characterizer implementation;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the separate broader repository status.

## Immediate boundary

Do not begin E4 executable work before E3 is trusted green.

Run:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before editing.
