# E8 Macro Context Attribution / Deployment — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## 1. Trusted predecessor

E7 Evolution Memory / Evidence UI was operator-validated at exact DSL checkout:

```text
dc420d7f7961a4f0517b00c059d159b8face706c
[PASS] Tactical P1 verification completed: mode=Full.
```

## 2. E8 objective

E8 begins macro/parent-context use only after independently robust micro evidence exists.

```text
trusted NEUTRAL micro TacticalProfile
 + external point-in-time OBSERVED BattlefieldContext per BattleCase
        ↓
read-only context attribution
        ↓
explicit context slices and incremental evidence
        ↓
separately declared deployment policy
        ↓
DeploymentDecision evidence
```

E8 does not rewrite historical micro results, modify Instrument DSL, call provider calculation logic from DSL execution, install an entry gate, or call BrokerEmulator.

## 3. Executable

```text
core/tactical_context_attribution.py
```

Schemas:

```text
tactical_context_attribution/v1
tactical_context_deployment/v1
```

Primary types:

```text
ContextSliceRule
TacticalContextAttributor
ContextDeploymentPolicy
```

## 4. Historical profile remains read-only

Attribution accepts only:

```text
schema == tactical_discovery/v1
context_policy.require_neutral_context == true
```

and joins its per-case results to a separate exact mapping:

```text
case_id -> OBSERVED BattlefieldContext
```

No missing or extra case is silently ignored. The original profile `run_hash`, `case_set_hash`, candidate identity and per-case results remain unchanged.

## 5. Causal context contract

Every attribution context must satisfy:

```text
mode == OBSERVED
context.validate_for(case.knowledge_cutoff) == PASS
```

Future context fails closed. E8 consumes existing immutable `ContextLayerSnapshot` / `BattlefieldContext` evidence and does not implement parent-feature provider algorithms or DSL `ctx.*` binding.

## 6. Explicit context slices

`ContextSliceRule` declares:

```text
slice_id
layer
context_id
feature_key
operator = EQ | GT | GTE | LT | LTE
value
metadata
```

Required layer/context/feature absence fails closed. Values are never guessed or silently defaulted. Slices are independent declared analyses and may overlap.

## 7. Attribution evidence

For the full neutral baseline and each slice E8 exposes explicit axes:

```text
cases
active_cases
no_trade_cases
profitable_case_rate
average_return_pct
median_return_pct
worst_case_return_pct
worst_mdd_pct
cost_per_case
average_mfe_giveback_pct
matched_case_ids
incremental_vs_all
retained_case_rate
retained_active_case_rate
```

Policies:

```text
INDEPENDENT_DECLARED_CONTEXT_SLICES_NO_HIDDEN_SCORE
HISTORICAL_MICRO_PROFILE_READ_ONLY
ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY
```

There is no weighted macro score and no automatic `best regime` field.

## 8. Deployment policy evidence

`ContextDeploymentPolicy` is separate from attribution and declares explicit policy/version/tactic/rule/attribution identity.

Evidence status:

```text
RESEARCH_ONLY
VALIDATED
```

`VALIDATED` requires a separate non-empty `validation_evidence_hash`; training attribution cannot self-promote into deployment validation.

Decision evaluation requires `BattlefieldContext.mode == DEPLOYMENT` and emits the existing `DeploymentDecision` plus deterministic policy/decision hashes.

E8 remains non-operational:

```text
policy_evidence_validated = true | false
operational_authority = false
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

## 9. Regression coverage

```text
test_stage1_tactical_context_attribution.py
```

Coverage includes neutral-profile immutability, exact causal context coverage, future-context fail-close, deterministic ordering, axis deltas with no hidden score, DEPLOYMENT-only policy evaluation, research-only non-authority, separate validation-evidence requirement and absence of execution wiring.

## 10. Mutation boundary

E8 changed none of:

```text
Parser
Semantic
Runtime
TA/indicator authority
Backtest accounting
BrokerEmulator
BattleCase provider semantics
E3 parameter search
E4 characterization
E5 skill rendering
E6 validation adjudication
E7 evolution lineage/promotion authority
```

## 11. Trusted Full checkpoint

The operator synchronized `main`, confirmed exact checkout:

```text
3256f1de6b9bb7e8b79342ea037edcd51125bcda
```

and ran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E8 is trusted Full-green at `3256f1de6b9bb7e8b79342ea037edcd51125bcda`.**

## 12. Nonclaims

E8 does not establish a profitable/generalizing real JMA macro slice, production parent-feature providers, DSL `ctx.*` binding, functioning multi-symbol deployment selection, operational entry-gate/Broker authority, autonomous allocation, adaptive learner, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## 13. Post-E8 boundary

The next concrete blocker is reproducible context production. The authorized next tranche is:

```text
PCTX1 Parent Feature Provider / Feature Manifest
```

PCTX1 remains outside Instrument DSL execution and must receive its own trusted Full validation before any Core-facing `ctx.*` binding or operational deployment wiring begins.
