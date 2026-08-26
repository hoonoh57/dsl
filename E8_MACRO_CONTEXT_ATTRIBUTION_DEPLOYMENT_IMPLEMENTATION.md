# E8 Macro Context Attribution / Deployment — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

E7 Evolution Memory / Evidence UI was operator-validated at exact DSL checkout:

```text
dc420d7f7961a4f0517b00c059d159b8face706c
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E7 is trusted Full-green at that SHA.

## 2. E8 objective

E8 begins macro/parent-context use only after independently robust micro evidence exists.

The governing research sequence is:

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

E8 does **not** rewrite historical micro results, modify the Instrument DSL, call provider calculation logic from DSL execution, install an entry gate, or call BrokerEmulator.

This preserves the architecture rule:

```text
macro intelligence = additive reconnaissance / command evidence
micro tactic = independently validated tactical authority
```

## 3. New executable

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

Attribution accepts only an existing:

```text
schema == tactical_discovery/v1
context_policy.require_neutral_context == true
```

profile.

The profile is never re-run or modified merely to attach macro context. E8 joins case-level results to a separate mapping:

```text
case_id -> OBSERVED BattlefieldContext
```

The context mapping must cover the profile's BattleCases exactly: no missing case and no extra case is silently ignored.

This means macro attribution does not contaminate the original:

```text
profile run_hash
case_set_hash
candidate_hash
historical per-case evidence
```

## 5. Causal context contract

Every attribution context must:

```text
mode == OBSERVED
context.validate_for(case.knowledge_cutoff) == PASS
```

Therefore:

```text
context.as_of <= case knowledge_cutoff
layer.as_of <= case knowledge_cutoff
```

Future context fails closed.

E8 consumes existing immutable `ContextLayerSnapshot` / `BattlefieldContext` evidence. It does not implement market/sector/group Provider algorithms or DSL `ctx.*` binding.

## 6. Explicit context slices

`ContextSliceRule` declares one inspectable condition:

```text
slice_id
layer
context_id
feature_key
operator
value
metadata
```

Current operators:

```text
EQ
GT
GTE
LT
LTE
```

Examples:

```text
MARKET / KOSPI_REGIME / state EQ RISK_ON
MARKET / KOSPI_REGIME / strength GT 0.5
SECTOR / SEMICONDUCTOR / relative_strength GT 1.2
GROUP / LEADER_FOLLOWER / follower_alignment GTE 0.7
```

A required layer/context/feature missing from a case fails closed. Values are never guessed or silently replaced by zero/false.

Slices are independent declared analyses. They may overlap; E8 does not invent a mutually exclusive hidden regime classifier.

## 7. Attribution evidence

For the complete neutral baseline and each declared slice, E8 computes explicit axes only:

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
```

Each slice also exposes:

```text
matched_case_ids
incremental_vs_all
retained_case_rate
retained_active_case_rate
```

`incremental_vs_all` is a direct axis-by-axis slice-minus-baseline delta. There is no weighted macro score and no `best regime` field.

Policies:

```text
INDEPENDENT_DECLARED_CONTEXT_SLICES_NO_HIDDEN_SCORE
HISTORICAL_MICRO_PROFILE_READ_ONLY
ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY
```

The deterministic `attribution_hash` includes the original micro identity, the exact case-to-context hashes, declared rules and resulting slice evidence.

Caller order of the context mapping or rule list must not change attribution identity.

## 8. Deployment policy evidence

`ContextDeploymentPolicy` is deliberately separate from attribution.

It declares:

```text
policy_id
policy_version
tactic_id
ContextSliceRule
attribution_hash
evidence_status
validation_evidence_hash
priority_if_allowed
```

Evidence status is explicit:

```text
RESEARCH_ONLY
VALIDATED
```

`VALIDATED` requires a separate non-empty `validation_evidence_hash`. E8 does not manufacture that validation status from training attribution.

Deployment evaluation accepts only:

```text
BattlefieldContext.mode == DEPLOYMENT
```

and emits the existing `DeploymentDecision` contract plus deterministic policy/decision hashes.

A slice match may produce an allow decision; a miss produces a block decision for the declared tactic.

However every result also states:

```text
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

So this tranche produces command evidence, not a live order path.

## 9. Why OBSERVED and DEPLOYMENT are separate

The progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED context attribution
 -> separate Validation / OOS evidence for a context policy
 -> explicit DEPLOYMENT policy
```

This prevents the common error:

```text
training context happened to correlate with profit
 -> immediately block all other environments
 -> tactic appears robust only because difficult battles disappeared
```

Macro intelligence may improve deployment, but it cannot retroactively become life support for an otherwise weak micro tactic.

## 10. Cascading parent-feature compatibility

E8 is compatible with the authoritative parent-feature architecture:

```text
Market/Index Provider
 -> MARKET ContextLayerSnapshot
 -> Sector Provider + MARKET snapshot
 -> SECTOR ContextLayerSnapshot
 -> Group/Leader-Follower Provider + parent snapshots
 -> GROUP ContextLayerSnapshot
 -> E8 attribution/deployment evidence
```

The Provider implementation may later come from deterministic market logic, a sector engine or an optional Multi-Symbol Add-on. Instrument DSL still receives no arbitrary peer-symbol query authority.

## 11. Regression coverage

```text
test_stage1_tactical_context_attribution.py
```

Coverage includes:

- OBSERVED context attribution against a neutral frozen micro profile;
- historical profile remains unchanged;
- exact case coverage;
- future context fail-close;
- neutral-baseline requirement;
- deterministic identity independent of mapping/rule input order;
- explicit axis deltas with no hidden score/best field;
- DEPLOYMENT-only command-policy evaluation;
- RESEARCH_ONLY decisions have no operational authority;
- VALIDATED status requires separate validation evidence;
- no DSL entry-gate/Broker integration claim.

The Tactical P1 verifier discovers the regression through `test_stage1_*.py`.

## 12. Mutation boundary

E8 adds no changes to:

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

It is a read-only analysis/command sidecar over immutable evidence.

## 13. Nonclaims

This tranche does **not** establish:

- that any real JMA generation has a profitable macro slice;
- that a context rule generalizes OOS;
- a production Market/Sector/Group Parent Feature Provider;
- DSL `ctx.*` binding;
- a functioning multi-symbol selection/deployment Add-on;
- live entry-gate integration;
- Broker order authority from macro context;
- autonomous portfolio allocation;
- production profitability/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## 14. Next boundary

Do not treat E8 as trusted or wire any context decision into production entry authorization until the exact E8 repository SHA receives Tactical P1 Full validation.
