# Quant DSL Current State

Status: **CTXINT2_TRUSTED_FULL_PASS / CTXINT3_NEXT_OPEN_TIMING_INTEGRATION_IMPLEMENTED_AWAITING_LOCAL_VALIDATION / REMEDIATION_REQUIRED**  
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
15. `CTXINT2_VALIDATED_CONTEXT_BACKTEST_ENTRY_GATE_INTEGRATION.md`
16. `CTXINT3_VALIDATED_CONTEXT_NEXT_OPEN_TIMING_INTEGRATION.md`
17. earlier product/execution/playbook/audit checkpoints
18. `PROGRESS_CHECKPOINT_2026-08-26.md`

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
CTXINT1 81903641b2877e16a3bcdcbf7ed1c1bcf1864ad9
CTXINT2 b3b547b9d2d0eaeee654790243f031a3bbb88198
```

Recent operator evidence:

```text
CTXINT1: Ran 7 tests in 0.129s / OK / Full PASS
CTXINT2: Ran 7 tests in 0.106s / OK / Full PASS
```

## Governing architecture

Core remains deterministic and single-instrument.

```text
registered causal parent evidence
 -> Train/Validation/OOS/Harsh validation
 -> validated policy evidence
 -> block-only composition proof
 -> existing Backtest entry-gate seam
 -> common execution policy
 -> BrokerEmulator
```

Parent context may remove an entry opportunity. It may not create one, bypass local guards, alter exits or submit Broker orders directly.

## CTXINT2 trusted state

Exact trusted checkpoint:

```text
b3b547b9d2d0eaeee654790243f031a3bbb88198
Ran 7 tests in 0.106s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

This proves blocking-only `bar_close` Backtest integration through the existing `entry_gate` seam while BrokerEmulator remains execution authority.

During CTXINT3 design, deferred entry orders were recognized as a separate signal-time/fill-time authority problem. Current CTXINT2 source is therefore hardened to reject LIMIT/STOP/STOP_LIMIT until that problem receives its own validation. The original exact trusted checkpoint remains the SHA above; the hardened source is part of the current untrusted CTXINT3 checkout.

## CTXINT3 current executable tranche

New executable/regression:

```text
core/tactical_context_integration_scope.py
core/tactical_context_next_open_integration.py
test_stage1_tactical_context_next_open_integration.py
```

Detailed checkpoint:

```text
CTXINT3_VALIDATED_CONTEXT_NEXT_OPEN_TIMING_INTEGRATION.md
```

CTXINT3 authorizes only the following causal timing for MARKET entries:

```text
completed bar t trigger + local guard + validated context permission
 -> shifted one bar
 -> may suppress/allow the already-existing next_open entry at bar t+1 open
```

The fill bar's unfinished context is never used to rescue the fill. First bar has no prior completed-bar authority. Exits remain outside the context gate.

Deferred entry orders remain fail-closed because a multi-bar pending order needs a separately declared rule for original signal permission versus later fill-time permission.

## Remote CI environment

GitHub Actions has repeatedly failed before executable steps receive a runner. Such failures remain classified `environment issue`; workflow/test/product guards are not weakened.

## Still not implemented / nonclaims

Do not claim yet:

- trusted Full PASS for CTXINT3;
- validated LIMIT/STOP/STOP_LIMIT context timing;
- production/live parent-context gating;
- empirical profitability of a real GROUP context rule;
- automatic cross-symbol allocation;
- live-trading readiness;
- repository-wide Chart/overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate validation boundary

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_tactical_context_next_open_integration.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Any executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
