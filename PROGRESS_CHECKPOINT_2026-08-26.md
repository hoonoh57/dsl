# Quant DSL Progress Checkpoint — 2026-08-26 KST

Status: **E3_MULTI_BATTLE_PARAMETER_SEEKER_TRUSTED_FULL_PASS / CORE_DSL_FREEZE_ACTIVE**

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

E3A introduced `core/tactical_observation.py` and its regression contract. Feature calculation is prefix-only and observation identity was hardened so future-only market mutations may change full `BattleCase.case_hash` provenance but cannot change the earlier observation's `market_prefix_hash`, feature values or `observation_hash`.

Trusted exact checkout:

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E3A is trusted Full-validated at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`.**

### E3 Multi-Battle Parameter Seeker

E3 added `core/tactical_parameter_seeker.py` and `test_stage1_tactical_parameter_seeker.py`.

The trusted contract is:

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

Important boundaries remain:

- E3 v1 accepts `ParameterSpec(target="dsl")` only;
- execution-setting tuning is rejected so frozen `BattleCase` identity/settings do not drift between candidates;
- candidate DSL structure is unchanged except declared numeric `input` values;
- every profile keeps the same `case_set_hash` and context policy;
- no `MAX_RETURN`/`ROBUST_SCORE`-style hidden universal score is introduced;
- no automatic promotion occurs;
- worker count may not change seek identity or comparison evidence.

The operator reported Full PASS and then confirmed the exact local checkout:

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

Remote `main` also pointed at the same SHA at verification review time.

Therefore **E3 Multi-Battle Parameter Seeker is trusted Full-validated at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`.**

Detailed implementation checkpoint:

```text
E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md
```

## Stability architecture remains authoritative

The project continues under:

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
```

Key rules:

- Core Instrument DSL stays deterministic and narrow;
- adaptive learning/memory remains optional sidecar research;
- arbitrary cross-symbol reads/ranking remain outside Instrument DSL;
- parent/cascading features remain available through Provider -> immutable Context snapshot -> future read-only `ctx.*` binding;
- parent calculations do not execute inside DSL Runtime;
- hard guards/common execution authority cannot be bypassed by learned/add-on/context evidence without explicit future authority.

## Next mainline tranche: E4 causal characterization

E4 may now begin because E3 is trusted green.

E4 must remain evidence-only and deterministic. The first executable tranche should characterize actual tactic engagements by joining:

```text
entry signal_time
 -> causal TacticalObservation at that timestamp
 -> later realized trade outcome label
 -> deterministic descriptive strata / repeated failure-opportunity evidence
```

The causal observation and future outcome must remain separate fields. Future return/MFE/MAE/giveback/exit outcome may label an earlier observation for research, but may never become an input feature for that observation.

E4 must not:

- modify Parser / Runtime / Backtest / Broker semantics;
- introduce a learner or opaque universal score;
- auto-create a new DSL skill;
- use future outcome values as decision-time features;
- turn parent-context or multi-symbol research into a Core dependency.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- Core DSL Freeze / sidecar/provider/Add-on boundaries are authoritative.

Do not claim yet:

- E4 trusted implementation;
- a strongest/profitable tactic or parameter set;
- automatic parameter/skill promotion;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the separate broader repository status.
