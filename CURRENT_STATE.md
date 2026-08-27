# Quant DSL Current State

Status: **MSA3_TRUSTED_FULL_PASS / CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
19. `CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_ARENA_IMPLEMENTATION.md`
20. earlier product/execution/playbook/audit checkpoints
21. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

Every checkout below received:

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
MSA3    02904728cb0a39669e6809ba21c4e2dd8eb947e3
```

Recent focused evidence:

```text
PCTX2D: Ran 6 tests in 0.174s / OK
MSA1:   Ran 6 tests in 0.003s / OK
MSA2:   Ran 7 tests in 0.017s / OK
MSA3:   Ran 7 tests in 0.078s / OK
```

Each was followed by Full PASS at the exact SHA shown above.

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

Trusted parent calculation/publication path:

```text
PCTX2A deterministic MARKET provider
 -> PCTX2C exact root precomputation
 -> PCTX2D explicit dependency DAG
 -> descriptive SECTOR provider
 -> MSA3 research-only GROUP provider publication
```

Trusted multi-symbol evidence path:

```text
single-instrument causal state @ exact t
 -> MSA1 immutable InstrumentSignalSnapshot
 -> explicit SnapshotUniverse
 -> MSA2 bounded exact chronological GROUP evidence
 -> MSA3 bounded registered aggregate GROUP features
```

Provider calculation/I/O, universe discovery, peer ranking, allocation and adaptive learning remain outside Instrument DSL execution.

## MSA3 trusted state

Trusted exact checkpoint:

```text
02904728cb0a39669e6809ba21c4e2dd8eb947e3
Ran 7 tests in 0.078s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

MSA3 publishes only five aggregate GROUP features, with follower-dependent values optional/absent rather than defaulted. Publication remains `RESEARCH_ONLY`, `operational_authority=false`.

## CTXVAL1 current executable tranche

New module:

```text
core/tactical_context_validation.py
```

New regression:

```text
test_stage1_tactical_context_validation.py
```

Detailed checkpoint:

```text
CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_ARENA_IMPLEMENTATION.md
```

Schemas/policies:

```text
tactical_context_validation_arena/v1
tactical_context_validation_contract/v1
registered_context_validation_slice/v1
PARTITIONED_E8_ATTRIBUTION_TRAIN_VALIDATION_OOS_HARSH_DECLARED_AXES_NO_HIDDEN_SCORE
EXACT_REGISTERED_PCTX1_OBSERVED_CONTEXT_ONLY
```

### Exact registered context requirement

Every validation case uses a frozen NEUTRAL `tactical_discovery/v1` result and an exact OBSERVED PCTX1 assembly context:

```text
context.as_of == case.knowledge_cutoff
parent_feature_contract == parent_context_assembly/v1
exact parent_feature_knowledge_cutoff
non-empty immutable manifest/result hashes
required registered manifest hash present
```

There is no provider call, nearest/fill-forward, tactic replay, Backtest mutation or Broker wiring in CTXVAL1.

### Partition evidence

CTXVAL1 requires exactly one TRAIN, VALIDATION and OOS partition plus at least one HARSH partition. HARSH requires `adverse_reason`; case IDs are globally disjoint; all partitions use the same candidate hash.

E8 `TacticalContextAttributor` is run independently per partition. Each registered slice is judged against explicit no-score retained-case, return, drawdown, profitable-rate, cost and MFE-giveback tolerances.

A slice must survive all holdouts. TRAIN-positive but OOS-regressing evidence fails.

### Output authority

Passing slices receive a slice-specific `validation_evidence_hash` and may become *evidence-eligible* for a separately declared E8 deployment policy. CTXVAL1 itself remains:

```text
operational_authority = false
execution_integration = EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

It does not create allowed/blocked symbols, allocation, entry gates, DeploymentDecision or Broker orders.

## Remote CI environment

Recent GitHub Actions runs repeatedly failed before executable steps obtained a runner. These are `environment issue`; workflow/test guards have not been weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for CTXVAL1;
- empirical OOS benefit from real GROUP context;
- production GROUP deployment policy;
- automatic cross-symbol selection or portfolio allocation;
- operational parent-context entry gate;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

Validate CTXVAL1 before any GROUP DEPLOYMENT use or selection-policy work:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_validation.py
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
