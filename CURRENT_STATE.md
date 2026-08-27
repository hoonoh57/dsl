# Quant DSL Current State

Status: **MSA1_TRUSTED_FULL_PASS / MSA2_BOUNDED_GROUP_EVIDENCE_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-27 KST

## Authority order

1. `EVOLVING_MICRO_WARRIOR_PLAN.md`
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md`
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md`
7. `MULTI_LAYER_DSL_ARCHITECTURE.md`
8. E3-E8 implementation checkpoints
9. `PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md`
10. `PCTX2B_PARENT_CONTEXT_FRAME_BINDER_IMPLEMENTATION.md`
11. `CTXDSL1_GENERIC_PARENT_CONTEXT_REFERENCE_IMPLEMENTATION.md`
12. `CTXBT1_EXACT_PARENT_CONTEXT_BACKTEST_INTEGRATION.md`
13. `PCTX2A_MARKET_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md`
14. `PCTX2C_EXACT_ROOT_PROVIDER_FRAME_ORCHESTRATION.md`
15. `PCTX2D_DEPENDENCY_DAG_SECTOR_PROVIDER_IMPLEMENTATION.md`
16. `MSA1_IMMUTABLE_MULTI_SYMBOL_SNAPSHOT_EVIDENCE_IMPLEMENTATION.md`
17. `MSA2_BOUNDED_GROUP_LEADER_FOLLOWER_BREADTH_EVIDENCE_IMPLEMENTATION.md`
18. earlier product/execution/playbook/audit checkpoints
19. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

Every exact checkout below received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

```text
E0     ac01525223f897f155de63f02529b0a6429a0882
E1     6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2     620f741730b0ae821fc48affd22b5420f38a6cac
E3A    06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3     cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4     560526b7f5af19462a57fd1e5b433bcbe5596500
E5     c1351152d58e4219b9998f0b35b7636f340dc986
E6     ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7     dc420d7f7961a4f0517b00c059d159b8face706c
E8     3256f1de6b9bb7e8b79342ea037edcd51125bcda
PCTX1  866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
PCTX2C  7aee063932e0d70d38c2e7f876b140d049029771
PCTX2D  6de666c277d1a6d7ffb47fd9e6093e50b34ebb45
MSA1    adaef963dce717b252f2575896a74462c8a277a2
```

Recent focused evidence:

```text
PCTX2D: Ran 6 tests in 0.174s / OK
MSA1:   Ran 6 tests in 0.003s / OK
```

Both were followed by Full PASS at their exact trusted SHA.

## Governing architecture

Core remains deterministic and single-instrument.

```text
PCTX1 typed/versioned provider contract
 -> PCTX2B exact frozen frame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 Backtest exact binding
 -> existing execution policy
 -> BrokerEmulator
```

Trusted parent calculation/precompute path:

```text
PCTX2A deterministic MARKET provider
 -> PCTX2C exact root precomputation
 -> PCTX2D explicit dependency DAG
 -> descriptive SECTOR provider
```

Trusted multi-symbol evidence seam:

```text
single-instrument causal state @ exact t
 -> MSA1 InstrumentSignalSnapshot
 -> explicit SnapshotUniverse
 -> observation-only leaderboards / Pareto
```

Provider calculation/I/O, universe discovery, peer ranking, allocation and adaptive learning remain outside Instrument DSL execution.

## MSA1 trusted state

Trusted exact checkpoint:

```text
adaef963dce717b252f2575896a74462c8a277a2
Ran 6 tests in 0.003s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA1 is immutable point-in-time evidence only. It exposes no deployment authority and does not call DSLRuntime, BacktestEngine, BrokerEmulator or ParentFeatureProvider.

## MSA2 current executable tranche

New module:

```text
core/multi_symbol_group_evidence.py
```

New regression:

```text
test_stage1_multi_symbol_group_evidence.py
```

Detailed checkpoint:

```text
MSA2_BOUNDED_GROUP_LEADER_FOLLOWER_BREADTH_EVIDENCE_IMPLEMENTATION.md
```

Schema/policies:

```text
multi_symbol_group_evidence/v1
multi_symbol_group_evidence_policy/v1
STATIC_EXPLICIT_UNIVERSE_EXACT_CHRONOLOGICAL_POINTS
OBSERVATION_ONLY_BOUNDED_STATIC_UNIVERSE_LEADER_FOLLOWER_BREADTH_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY
```

MSA2 consumes a bounded chronological sequence of exact MSA1 points. v1 requires one stable universe ID, ordered symbol topology, source authority and stable candidate/family/generation identity per symbol across the frame.

An explicit `GroupEvidencePolicy` declares one comparison metric, MAX/MIN direction, favorable threshold, leader count, lookback points and hard `max_symbols`/`max_points` bounds.

It computes descriptive:

```text
comparison eligible breadth
favorable breadth
current leader/follower sets
leader/follower metric means and direction-normalized spread
follower favorable rate
current leader persistence over bounded lookback
```

No hidden score is used. `leader_symbols` is observation evidence, not permission or selection authority.

MSA2 always returns:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

and does not emit allowed/blocked symbols, allocation, entry gate, DeploymentDecision or Broker orders.

If comparison eligibility collapses so no follower remains, follower aggregates are explicit null values rather than fabricated zeroes.

## Existing multi-symbol vertical slice

`core/multi_symbol.py` remains the earlier deterministic scenario/cohort orchestration engine and is not modified by MSA1/MSA2. New peer/group research should use immutable snapshots rather than add cross-symbol syntax to Instrument DSL.

## Remote CI environment

Recent GitHub Actions jobs for these parent/add-on tranches have repeatedly terminated with no executable steps and no assigned runner (`runner_id=0`). Those incidents are classified:

```text
environment issue
```

No workflow/test/product guard has been weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for MSA2;
- production GROUP/leader-follower/breadth edge;
- MSA2-derived registered GROUP parent features;
- validated cross-symbol selection edge;
- automatic symbol permission or portfolio allocation;
- evidence that MARKET/SECTOR/GROUP context improves OOS profitability;
- operational macro deployment authority;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate MSA2 before publishing any MSA2-derived GROUP feature or adding deployment selection:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_multi_symbol_group_evidence.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If an executable failure occurs, classify the first failure exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```
