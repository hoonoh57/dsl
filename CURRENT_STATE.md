# Quant DSL Current State

Status: **E8_MACRO_CONTEXT_ATTRIBUTION_DEPLOYMENT_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-27 KST

## Authority

Read in this order:

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
14. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md`
15. `P1_TACTICAL_DATA_IMPLEMENTATION.md`
16. `PRODUCT_IMPLEMENTATION_PLAN.md`
17. `STAGE1_EXECUTION_POLICY.md`
18. `QUANT_DSL_PLAYBOOK.md`
19. `DSL_ENGINE_AUDIT.md`
20. `PROGRESS_CHECKPOINT_2026-08-26.md`

## Product direction

Final deployment remains layered:

```text
Parent battlefield feature providers
 -> BattlefieldContext
 -> Market / Regime
 -> Sector / Group / Narrative
 -> eligible Tactical Unit
 -> optional multi-symbol selection / ranking Add-on
 -> validated evolving micro tactic
 -> common execution policy
 -> BrokerEmulator
```

Research remains micro-first:

```text
minimal tactic family
 -> frozen BattleCases
 -> deterministic failure evidence
 -> causal characterization
 -> one legal structural skill child
 -> numeric Parameter Seeker where needed
 -> Train / Validation / OOS / Harsh
 -> ACCEPT / REJECT / REVIEW evidence
 -> append-only generation memory / explicit head
 -> lineage/evidence UI
 -> macro/parent-context attribution
 -> separately validated deployment policy
```

Macro remains an amplifier, not life support for a weak micro tactic.

## Core DSL freeze / parent inheritance

The governing rule remains:

> **Core DSL Freeze + Adaptive/Analysis Sidecar.**

Core owns deterministic local calculations, registered indicators/state, causal signals, one base timeframe, supported completed higher-timeframe MTF, explicit order intent and reproducible Backtest/Broker semantics.

Core does not own market-regime calculation, sector discovery, leader/follower scans, arbitrary peer-symbol reads/ranking, online learning, external DB/network calls or portfolio selection.

Cascading parent inheritance remains preserved through:

```text
Market / Sector / Group / Leader-Follower Provider
 -> immutable ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only Context Binder
 -> registered ctx.* value
 -> Instrument DSL local tactic
