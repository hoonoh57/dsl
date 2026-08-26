# Quant DSL Progress Checkpoint — 2026-08-26 KST

Status: **E2_JMA_TRUSTED_FULL_PASS / E3A_CAUSAL_OBSERVATION_AWAITING_TRUSTED_FULL**

## Trusted Full checkpoints

### Earlier E0 / initial E1-E2 foundation

Trusted executable checkpoint:

```text
ac01525223f897f155de63f02529b0a6429a0882
```

Result:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

### E1 Korean regular-session contract

Trusted executable checkpoint:

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
```

The operator pulled `main`, received `Already up to date.`, and then reported:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E1 is trusted Full-validated at that checkpoint.

### E2 JMA family / legal skill-tree contract

The first E2 Full attempt failed in the new JMA catalog regression because the test executed a `5m` DSL against the BacktestEngine's default deterministic `1d` synthetic fixture.

Classification: **test defect**.

The product timeframe mismatch check was correct and was not weakened. Remediation commit:

```text
fb55435e17618cead68f1d8474cc65e40a198ca3
```

The test was changed to use an explicit deterministic `5m` fixture.

After pulling current `main`, the operator reported the remediated consolidated boundary:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

The remote `main` executable HEAD immediately before the new learning work was:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
```

Therefore **E2 JMA family catalog + generic legal skill-tree enforcement are trusted Full-validated at `620f741730b0ae821fc48affd22b5420f38a6cac`.**

## New authoritative learning direction

`ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` is now the micro-learning sequencing addendum.

The required local-warrior loop is:

```text
TACTIC OPPORTUNITY
 -> CAUSAL LOCAL OBSERVATION
 -> TACTICAL MEMORY
 -> SURVIVAL / OPPORTUNITY / UNCERTAINTY ESTIMATE
 -> RESOLUTION / EXECUTION MODE SELECTION
 -> ENTER / WAIT / ABSTAIN
 -> ACTUAL + SHADOW EVIDENCE
 -> NEXT TRAINING MEMORY VERSION
```

Macro regime remains optional later reconnaissance. Local learning must work without macro life support.

Adaptive timeframe is explicitly a **family-level validated resolution-mode selection problem**, not runtime self-modification of one DSL candidate. The current Stage 1 DSL cannot silently request arbitrary lower-timeframe or tick evidence.

## E3A executable boundary now added

`core/tactical_observation.py` introduces the first causal JMA/local battlefield observation contract.

Initial features include:

- JMA fast/slow values, spread, slope, spread velocity, acceleration and crossover age/state;
- SMA60 slope and price distance;
- ATR/range, volume ratio/change and gap proxy;
- recent 3/6/12-bar returns and return from session open;
- session-high/session-low location;
- time from open, time to close and session progress;
- primitive price geometry including higher-high/higher-low ratios, swing-high/swing-low slopes, body direction, wick asymmetry and breakout distance.

The first implementation intentionally does **not** yet train a model or select a different timeframe. It only gives the warrior a deterministic causal sensory snapshot.

`test_stage1_tactical_observation.py` checks:

- time/JMA/trend/volatility/price-structure features are exposed;
- rising highs and lows remain observable even when candle-body direction is weak/mixed;
- changing only future bars cannot change an earlier observation's feature values;
- timeframe mismatch fails closed;
- insufficient observation warm-up fails closed.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- the adaptive learning architecture is documented;
- E3A causal observation source/tests are implemented.

Do not claim yet:

- trusted Full PASS for E3A;
- a trained LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- learned profitability/generalization;
- live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains separate broader repository status.

## Next boundary

Pull current `main` and run:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as `test defect / product defect / authority drift / environment issue / unknown` before editing.

If E3A is green, the next micro-tranche is **E3B TacticalExperience / TacticalMemory**, not an immediate opaque learner or live adaptive timeframe switch.
