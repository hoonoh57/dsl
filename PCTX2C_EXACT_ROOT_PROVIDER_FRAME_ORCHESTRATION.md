# PCTX2C Exact Root Provider Frame Orchestration — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING LOCAL EXECUTABLE VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

PCTX2A received operator validation at exact checkout:

```text
6f6aef0b09354b1171ce3eccc78d4daa451fe183
python -m unittest -v test_stage1_market_parent_feature_provider.py
Ran 7 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore the first deterministic MARKET parent provider is trusted Full-green at that SHA.

The earlier combined CTXDSL1 + CTXBT1 executable context path remains trusted at:

```text
99bb2e5f5a248dc61cddb23677b5798b258848f2
```

## 2. Objective

PCTX2C fills the missing orchestration seam between concrete provider calculation and exact historical tactic consumption.

```text
explicit target instrument market timeline
 + explicit independent root providers
 -> precompute provider result at every exact target bar
 -> PCTX1 ParentContextAssembly at every exact target bar
 -> PCTX2B ParentContextFrame
 -> CTXDSL1 / CTXBT1 consumption
```

Providers are called before Backtest execution. Backtest still receives only an immutable frame and registry.

## 3. Executable

New module:

```text
core/parent_context_orchestrator.py
```

Schema:

```text
parent_context_frame_build/v1
```

Build policy:

```text
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

Primary contracts:

```text
ParentContextFrameBuild
RootParentContextFrameBuilder
```

## 4. Target timeline authority

The builder consumes an explicit target market mapping and requires:

```text
_meta.instrument
_meta.timeframe
_meta.source
time[]
```

Every `time[]` value must be an exact `YYYYMMDDHHMMSS` timestamp. Timestamps must be unique and strictly increasing.

The builder records a deterministic `target_timeline_hash` over:

```text
target instrument
target timeframe
target source
exact ordered target timestamps
```

It does not infer a target symbol or timeframe from a parent provider.

## 5. Exact precomputation

For every target timestamp `t`, PCTX2C calls every configured root provider as:

```text
provider.build(
    as_of=t,
    knowledge_cutoff=t,
    dependencies=None,
)
```

The returned result must satisfy:

```text
result.as_of == t
result.knowledge_cutoff == t
result.manifest == provider.manifest
result.dependency_result_hashes == ()
```

Any mismatch fails closed.

There is no:

- nearest-time substitution;
- fill-forward;
- interpolation;
- missing-value default;
- provider invocation from DSL Runtime or Backtest;
- universe discovery;
- peer-symbol ranking;
- deployment score or Broker action.

## 6. Root-only boundary

PCTX2C v1 intentionally orchestrates independent root providers only.

This supports one or more explicitly configured MARKET roots, for example separately authorized KOSPI and KOSDAQ benchmark providers.

A provider that returns dependency hashes is rejected. Sector/Group/Leader-Follower cascading providers require a later explicit dependency-DAG orchestration tranche rather than implicit dependency discovery.

## 7. Order-independent identity

Providers are normalized by declared manifest identity before registry and assembly creation.

Reversing caller provider order must not alter:

```text
registry_hash
frame_hash
build_hash
```

The build evidence records sorted provider IDs and the exact PCTX2B frame hash.

## 8. OBSERVED vs DEPLOYMENT

PCTX2C can precompute both:

```text
OBSERVED
DEPLOYMENT
```

OBSERVED remains attribution/evidence only. Existing CTXDSL1/CTXBT1 contracts continue to reject an OBSERVED frame for executable `ctx.*` Backtest use.

DEPLOYMENT means the frame is eligible for executable binding; it does not create an automatic macro gate or Broker permission.

## 9. End-to-end boundary

The validated intended path after this tranche is:

```text
SessionMarketProvider
 -> PCTX2A MARKET provider
 -> PCTX2C exact precomputation
 -> PCTX1 assemblies
 -> PCTX2B frame
 -> CTXDSL1 ctx.*
 -> CTXBT1 Backtest
 -> existing execution policy
 -> BrokerEmulator
```

Context influences a tactic only when DSL explicitly references a registered `ctx.*` feature. Existing external `entry_gate` remains separate and restrictive.

## 10. Regression coverage

New regression:

```text
test_stage1_parent_context_orchestrator.py
```

Coverage includes:

- one provider call for every exact target bar;
- exact frame points equal target market timestamps;
- PCTX2A -> PCTX2C -> CTXBT1 -> Broker end-to-end execution;
- Broker authority unchanged;
- provider caller-order invariance;
- deterministic registry/frame/build identity;
- OBSERVED frame remains non-executable;
- duplicate/malformed target timestamps fail closed;
- missing target instrument fails closed;
- duplicate provider identity fails closed;
- root-only dependency smuggling fails closed.

The Tactical P1 Full verifier discovers the regression through `test_stage1_*.py`.

## 11. Mutation boundary

PCTX2C adds only orchestration and regression code. It does not modify:

```text
Parser
Semantic
DSL Runtime
BacktestEngine
BrokerEmulator
PCTX1 contract semantics
PCTX2B exact-time semantics
PCTX2A feature formulas
entry_gate
Chart SSOT
```

## 12. Nonclaims

PCTX2C does not establish:

- Sector/Group/Leader-Follower provider dependencies;
- validated macro profitability;
- automatic deployment authorization;
- portfolio ranking/allocation;
- arbitrary peer-symbol reads from Instrument DSL;
- Broker-side parent calculation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 13. Validation gate

Validate this exact orchestration tranche before beginning dependency-DAG parent layers or operational deployment-policy wiring:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
python -m unittest -v test_stage1_parent_context_orchestrator.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If an executable failure occurs, classify the first failure exactly as one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before changing code.
