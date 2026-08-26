# Quant DSL Current State

Status: **PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
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
15. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md`
16. `P1_TACTICAL_DATA_IMPLEMENTATION.md`
17. `PRODUCT_IMPLEMENTATION_PLAN.md`
18. `STAGE1_EXECUTION_POLICY.md`
19. `QUANT_DSL_PLAYBOOK.md`
20. `DSL_ENGINE_AUDIT.md`
21. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Governing architecture

Research remains micro-first and deployment remains layered.

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

Target deployment remains:

```text
Parent Feature Providers
 -> immutable BattlefieldContext
 -> Market / Sector / Group intelligence
 -> eligible Tactical Unit
 -> optional multi-symbol selection/ranking Add-on
 -> validated micro tactic
 -> common execution policy
 -> BrokerEmulator
```

Macro intelligence is an amplifier, not life support for a weak micro tactic.

## Core DSL freeze

Core remains responsible for deterministic local scalar/series/state/indicator calculation, causal tactic signals, supported completed MTF, explicit order intent and reproducible Backtest/Broker semantics.

Core still does **not** own:

- provider data acquisition/calculation;
- arbitrary peer-symbol reads;
- universe/ranking/allocation logic;
- sector/leader discovery;
- online learning;
- external DB/network calls during DSL evaluation;
- operational macro command wiring.

Only a future generic read-only context-reference mechanism is eligible for Core promotion, and only after the promotion criteria in `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` are met.

## Trusted Full checkpoints

Each exact SHA below received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

```text
E0  ac01525223f897f155de63f02529b0a6429a0882
E1  6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2  620f741730b0ae821fc48affd22b5420f38a6cac
E3A 06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3  cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4  560526b7f5af19462a57fd1e5b433bcbe5596500
E5  c1351152d58e4219b9998f0b35b7636f340dc986
E6  ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7  dc420d7f7961a4f0517b00c059d159b8face706c
E8  3256f1de6b9bb7e8b79342ea037edcd51125bcda
```

E4's first Full failure was an `environment issue`: the external Chart SSOT local checkout was stale. After fast-forwarding Chart SSOT to `7a43f0f52928045904d192deb7d8d532cb4c533e`, the same E4 DSL SHA passed without weakening E4 source/tests.

## E8 trusted state

`core/tactical_context_attribution.py` provides read-only attribution of frozen NEUTRAL micro evidence against exact causal OBSERVED `BattlefieldContext`, plus explicit non-operational deployment-policy evidence.

E8 keeps these distinctions:

```text
context attribution
!= policy validation
!= DeploymentDecision evidence
!= operational entry authority
```

Even validated policy evidence remains:

```text
operational_authority = false
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

Trusted E8 checkpoint:

```text
3256f1de6b9bb7e8b79342ea037edcd51125bcda
[PASS] Tactical P1 verification completed: mode=Full.
```

## PCTX1 current executable tranche

New module:

```text
core/parent_feature_provider.py
```

New regression:

```text
test_stage1_parent_feature_provider.py
```

Detailed checkpoint:

```text
PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTATION.md
```

### Provider / manifest contract

Public parent intelligence is now described through:

```text
ParentFeatureSpec
ParentFeatureManifest
ParentFeatureRegistry
ParentFeatureProviderResult
ParentFeatureProvider Protocol
ParentContextAssembly
ParentContextAssembler
```

Schemas:

```text
parent_feature_provider/v1
parent_feature_registry/v1
parent_context_assembly/v1
```

A stable manifest declares provider/version/layer/context plus typed feature semantics and staleness/missing policy. Current value types are `NUMBER`, `STRING`, and `BOOLEAN`; v1 causality is `CONFIRMED_ONLY`.

### Calculation remains outside DSL

The architecture is now executable as a contract:

```text
source adapter / provider-specific calculator
 -> ParentFeatureProviderResult
 -> ParentContextAssembler
 -> immutable BattlefieldContext
 -> E8 attribution / future read-only binder
```

Parser/Runtime never calls a provider.

### Fail-closed provider result

PCTX1 rejects:

- future provider result;
- stale result beyond manifest policy;
- missing required feature;
- undeclared feature;
- incompatible typed value;
- missing source authority;
- malformed dependency hashes.

Optional values remain explicitly absent instead of silently becoming zero/false.

### Cascading provenance

Provider results may depend on immutable parent `result_hash` values. Assembly requires every dependency to be present and no later than the child provider result.

The resulting `BattlefieldContext.metadata` carries manifest/result hashes and exact knowledge cutoff, so provider/version changes alter context identity even when feature values happen to match.

Assembly policy:

```text
PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY
```

### Still not implemented

- production KOSPI/KOSDAQ Market Provider;
- production Sector/Group/Leader-Follower Provider;
- historical intraday context timeline/frame;
- Runtime Context Binder;
- Instrument DSL `ctx.*` syntax/type binding;
- operational context entry-gate/Broker integration;
- production multi-symbol deployment selector.

PCTX1 itself changes none of Parser/Semantic/Runtime/Backtest/Broker/Chart authority.

## Validation status / nonclaims

May claim E0-E8 trusted Full PASS at the exact SHAs above and PCTX1 source/tests implemented awaiting Full.

Do not claim yet:

- trusted Full PASS for PCTX1;
- a production parent-feature calculation;
- a real profitable/generalizing macro slice;
- DSL parent-context consumption;
- operational deployment authorization;
- autonomous portfolio allocation;
- trained adaptive learner;
- adaptive lower-timeframe/tick deployment;
- live-trading readiness;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate boundary

Do not start PCTX2 concrete provider/timeline work, Core-facing `ctx.*` binding, or deployment gate wiring before PCTX1 receives trusted Full validation at an exact repository SHA.

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
