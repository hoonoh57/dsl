# Quant DSL Progress Checkpoint — 2026-08-26 KST

Status: **E2_JMA_TRUSTED_FULL_PASS / E3A_SIDECAR_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

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

Result:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

The first E2 Full attempt failed because a 5m DSL regression test used the default deterministic 1d synthetic fixture.

Classification: **test defect**.

The product timeframe mismatch rule was correct and was not weakened. The test was remediated with an explicit deterministic 5m fixture.

Trusted executable checkpoint after remediation:

```text
620f741730b0ae821fc48affd22b5420f38a6cac
```

Result:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E2 JMA family catalog + generic legal skill-tree enforcement are trusted Full-validated at `620f741730b0ae821fc48affd22b5420f38a6cac`.

## E3A sidecar executable already added

After the E2 PASS, `core/tactical_observation.py` and `test_stage1_tactical_observation.py` were added.

They provide a causal point-in-time observation seam for JMA/trend/time/volatility/primitive price geometry and verify that future-bar changes cannot alter earlier observation features.

This executable boundary has **not yet** received a trusted Full PASS.

## Architecture correction: Core DSL Freeze + Adaptive Sidecar

A subsequent design review identified a larger risk: allowing every adaptive-learning idea to become a DSL/runtime requirement would make the language and execution kernel unstable and unpredictable.

The new authoritative policy is:

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
```

Governing rule:

> **Core DSL Freeze + Adaptive Sidecar.**

The Core DSL remains deterministic and narrow. Learning, memory, dynamic resolution selection and pattern research stay outside Parser / Runtime / Backtest / Broker unless a future capability independently earns promotion under strict criteria.

`ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` is now an optional sidecar research document rather than the main implementation sequence.

Deterministic equipment/hard guards have precedence over learned admissibility. Example: a future JMS2 range guard may block entry before any learner is consulted.

Adaptive timeframe remains external selection among separately validated tactic-family modes, not mutation of one running DSL candidate.

## Mainline restored

After the current E3A sidecar boundary is trusted green, development returns to the original tactic-evolution mainline:

```text
E3  Multi-Battle Parameter Seeker
E4  Causal Failure / Opportunity Characterizer
E5  Bounded Structural Skill Generator
E6  Train / Validation / OOS / Harsh Evolution Arena
E7  Evolution Evidence UI
E8  Macro Context Attribution / Deployment
```

TacticalMemory / LocalBattlefieldLearner / adaptive resolution research is deferred and non-blocking. It may resume later only when mainline evidence demonstrates a concrete need and it can remain behind stable sidecar interfaces.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- Core DSL Freeze / Adaptive Sidecar is now authoritative;
- E3A observation source/tests are implemented as a sidecar seam.

Do not claim yet:

- trusted Full PASS for E3A;
- Multi-Battle Parameter Seeker implementation;
- TacticalMemory or trained learner;
- adaptive 5m/3m/1m/tick deployment;
- learned profitability/generalization;
- live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the separate broader repository status.

## Immediate boundary

Do not stack another executable tranche on the unverified E3A boundary.

Run:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as `test defect / product defect / authority drift / environment issue / unknown` before editing.

If it passes, checkpoint E3A as trusted green and begin **E3 Multi-Battle Parameter Seeker** without changing Core DSL grammar/runtime semantics.
