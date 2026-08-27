# Quant DSL Current State

Status: **MSA2_TRUSTED_FULL_PASS / MSA3_REGISTERED_GROUP_PARENT_FEATURE_PUBLICATION_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
18. `MSA3_REGISTERED_GROUP_PARENT_FEATURE_PUBLICATION_IMPLEMENTATION.md`
19. earlier product/execution/playbook/audit checkpoints
20. `PROGRESS_CHECKPOINT_2026-08-26.md`

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
MSA2    3a5a2ece658ead28a1822ef7482a3d284d12e2d6
```

Recent focused evidence:

```text
PCTX2D: Ran 6 tests in 0.174s / OK
MSA1:   Ran 6 tests in 0.003s / OK
MSA2:   Ran 7 tests in 0.017s / OK
```

Each was followed by the consolidated Full PASS at the exact SHA above.

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

Trusted multi-symbol evidence path:

```text
single-instrument causal state @ exact t
 -> MSA1 immutable InstrumentSignalSnapshot
 -> explicit SnapshotUniverse
 -> MSA2 bounded exact chronological GROUP evidence
```

Provider calculation/I/O, universe discovery, peer ranking, allocation and adaptive learning remain outside Instrument DSL execution.

## MSA2 trusted state

Trusted exact checkpoint:

```text
3a5a2ece658ead28a1822ef7482a3d284d12e2d6
Ran 7 tests in 0.017s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA2 is still observation-only. Leader/follower/breadth/persistence evidence is descriptive and has no operational authority.

## MSA3 current executable tranche

New module:

```text
core/group_evidence_parent_feature_provider.py
```

New regression:

```text
test_stage1_group_evidence_parent_feature_provider.py
```

Detailed checkpoint:

```text
MSA3_REGISTERED_GROUP_PARENT_FEATURE_PUBLICATION_IMPLEMENTATION.md
```

MSA3 does not run MSA1/MSA2 analysis. It reads only an exact immutable timeline of already-computed `multi_symbol_group_evidence/v1` results and verifies each MSA2 `result_hash` against its payload.

Resolution policy:

```text
EXACT_PRECOMPUTED_MSA2_EVIDENCE_NO_NEAREST_NO_FILL_FORWARD
```

Publication policy:

```text
EXACT_PRECOMPUTED_MSA2_EVIDENCE_PLUS_EXPLICIT_SECTOR_DEPENDENCY_NO_PEER_RUNTIME_READ_NO_DEPLOYMENT_AUTHORITY
publication_state = RESEARCH_ONLY
operational_authority = false
```

### Registered GROUP features

For namespace `semiconductor`, the manifest is deliberately restricted to five aggregate values:

```text
group.semiconductor_comparison_eligible_rate
group.semiconductor_favorable_breadth_rate
group.semiconductor_leader_persistence_rate
group.semiconductor_leader_follower_spread       optional
group.semiconductor_follower_favorable_rate      optional
```

No leader/follower symbol identity, rank list, allowed/blocked symbol list, slot/allocation, gate or order authority is published.

When follower evidence is absent, the two follower-dependent values remain `OPTIONAL_ABSENT`; they are not defaulted to zero.

### PCTX2D dependency seam

The GROUP provider requires exactly one configured exact-time SECTOR result. The GROUP `ParentFeatureProviderResult` carries that SECTOR `result_hash` in `dependency_result_hashes`, preserving:

```text
MARKET -> SECTOR -> GROUP
```

MSA3 regression uses only an `OBSERVED` PCTX2D frame plus the generic registered binder. It does not execute the new GROUP feature through CTXBT1/Backtest in this tranche.

Registered publication is not deployment validation.

## Existing multi-symbol vertical slice

`core/multi_symbol.py` remains the earlier deterministic scenario/cohort orchestration engine and is not modified by MSA1-MSA3. New peer/group research uses immutable snapshots/evidence rather than cross-symbol Instrument DSL syntax.

## Remote CI environment

Recent GitHub Actions jobs have repeatedly terminated before executable steps with no assigned runner (`runner_id=0`). These incidents are classified:

```text
environment issue
```

No workflow/test/product guard has been weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for MSA3;
- validated OOS benefit from GROUP context;
- GROUP feature DEPLOYMENT eligibility;
- automatic cross-symbol selection/permission;
- portfolio slot/allocation authority;
- operational macro gate;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate MSA3 before any GROUP DEPLOYMENT use or selection-policy work:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_group_evidence_parent_feature_provider.py
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
