# Quant DSL Current State

Status: **CTXVAL1_TRUSTED_FULL_PASS / CTXDEP1_VALIDATED_CONTEXT_DEPLOYMENT_POLICY_EVIDENCE_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-28 KST

## Authority order

1. `EVOLVING_MICRO_WARRIOR_PLAN.md`
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md`
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md`
7. `MULTI_LAYER_DSL_ARCHITECTURE.md`
8. E3-E8 implementation checkpoints
9. PCTX1/PCTX2B/CTXDSL1/CTXBT1 checkpoints
10. PCTX2A/PCTX2C/PCTX2D checkpoints
11. MSA1/MSA2/MSA3 checkpoints
12. `CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_ARENA_IMPLEMENTATION.md`
13. `CTXDEP1_VALIDATED_CONTEXT_DEPLOYMENT_POLICY_EVIDENCE_IMPLEMENTATION.md`
14. earlier product/execution/playbook/audit checkpoints
15. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

Every checkout below received Tactical P1 Full PASS at the exact SHA:

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
CTXVAL1 db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
```

Recent focused evidence:

```text
MSA3:   Ran 7 tests in 0.078s / OK
CTXVAL1: Ran 7 tests in 0.073s / OK
```

Both were followed by Full PASS at their exact trusted SHA.

## Governing architecture

Core remains deterministic and single-instrument.

```text
PCTX provider calculation/precompute outside DSL
 -> exact frozen parent context
 -> read-only registered ctx.*
 -> Backtest exact binding
 -> existing execution policy
 -> BrokerEmulator
```

Cross-symbol research remains outside Instrument DSL:

```text
MSA1 immutable per-symbol snapshots
 -> MSA2 bounded group evidence
 -> MSA3 research-only aggregate GROUP publication
 -> CTXVAL1 Train/Validation/OOS/Harsh evidence
 -> CTXDEP1 explicit validated deployment-policy evidence
```

No peer-symbol runtime reads, universe discovery, ranking, allocation or provider calls are added to Instrument DSL.

## CTXVAL1 trusted state

Exact trusted checkpoint:

```text
db9d9ddeeec55f2774d7a2d873ec2f19d77726b4
Ran 7 tests in 0.073s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXVAL1 proves the registered-context validation machinery is executable across explicit TRAIN, VALIDATION, OOS and HARSH partitions. It produces slice-specific validation evidence only and remains non-operational.

The initial failure at `d2abaeed...` was classified `test defect`; only the malformed regression fixture was corrected before the final trusted PASS.

## CTXDEP1 current executable tranche

New module/regression:

```text
core/tactical_context_deployment_evidence.py
test_stage1_tactical_context_deployment_evidence.py
```

Detailed checkpoint:

```text
CTXDEP1_VALIDATED_CONTEXT_DEPLOYMENT_POLICY_EVIDENCE_IMPLEMENTATION.md
```

CTXDEP1 accepts only an intact CTXVAL1 arena and one independently validated PASS slice. It verifies arena identity, slice status, registered feature/manifest identity and partition attribution consistency, then creates an E8 `ContextDeploymentPolicy` anchored to the exact CTXVAL1 `validation_evidence_hash`.

Output remains:

```text
policy_evidence_validated = true
operational_authority = false
execution_integration = POLICY_EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

It does not install an entry gate or call Backtest/Broker.

## Remote CI environment

Recent GitHub Actions runs have repeatedly terminated before executable steps received a runner. Those failures are classified:

```text
environment issue
```

No workflow/test/product guard has been weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for CTXDEP1;
- empirical profitability of a real GROUP deployment rule;
- operational parent-context entry gate;
- automatic cross-symbol selection/allocation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_deployment_evidence.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
