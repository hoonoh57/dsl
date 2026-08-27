# PCTX2C Exact Root Provider Frame Orchestration — Implementation Checkpoint

Status: **TRUSTED FULL PASS / 2026-08-27 KST**

## Trusted predecessor

PCTX2A is trusted at:

```text
6f6aef0b09354b1171ce3eccc78d4daa451fe183
Ran 7 tests ... OK
[PASS] Tactical P1 verification completed: mode=Full.
```

## Objective and contract

PCTX2C precomputes independent root providers before tactic execution:

```text
explicit target instrument exact timeline
 + explicit independent root providers
 -> provider result at every exact target bar
 -> PCTX1 assembly at every exact target bar
 -> PCTX2B ParentContextFrame
 -> optional CTXDSL1 / CTXBT1 consumption
```

Executable:

```text
core/parent_context_orchestrator.py
```

Schema/policy:

```text
parent_context_frame_build/v1
PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD
```

For every target time `t`, every root is called with exact `as_of=t`, `knowledge_cutoff=t`, `dependencies=None`. Result timestamp/manifest identity must match exactly and root results may not carry dependency hashes.

Target market requires explicit `_meta.instrument`, `_meta.timeframe`, `_meta.source` and unique strictly increasing `YYYYMMDDHHMMSS` timestamps. No nearest lookup, interpolation, fill-forward, source guessing, universe discovery, ranking, provider invocation from Backtest, deployment scoring or Broker action is permitted.

Provider order is normalized by manifest identity, so equivalent caller ordering preserves registry/frame/build identity.

OBSERVED frames remain evidence-only. DEPLOYMENT only permits later registered binding and does not create automatic entry authority.

## Regression

```text
test_stage1_parent_context_orchestrator.py
```

Coverage includes exact provider invocation per target bar, target/frame identity, PCTX2A -> PCTX2C -> CTXBT1 -> Broker end-to-end, caller-order invariance, OBSERVED execution rejection, malformed timeline, duplicate provider and dependency-smuggling fail-close behavior.

## Trusted validation

Operator validation at exact checkout:

```text
7aee063932e0d70d38c2e7f876b140d049029771
Ran 6 tests in 0.107s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore PCTX2C is trusted Full-green at that SHA.

## Boundary after trust

PCTX2C remains root-only. Dependency-cascading MARKET -> SECTOR -> GROUP orchestration requires an explicit DAG boundary. It does not establish parent-context profitability, automatic macro entry authority, peer-symbol DSL reads, ranking/allocation, Broker-side provider calculation, live readiness or repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains broader repository status.
