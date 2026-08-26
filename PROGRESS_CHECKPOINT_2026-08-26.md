# Quant DSL Progress Checkpoint — 2026-08-26 KST

Status: **E3_TRUSTED_FULL_PASS / E4_CAUSAL_CHARACTERIZER_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

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

Trusted contract:

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
- every profile keeps the same `case_set_hash` and context policy;
- no hidden universal score is introduced;
- no automatic promotion occurs;
- worker count may not change seek identity or comparison evidence.

The operator reported Full PASS and confirmed the exact local checkout:

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

## E4 executable boundary now added

`core/tactical_characterization.py` adds the first **Causal Failure / Opportunity Characterizer**.

Its evidence flow is:

```text
trusted tactical_discovery profile
 + exact frozen BattleCases
 + actual closed-trade signal_time
        ↓
causal TacticalObservation at signal_time
        ↓
compact causal feature subset
        │
        ├──────── future boundary ────────┐
        ↓                                 ↓
causal_features                    future outcome labels
                                   return / MFE / MAE
                                   giveback / exit / hold
        └─────────────────┬───────────────┘
                          ↓
             deterministic descriptive strata
```

The two identities are separated:

```text
causal_dataset_hash
labeled_dataset_hash
```

Changing only future labels must not change `causal_dataset_hash`.

Initial compact causal axes are:

```text
minutes_from_open
jma_spread_atr
sma60_slope_pct
price_to_sma60_atr
atr_pct
volume_ratio
higher_high_ratio
higher_low_ratio
```

E4 reports value-only quantile strata with support, profitable rate, return/MFE/MAE/giveback and outcome-tag counts. It also carries existing case-level `TacticalFailureAnalyzer` evidence.

Explicit boundaries:

- causal features and future outcomes are separate payloads;
- exact profile/BattleCase identity is required;
- no hidden universal score;
- no learner;
- no live gate;
- no automatic SkillSpec generation;
- no Parser/Runtime/Backtest/Broker modification.

Regression coverage in `test_stage1_tactical_characterization.py` verifies causal/label separation, future-label mutation isolation, exact BattleCase identity and deterministic result hashes/strata.

Detailed implementation checkpoint:

```text
E4_CAUSAL_FAILURE_OPPORTUNITY_CHARACTERIZER_IMPLEMENTATION.md
```

This E4 executable boundary has **not yet received trusted Full validation**.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- Core DSL Freeze / sidecar/provider/Add-on boundaries are authoritative;
- E4 source/tests are implemented awaiting Full validation.

Do not claim yet:

- trusted Full PASS for E4;
- a strongest/profitable tactic or parameter set;
- automatic parameter/skill promotion;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the separate broader repository status.

## Immediate boundary

Do not begin E5 executable work before E4 is trusted green.

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
