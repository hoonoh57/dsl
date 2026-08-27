# Quant DSL Current State

Status: **PCTX2B_PARENT_CONTEXT_FRAME_BINDER_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-27 KST

## Authority order

1. `EVOLVING_MICRO_WARRIOR_PLAN.md`
2. `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`
3. `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`
4. `MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md`
5. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md`
6. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md`
7. `MULTI_LAYER_DSL_ARCHITECTURE.md`
8. `E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md`
9. `E4_CAUSAL_FAILURE_OPPORTUNITY_CHARACTERIZER_IMPLEMENTATION.md`
10. `E5_BOUNDED_STRUCTURAL_SKILL_GENERATOR_IMPLEMENTATION.md`
11. `E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md`
12. `E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTATION.md`
13. `E8_MACRO_CONTEXT_ATTRIBUTION_DEPLOYMENT_IMPLEMENTATION.md`
14. `PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md`
15. `PCTX2B_PARENT_CONTEXT_FRAME_BINDER_IMPLEMENTATION.md`
16. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md`
17. `P1_TACTICAL_DATA_IMPLEMENTATION.md`
18. `PRODUCT_IMPLEMENTATION_PLAN.md`
19. `STAGE1_EXECUTION_POLICY.md`
20. `QUANT_DSL_PLAYBOOK.md`
21. `DSL_ENGINE_AUDIT.md`
22. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Governing architecture

Research remains micro-first while target deployment remains layered.

```text
minimal tactic family
 -> frozen BattleCases
 -> deterministic failure evidence
 -> causal characterization
 -> one legal structural skill
 -> bounded numeric seeking
 -> Train / Validation / OOS / Harsh
 -> ACCEPT / REJECT / REVIEW
 -> append-only generation memory
 -> lineage/evidence UI
 -> parent/macro context attribution
 -> separately validated deployment evidence
```

Target deployment:

```text
Parent Feature Providers
 -> immutable point-in-time context
 -> Market / Sector / Group intelligence
 -> eligible Tactical Unit
 -> optional multi-symbol selection/ranking Add-on
 -> validated micro tactic
 -> common execution policy
 -> BrokerEmulator
```

Macro intelligence remains an amplifier, not life support for a weak micro tactic.

## Core DSL freeze

Core remains responsible for deterministic local scalar/series/state/indicator calculation, causal tactic signals, supported completed MTF, explicit order intent and reproducible Backtest/Broker semantics.

Core still does **not** own provider calculation/I/O, arbitrary peer-symbol reads, universe/ranking/allocation, sector/leader discovery, online learning, external DB/network calls during tactic evaluation, or operational macro command wiring.

Only a future generic read-only context-reference mechanism may be promoted into Core, after repeated tactic-family need and the promotion criteria in `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` are satisfied.

## Trusted Full checkpoints

Every exact checkout below received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

```text
E0    ac01525223f897f155de63f02529b0a6429a0882
E1    6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2    620f741730b0ae821fc48affd22b5420f38a6cac
E3A   06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3    cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4    560526b7f5af19462a57fd1e5b433bcbe5596500
E5    c1351152d58e4219b9998f0b35b7636f340dc986
E6    ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7    dc420d7f7961a4f0517b00c059d159b8face706c
E8    3256f1de6b9bb7e8b79342ea037edcd51125bcda
PCTX1 866bf0a5a25bf6759d1b264d62efcf9f1f277446
```

E4's first Full failure was an `environment issue`: the external Chart SSOT local checkout was stale. After fast-forwarding Chart SSOT to `7a43f0f52928045904d192deb7d8d532cb4c533e`, the same E4 DSL SHA passed without weakening E4 product/tests.

## PCTX1 trusted state

`core/parent_feature_provider.py` is now the trusted provider/manifest production contract.

It defines:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider Protocol
ParentContextAssembly
ParentContextAssembler
```

Provider-specific calculation stays outside Instrument DSL and publishes immutable typed results. PCTX1 fails closed on future/stale results, required-feature absence, undeclared features, type mismatch, missing source and malformed dependencies.

Trusted PCTX1 checkpoint:

```text
866bf0a5a25bf6759d1b264d62efcf9f1f277446
[PASS] Tactical P1 verification completed: mode=Full.
```

## PCTX2B current executable tranche

PCTX2B was selected before PCTX2A concrete providers because intraday semantics require an exact decision-time context transport contract before production calculations are coupled to it.

New executable:

```text
core/parent_context_frame.py
```

New regression:

```text
test_stage1_parent_context_frame.py
```

Detailed checkpoint:

```text
PCTX2B_PARENT_CONTEXT_FRAME_BINDER_IMPLEMENTATION.md
```

Schemas:

```text
parent_context_frame/v1
parent_context_binding/v1
```

### Exact causal timeline

A `ParentContextFrame` contains precomputed PCTX1 assemblies for one target instrument.

Every point requires:

```text
target_time
 == assembly.knowledge_cutoff
 == assembly.context.as_of
```

Resolution policy:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
```

There is no nearest-time substitution, interpolation, hidden carry-forward or provider call during lookup.

### Fixed semantic topology

Every point in one frame must carry the same manifest-hash topology. Provider/version drift inside a frame fails closed.

The frame records the PCTX1 `registry_hash`; changing provider semantics/result/context at any point changes deterministic frame identity.

### Generic read-only sidecar binder

`ParentContextBinder` resolves explicit registered feature IDs against one exact-time frozen context.

Policy:

```text
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
```

It re-checks public type semantics and preserves optional absence explicitly as:

```text
present = false
value = null
```

This binder is **not** the Instrument DSL Runtime Context Binder. Parser/Semantic/Runtime still have no executable `ctx.*` capability.

### Still not implemented

- PCTX2A production KOSPI/KOSDAQ Market Parent Feature Provider;
- production Sector/Group/Leader-Follower Provider;
- source acquisition adapters standardized for parent context;
- Instrument DSL `ctx.*` syntax/type binding;
- Parser/Semantic/Runtime context-reference support;
- operational deployment entry-gate/Broker integration;
- production multi-symbol deployment selector.

PCTX2B changes none of Parser/Semantic/Runtime/Backtest/Broker/Chart authority.

## Validation status / nonclaims

May claim E0-E8 and PCTX1 trusted Full PASS at the exact SHAs above. PCTX2B source/tests are implemented awaiting Full.

Do **not** claim yet:

- trusted Full PASS for PCTX2B;
- a production parent-feature calculation;
- a real profitable/generalizing macro slice;
- executable DSL parent-context consumption;
- operational deployment authorization;
- autonomous portfolio allocation;
- trained adaptive learner;
- adaptive lower-timeframe/tick deployment;
- live-trading readiness;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate boundary

Do not begin PCTX2A concrete Market Provider work, Core-facing `ctx.*` binding, or deployment gate wiring before PCTX2B receives trusted Full validation at an exact repository SHA.

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If Full fails, classify the first executable failure exactly as one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before changing code.
