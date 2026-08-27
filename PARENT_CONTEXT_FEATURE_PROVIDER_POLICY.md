# Parent Context Feature Provider / Read-Only DSL Binding Policy

Status: **AUTHORITATIVE CONTEXT-INHERITANCE POLICY / PCTX1-PCTX2C + CTXDSL1-CTXBT1 TRUSTED / PCTX2D ACTIVE / 2026-08-27 KST**

## Governing rule

> **Parent features are computed outside Instrument DSL, frozen as point-in-time context evidence, and consumed inside DSL only through a narrow registered read-only binding contract.**

Instrument DSL remains deterministic and single-instrument. It may know stable `feature_id` values; it must not know provider algorithms, perform provider I/O, discover peers/universes or rank symbols.

## Trusted chain

```text
PCTX1 typed/versioned Parent Feature Provider contract
 -> PCTX2B exact ParentContextFrame
 -> CTXDSL1 generic read-only ctx.*
 -> CTXBT1 exact Backtest binding
 -> existing execution policy
 -> BrokerEmulator
```

Trusted exact checkpoints:

```text
PCTX1  866bf0a5a25bf6759d1b264d62efcf9f1f277446
PCTX2B ce18ffc4b9f7758d57117b9b08eaa2d8c1e7aba4
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
PCTX2A  6f6aef0b09354b1171ce3eccc78d4daa451fe183
PCTX2C  7aee063932e0d70d38c2e7f876b140d049029771
```

Every listed exact checkout received:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

PCTX2A additionally received seven focused provider tests; PCTX2C received six focused orchestration tests.

## PCTX1 contract

`ParentFeatureSpec`, `ParentFeatureManifest`, `ParentFeatureRegistry`, `ParentFeatureProviderResult`, `ParentContextAssembly` and `ParentContextAssembler` define immutable typed evidence.

Required behavior remains fail-closed for future data, stale data beyond manifest limit, missing required feature, undeclared feature, incompatible type, missing source and missing/future dependency evidence. Optional values remain explicitly absent rather than silently defaulted.

Every semantic change requires provider/manifest version identity change.

## PCTX2B / CTXDSL1 / CTXBT1 exact binding

Frame points require:

```text
target_time == assembly.knowledge_cutoff == assembly.context.as_of
```

Resolution/binding policies remain:

```text
EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD
REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL
REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL
EXACT_MARKET_BAR_TIMES_DEPLOYMENT_FRAME_NO_PROVIDER_CALL
```

Supplying context does not itself authorize an entry. Context affects tactic logic only through an explicit registered `ctx.*` expression; existing `entry_gate` and Broker execution policy remain separate restrictions.

## PCTX2A MARKET provider — trusted

`KrxBenchmarkMarketParentFeatureProvider` consumes an explicit `SessionMarketProvider`, benchmark symbol, namespace and source authority. It requires exact causal source prefixes ending at `as_of == knowledge_cutoff` and publishes descriptive return/trend/ATR/volume/regime features only.

No ALLOW/BLOCK/PERMIT/GATE/order/allocation feature is produced.

## PCTX2C root orchestration — trusted

`RootParentContextFrameBuilder` precomputes independent root provider results for every exact target bar before tactic execution.

Policy:

```text
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

It remains root-only. Provider caller order is normalized by manifest identity. No provider call occurs from Parser/Semantic/Runtime/Backtest/Broker.

Trusted exact PCTX2C checkpoint:

```text
7aee063932e0d70d38c2e7f876b140d049029771
Ran 6 tests in 0.107s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## PCTX2D explicit dependency DAG — active

New orchestration:

```text
core/parent_context_dependency_orchestrator.py
```

Policy:

```text
EXPLICIT_DEPENDENCY_DAG_PRECOMPUTE_EVERY_EXACT_TARGET_BAR
```

Every provider node explicitly declares parent `provider_id` dependencies. Unknown/self/duplicate dependencies and cycles fail closed. Execution uses deterministic topological order.

At exact target `t`, each child provider receives only its declared already-built parent results for `t`. Its returned `dependency_result_hashes` must exactly equal the supplied parent result hashes. No implicit dependency discovery is allowed.

## First SECTOR provider — active PCTX2D component

```text
core/sector_parent_feature_provider.py
KrxSectorBenchmarkParentFeatureProvider
```

Construction requires explicit sector benchmark source/symbol/namespace/source authority plus explicit MARKET dependency provider ID and public MARKET return/regime feature IDs.

It can publish descriptive SECTOR values such as:

```text
sector.<namespace>_return_short_pct
sector.<namespace>_return_long_pct
sector.<namespace>_sma_slope_pct
sector.<namespace>_price_to_sma_pct
sector.<namespace>_relative_strength_long_pct
sector.<namespace>_regime_state
sector.<namespace>_market_alignment
```

This provider does not discover sector constituents, scan peer symbols, rank leaders/followers or emit execution authority.

## Cascading architecture

The intended causal chain is now explicit:

```text
raw benchmark data
 -> MARKET result
 -> declared result-hash dependency
 -> SECTOR result
 -> later declared dependency
 -> future GROUP result
 -> PCTX1 assembly
 -> exact PCTX2B frame
```

A future GROUP/Leader-Follower provider must use the same explicit DAG/result-hash discipline. It may not create arbitrary peer-symbol reads inside Instrument DSL.

## Evidence before operational gate

The required progression remains:

```text
NEUTRAL micro baseline
 -> OBSERVED parent context
 -> E8 attribution
 -> Validation/OOS evidence
 -> explicit DEPLOYMENT policy evidence
 -> separately validated operational integration
```

Descriptive MARKET/SECTOR context is not entry authority. Macro context must amplify a valid micro tactic rather than become life support for one.

## Multi-symbol boundary

Sector membership discovery, leader/follower analysis, cross-sectional ranking, universe construction and allocation remain in a future optional Multi-Symbol Add-on/orchestration layer. Such a layer may publish bounded registered provider outputs, but Instrument DSL still consumes only immutable registered context values.

## Current nonclaims

Do not claim yet:

- PCTX2D trusted Full PASS;
- GROUP/leader-follower provider intelligence;
- sector constituent discovery/ranking;
- MARKET/SECTOR OOS profitability benefit;
- automatic macro deployment authorization;
- arbitrary peer-symbol DSL reads;
- cross-symbol allocation deployment;
- Broker-side provider calculation;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.

## Immediate gate

Validate `test_stage1_parent_context_dependency_orchestrator.py` and Tactical P1 Full at one exact PCTX2D checkout before GROUP/leader-follower or operational deployment wiring. Any failure must first be classified exactly as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
