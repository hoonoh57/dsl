# Quant DSL Current State

Status: **LF1_TRUSTED_FULL_PASS / GCANCEL1_REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / REMEDIATION_REQUIRED**  
Updated: 2026-08-28 KST

## Session handoff and crash-safe recovery

`SESSION_HANDOFF.md` is the **primary human-readable handoff document** for this project.

`SESSION_RECOVERY.md` is the detailed crash-safe reconstruction procedure.

When the user sends `세션복구` in a new `dsl` project chat:

1. read `SESSION_HANDOFF.md` first for the human-level project story and next boundary;
2. inspect the tail of previous ChatGPT Project conversations for anything newer than the handoff;
3. recover the latest user-reported local SHA / focused test / Full test evidence from those conversations;
4. compare that point with current GitHub `main` and inspect intervening commits/files;
5. use this file and the authority documents to enforce architecture/permission boundaries;
6. reply briefly with only **개발철학(5개 이내) / 최근 한 일 / 앞으로 할 일**.

Important crash rule: neither the handoff nor this file is assumed to have been updated before an abrupt context-limit termination. Recovered exact local PASS evidence outranks stale `AWAITING_LOCAL_VALIDATION` text, while newer remote executable commits without local PASS remain untrusted.

The assistant cannot directly inspect unshared local-only filesystem state. Only when such state materially blocks recovery should a minimal `git status` / `git rev-parse HEAD` confirmation be requested.

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
12. `LF1_LEADER_FOLLOWER_RELATION_EVIDENCE_IMPLEMENTATION.md`
13. `CTXVAL1_REGISTERED_PARENT_CONTEXT_VALIDATION_ARENA_IMPLEMENTATION.md`
14. `CTXDEP1_VALIDATED_CONTEXT_DEPLOYMENT_POLICY_EVIDENCE_IMPLEMENTATION.md`
15. `CTXINT1_VALIDATED_CONTEXT_GATE_PREVIEW_IMPLEMENTATION.md`
16. `CTXINT2_VALIDATED_CONTEXT_BACKTEST_ENTRY_GATE_INTEGRATION.md`
17. `CTXINT3_VALIDATED_CONTEXT_NEXT_OPEN_TIMING_INTEGRATION.md`
18. earlier product/execution/playbook/audit checkpoints
19. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Trusted exact Full checkpoints

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
CTXINT3 7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1     5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
```

Recent operator evidence:

```text
CTXINT3: Ran 7 tests in 0.150s / OK / Full PASS
LF1:     Ran 7 tests in 0.058s / OK / Full PASS
```

## Governing architecture

Core DSL stays deterministic and single-instrument. Cross-symbol intelligence remains an optional Add-on.

```text
single-instrument causal snapshots
 -> bounded group evidence
 -> leader/follower relationship evidence
 -> later validated orchestration
 -> generic DSL order intent/cancel primitives
 -> common execution policy
 -> BrokerEmulator
```

The DSL must not calculate leader/follower roles, discover peers, rank symbols or allocate capital. Those remain Add-on responsibilities.

## LF1 trusted state

Exact trusted checkpoint:

```text
5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
Ran 7 tests in 0.058s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Human meaning: LF1 can identify one qualified leader and measure which followers tend to react after it, including follow rate and lag, while keeping those observations separate and non-operational.

LF1 still has no order, allocation, entry-gate or live-selection authority.

## GCANCEL1 remote-unvalidated state

Executable remote checkpoint:

```text
583c5362ca5ea57e62353a963cd5a2cfb0addfad
```

`BrokerEmulator.cancel_client_order(...)` now resolves an explicit `client_order_id` fail-closed and delegates the actual `ACCEPTED/TRIGGERED -> CANCELED` transition to the existing broker-owned `cancel(...)` path.

Focused regression file: `test_stage1_pending_order_cancel.py`.

Change audit from pre-tranche HEAD `76134a4c565a52e965980799a76dcba127c00355` shows executable changes only in:

```text
core/broker.py
test_stage1_pending_order_cancel.py
```

This is **not trusted yet** because no exact user-local focused + Full PASS has been reported.

## Immediate next boundary

Do not begin Parser/Backtest integration until GCANCEL1 is locally trusted.

Required local validation after pull:

```powershell
python -m unittest test_stage1_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

After both pass, the next executable micro-tranche is generic Instrument DSL / Backtest cancellation intent integration using explicit stable client identity.

That integration must remain feature-blind:

- no leader/follower syntax;
- no sector or peer-symbol syntax;
- no learned-policy authority;
- no alternative cancellation lifecycle outside BrokerEmulator.

Only after the generic cancel path is independently trusted should a later story compose:

```text
leader rebounds
 -> follower setup appears
 -> pending follower order exists
 -> leader/sector invalidates
 -> cancel pending order
```

## Remote CI environment

GitHub Actions for GCANCEL1 again failed before any executable job step was created (`steps=[]`). Classification remains `environment issue`; workflow/test/product guards are not weakened.

## Nonclaims

Do not claim profitable leader/follower edge, production leader/follower selection, validated generic DSL cancellation, live trading readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Current validation boundary

GCANCEL1 exists remotely but remains `REMOTE_UNVALIDATED`. Exact local focused + Full PASS is the trust gate.

Any later executable failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
