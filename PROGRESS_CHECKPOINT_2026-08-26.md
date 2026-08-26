# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **E8_TRUSTED_FULL_PASS / PCTX1_PARENT_FEATURE_PROVIDER_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

## Trusted Full checkpoints

Each exact checkout below received:

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

E4's first Full failure was classified `environment issue` because the local external Chart SSOT checkout was stale. After fast-forwarding Chart SSOT to `7a43f0f52928045904d192deb7d8d532cb4c533e`, the same E4 DSL SHA passed without changing E4 product/tests.

## Stability architecture

Authoritative boundaries remain:

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
MICRO_FIRST_MACRO_READY_ARCHITECTURE.md
```

Core stays deterministic and single-instrument. Parent feature calculation, peer-symbol analysis, ranking, provider I/O and adaptive learning stay outside Instrument DSL execution.

## E8 trusted checkpoint

E8 separates:

```text
trusted NEUTRAL micro profile
 -> OBSERVED context attribution
 -> separate context-policy validation
 -> DEPLOYMENT decision evidence
 -> future operational integration
```

The operator confirmed exact E8 checkout:

```text
3256f1de6b9bb7e8b79342ea037edcd51125bcda
```

and Full PASS.

Therefore **E8 is trusted Full-green at `3256f1de6b9bb7e8b79342ea037edcd51125bcda`.**

E8 remains deliberately non-operational:

```text
operational_authority = false
execution_integration = NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER
```

## Post-E8 mainline decision

The immediate blocker is now reproducible parent-context production, not entry-gate wiring and not Core `ctx.*` grammar.

The next tranche is named separately from the E0-E8 roadmap:

```text
PCTX1 Parent Feature Provider / Feature Manifest
```

This follows the authoritative parent-context policy and avoids inventing an unsupported `E9` phase.

## PCTX1 executable boundary

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

### Contracts

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

### Feature identity

A public feature is declared through provider/version/layer/context metadata and a typed feature spec:

```text
feature_id
feature_key
value_type
semantic_version
causality_policy
required
missing_policy
```

Current v1 supports:

```text
NUMBER
STRING
BOOLEAN
CONFIRMED_ONLY
FAIL_CLOSED
OPTIONAL_ABSENT
```

### Registry

The deterministic registry exposes stable feature IDs without exposing calculation implementation. It rejects duplicate provider/version and duplicate feature identities.

This is the future discoverability seam for strategy generators and a generic read-only binder.

### Provider result

Provider-specific calculation remains external to Instrument DSL. Once computed, a result records:

```text
manifest
as_of
knowledge_cutoff
source
features
dependency_result_hashes
metadata
snapshot_hash
result_hash
```

It fails closed on future/stale evidence, required-feature absence, undeclared features, type mismatch, missing source or malformed dependencies.

### Cascading context

Parent results can form an explicit causal chain through immutable `result_hash` dependencies. Assembly requires dependencies to exist and not be later than the child provider result.

`ParentContextAssembler` accepts only precomputed results and emits OBSERVED/DEPLOYMENT `BattlefieldContext` with manifest/result provenance in context metadata.

Policy:

```text
PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY
```

Input result ordering must not change context/assembly identity.

### Mutation boundary

PCTX1 does not modify:

```text
Parser
Semantic
Runtime
Backtest
BrokerEmulator
TA/indicator authority
Chart SSOT
E3-E8 adjudication semantics
```

It does not yet implement production market/sector/group calculators, context timelines, DSL `ctx.*`, Runtime binder or operational deployment wiring.

## Current validation status

May claim E0-E8 trusted Full PASS and PCTX1 source/tests implemented awaiting Full.

Do not claim PCTX1 trusted, production parent-feature calculation, DSL parent-context binding, operational macro gate, autonomous allocation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate boundary

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If Full fails, classify the first executable failure exactly as:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before editing. Do not begin PCTX2 or Core `ctx.*` work before PCTX1 is trusted green.