```

Still not implemented: general Parent Feature Provider framework, Feature Manifest registry, DSL `ctx.*` grammar/type binding, Runtime Context Binder and production Market/Sector/Group Providers.

The optional Multi-Symbol Add-on remains distinct from parent-context consumption. No production multi-symbol deployment selector exists.

## Trusted Full checkpoints

```text
E1  6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
E2  620f741730b0ae821fc48affd22b5420f38a6cac
E3A 06b52962a1b9b1212a11202ccef1f27b8d7f40c0
E3  cc3096c28ea8b9af718a1784df1b17af62bcde9a
E4  560526b7f5af19462a57fd1e5b433bcbe5596500
E5  c1351152d58e4219b9998f0b35b7636f340dc986
E6  ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
E7  dc420d7f7961a4f0517b00c059d159b8face706c
```

Each checkpoint above received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

E4's first Full attempt failed because the local external Chart SSOT checkout was stale; classification was `environment issue`. After fast-forwarding Chart SSOT to `7a43f0f52928045904d192deb7d8d532cb4c533e`, the same E4 DSL SHA passed without modifying E4 product/tests.

### E7 trusted state

E7 preserves E6 validation evidence append-only and projects one-skill lineage read-only. `GET /api/stage1/tactical/evolution/{family_id}` and the Tactical UI expose accepted generations, current explicit head, failure reasons, Train/Validation/OOS/Harsh evidence and rejected/reviewed attempts.

No promotion write route exists. Head mutation remains explicit `TacticalEvolutionStore.promote(...)` authority.

Trusted E7 checkpoint:

```text
dc420d7f7961a4f0517b00c059d159b8face706c
[PASS] Tactical P1 verification completed: mode=Full.
```

## E8 current executable tranche: Macro Context Attribution / Deployment Evidence

New executable:

```text
core/tactical_context_attribution.py
```

Schemas:

```text
tactical_context_attribution/v1
tactical_context_deployment/v1
```

### Attribution boundary

E8 accepts only a frozen `tactical_discovery/v1` profile whose discovery contract required `NEUTRAL` context. It joins the existing per-case results to a separate exact mapping:

```text
case_id -> OBSERVED BattlefieldContext
```

The mapping must cover every profile case exactly. Every context must pass `validate_for(result.knowledge_cutoff)`. Future context, missing context, extra context, missing layer/context/feature or incompatible mode fails closed.

Historical micro evidence is not rewritten:

```text
profile run_hash unchanged
case_set_hash unchanged
candidate_hash unchanged
per-case result evidence unchanged
```

### ContextSliceRule

Declared slice fields:

```text
slice_id
layer
context_id
feature_key
operator = EQ | GT | GTE | LT | LTE
value
metadata
```

This can inspect point-in-time parent features such as market regime, KOSPI strength, sector relative strength, leader strength or follower alignment without allowing Instrument DSL to query peer symbols directly.

### Attribution evidence

For the complete neutral baseline and each independent declared slice, E8 exposes:

```text
cases / active / no-trade
profitable_case_rate
average / median return
worst case return
worst MDD
cost per case
average MFE giveback
matched case IDs
slice-minus-baseline deltas
retained case / active-case rate
```

Policies:

```text
INDEPENDENT_DECLARED_CONTEXT_SLICES_NO_HIDDEN_SCORE
HISTORICAL_MICRO_PROFILE_READ_ONLY
ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY
```

There is no weighted macro score and no automatic `best regime` selection. Rule/context input order must not change `attribution_hash`.

### Deployment evidence boundary

`ContextDeploymentPolicy` is separate from attribution and requires an explicit `policy_id`, version, tactic, slice rule and attribution hash.

Evidence state is explicit:

```text
RESEARCH_ONLY
VALIDATED
```

`VALIDATED` additionally requires a separate `validation_evidence_hash`; E8 does not infer validation from training attribution.

Decision evaluation requires `BattlefieldContext.mode == DEPLOYMENT` and emits an existing `DeploymentDecision` plus deterministic policy/decision hashes.

However E8 v1 is **not operational wiring**. Even a policy carrying validated evidence reports:

```text
operational_authority = false
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

A future separately validated integration must connect deployment permission to the common entry gate. E8 itself does not call BrokerEmulator or modify DSL execution.

### Regression coverage

```text
test_stage1_tactical_context_attribution.py
```

It covers neutral baseline immutability, causal OBSERVED context, exact case coverage, future-context fail-close, deterministic rule/context ordering, explicit slice deltas, no hidden score, DEPLOYMENT-only policy decisions, RESEARCH_ONLY non-authority and separate validation-evidence requirement.

Detailed checkpoint:

```text
E8_MACRO_CONTEXT_ATTRIBUTION_DEPLOYMENT_IMPLEMENTATION.md
```

This E8 boundary has **not yet received trusted Full validation**.

## Validation status / nonclaims

May claim E1 through E7 trusted Full PASS at the exact SHAs above and E8 source/tests implemented awaiting Full.

Do not claim yet:

- trusted Full PASS for E8;
- that a real JMA macro/context slice is profitable or generalizes;
- a production Market/Sector/Group Parent Feature Provider;
- DSL `ctx.*` binding;
- functioning multi-symbol deployment selection;
- operational macro entry-gate/Broker authority;
- autonomous portfolio allocation;
- trained TacticalMemory/LocalBattlefieldLearner;
- adaptive 5m/3m/1m/tick deployment;
- live-trading readiness;
- repository-wide Chart or overall compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Immediate boundary

Do not wire E8 context decisions into production execution until this exact E8 executable boundary receives trusted Full validation.

Run:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before editing.
