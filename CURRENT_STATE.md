# Quant DSL Current State

Status: **CTXDEP1_TRUSTED_FULL_PASS / CTXINT1_VALIDATED_CONTEXT_GATE_PREVIEW_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
14. `CTXINT1_VALIDATED_CONTEXT_GATE_PREVIEW_IMPLEMENTATION.md`
15. earlier product/execution/playbook/audit checkpoints
16. `PROGRESS_CHECKPOINT_2026-08-26.md`

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
CTXDEP1 804baea25f29d1c77f2984d67e37dbb5ebb1160e
```

Recent operator evidence:

```text
CTXVAL1: Ran 7 tests in 0.073s / OK / Full PASS
CTXDEP1: Ran 6 tests in 0.028s / OK / Full PASS
```

## Governing architecture

Core remains deterministic and single-instrument.

```text
PCTX provider calculation outside DSL
 -> exact frozen parent context
 -> registered read-only ctx.*
 -> existing single-instrument tactic
 -> common execution policy
 -> BrokerEmulator
```

Cross-symbol and macro intelligence remain staged outside Instrument DSL:

```text
MSA1 immutable snapshots
 -> MSA2 bounded group evidence
 -> MSA3 research-only GROUP publication
 -> CTXVAL1 Train/Validation/OOS/Harsh validation
 -> CTXDEP1 validated deployment-policy evidence
 -> CTXINT1 preview-only gate composition
```

## CTXDEP1 trusted state

Exact trusted checkpoint:

```text
804baea25f29d1c77f2984d67e37dbb5ebb1160e
Ran 6 tests in 0.028s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

CTXDEP1 proves that only an independently validated CTXVAL1 condition can be converted into deployment-policy evidence while preserving tactic/rule/manifest/holdout provenance. It remains non-operational.

The initial source-scan failure at `ec1f5cef...` was classified `test defect`; only the regression/checkpoint was corrected before the trusted PASS.

## CTXINT1 current executable tranche

New files:

```text
core/tactical_context_gate_preview.py
test_stage1_tactical_context_gate_preview.py
CTXINT1_VALIDATED_CONTEXT_GATE_PREVIEW_IMPLEMENTATION.md
```

CTXINT1 verifies the intended composition before any operational gate is installed:

```text
effective entry eligibility
 = tactic trigger
 AND local hard-guard pass
 AND validated parent-context permission
```

It requires an exact DEPLOYMENT parent-context frame, exact registry/manifest/feature identity and the validated CTXDEP1 tactic/policy identity.

The preview explicitly proves:

```text
parent context cannot create a new entry opportunity
parent context cannot bypass a failed local hard guard
parent context may only remove an existing local opportunity
```

CTXINT1 remains:

```text
operational_authority = false
execution_integration = PREVIEW_ONLY_NOT_INSTALLED_AS_BACKTEST_ENTRY_GATE_OR_BROKER
```

Parser, Semantic, Runtime, BacktestEngine and BrokerEmulator are not changed by this tranche.

## Remote CI environment

GitHub Actions has repeatedly failed before executable steps receive a runner. Such failures are classified `environment issue`; workflow/test/product guards are not weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for CTXINT1;
- operational parent-context entry gating;
- actual Broker order suppression from validated context policy;
- empirical profitability of a real GROUP context rule;
- automatic cross-symbol selection/allocation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_gate_preview.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
