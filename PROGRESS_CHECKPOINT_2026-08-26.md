# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **E7_TRUSTED_FULL_PASS / E8_MACRO_CONTEXT_ATTRIBUTION_DEPLOYMENT_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

## Trusted Full checkpoints

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
```

Each exact checkpoint above received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

E4's first Full failure was classified `environment issue`: the local external Chart SSOT checkout was behind remote. After fast-forwarding Chart SSOT to `7a43f0f52928045904d192deb7d8d532cb4c533e`, the same E4 DSL SHA passed without changing E4 source/tests.

## Stability architecture remains authoritative

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
MICRO_FIRST_MACRO_READY_ARCHITECTURE.md
```

Core remains deterministic and narrow. Parent/cascading intelligence is computed outside Instrument DSL, frozen as point-in-time context, and may later be consumed through a read-only context seam. Arbitrary peer-symbol query/ranking remains outside Core. Macro intelligence cannot bypass hard local guards or common execution authority.

## E7 trusted checkpoint

E7 adds append-only E6 validation memory plus deterministic read-only evolution lineage and Tactical UI evidence.

Key distinctions remain explicit:

```text
Train ACCEPT
!= E6 final ACCEPT
!= promotion_eligible
!= recorded accepted generation
!= explicit family head
```

The lineage API is GET-only:

```text
GET /api/stage1/tactical/evolution/{family_id}
```

No promotion write route or browser `/promote` action exists. Head mutation remains explicit `TacticalEvolutionStore.promote(...)` authority.

The operator synchronized `main`, confirmed:

```text
dc420d7f7961a4f0517b00c059d159b8face706c
```

and ran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E7 is trusted Full-green at `dc420d7f7961a4f0517b00c059d159b8face706c`.**

Detailed checkpoint:

```text
E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTATION.md
```

## E8 executable boundary now added

New module:

```text
core/tactical_context_attribution.py
```

New regression:

```text
test_stage1_tactical_context_attribution.py
```

Detailed authority:

```text
E8_MACRO_CONTEXT_ATTRIBUTION_DEPLOYMENT_IMPLEMENTATION.md
```

### E8 evidence flow

```text
trusted NEUTRAL TacticalProfile
 + exact case_id -> OBSERVED BattlefieldContext mapping
 + declared ContextSliceRule(s)
        ↓
read-only attribution
        ↓
axis-by-axis slice evidence vs full micro baseline
        ↓
explicit ContextDeploymentPolicy
        ↓
DEPLOYMENT BattlefieldContext
        ↓
DeploymentDecision evidence only
```

### Neutral micro identity is preserved

Attribution accepts only `tactical_discovery/v1` profiles that were created under `require_neutral_context=true`.

It does not rewrite or re-run the profile merely to attach parent context. Existing `run_hash`, `case_set_hash`, candidate identity and per-case results remain historical micro evidence.

External context coverage must exactly match the profile case IDs. Every `OBSERVED BattlefieldContext` must be causal at the case `knowledge_cutoff`. Future/missing/extra/mismatched context fails closed.

### Context slices are explicit

A `ContextSliceRule` declares:

```text
slice_id
layer
context_id
feature_key
operator = EQ | GT | GTE | LT | LTE
value
```

This supports market regime/KOSPI state, sector strength, leader/follower alignment or other registered point-in-time parent features without allowing direct peer-symbol queries from Instrument DSL.

### No hidden macro score

Baseline and each slice expose explicit metrics:

```text
cases / active / no-trade
profitable_case_rate
average / median return
worst case return / worst MDD
cost per case
average MFE giveback
slice-minus-baseline delta
retained case / active rate
```

Policies:

```text
INDEPENDENT_DECLARED_CONTEXT_SLICES_NO_HIDDEN_SCORE
HISTORICAL_MICRO_PROFILE_READ_ONLY
ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY
```

No universal score, automatic best regime, profile rewrite or automatic macro gate exists.

### Deployment evidence is separate

`ContextDeploymentPolicy` requires explicit policy/version/tactic/rule/attribution identity.

Evidence status:

```text
RESEARCH_ONLY
VALIDATED
```

`VALIDATED` requires a separate `validation_evidence_hash`; training attribution cannot self-promote into deployment validation.

The decision context must be `DEPLOYMENT` mode. E8 emits the existing `DeploymentDecision` and deterministic policy/decision hashes.

E8 is still non-operational:

```text
policy_evidence_validated = true|false
operational_authority = false
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

A future separately validated integration is required before any deployment decision can restrict real entry authorization.

### Regression coverage

`test_stage1_tactical_context_attribution.py` covers:

- neutral profile immutability;
- OBSERVED causal context attribution;
- exact context-case coverage;
- future-context fail-close;
- neutral-baseline requirement;
- deterministic mapping/rule ordering;
- explicit slice delta evidence and absence of hidden score/best;
- DEPLOYMENT-only policy decisions;
- research-only non-authority;
- separate validation-evidence requirement.

The existing Tactical P1 Full verifier discovers this regression through `test_stage1_*.py`.

## Current validation status

May claim E1 through E7 trusted Full PASS at the exact SHAs above and E8 source/tests implemented awaiting Full.

Do not claim yet:

- trusted Full PASS for E8;
- profitable/generalizing macro slice for a real JMA generation;
- production parent-feature Providers;
- DSL `ctx.*` runtime binding;
- functioning multi-symbol deployment selector;
- operational context entry gate or Broker authority;
- autonomous portfolio allocation;
- trained adaptive learner;
- production/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate boundary

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

before editing. Do not wire E8 into production execution before trusted Full validation.
