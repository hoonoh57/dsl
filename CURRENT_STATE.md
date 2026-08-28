# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / REMEDIATION_REQUIRED**  
Updated: 2026-08-28 KST

## Recovery

`SESSION_HANDOFF.md` is the primary human-readable handoff. Exact user-local focused + Full PASS evidence outranks stale validation text; newer remote executable/test commits without local PASS remain untrusted.

## Governing architecture

Core DSL stays deterministic and single-instrument. Cross-symbol/leader/follower intelligence remains optional Add-on evidence/orchestration.

```text
single-instrument causal snapshots
 -> bounded external LF1 evidence
 -> local deterministic setup + hard guards
 -> LF2 observation-only ARM/CANCEL/HOLD intent evidence
 -> LFVAL1 partitioned evidence validation
 -> later bounded outcome evidence only if separately justified
```

Hard equipment/guards remain authoritative before optional adaptive intelligence. No peer discovery, ranking, allocation, provider calls, learning authority or leader/follower semantics belongs in Parser/Runtime/Backtest/Broker.

## Trusted exact checkpoints relevant to current boundary

```text
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
CTXINT3           7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1               5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
GCANCEL1          583c5362ca5ea57e62353a963cd5a2cfb0addfad
GCANCEL2          3cd5731a1702f7bfb11878dfd6e34339baa5f163
VSLICE1           72445456e86b695dc7288ab3a48856fa560463dd
LF2               5a6e6e53c089ed108d19fa729cba84874e856388
LFVAL1             283af6e8ed046324698b9ff49e95f5044131f453
```

Relevant external Chart contract checkpoint used by the trusted Full run:

```text
cascading-feature-solution/product-completion-mvp
258fd07ca76214819cec3822b02564e21a1c8680
```

## Recent operator evidence

```text
LF1:      Ran 7 tests in 0.058s / OK / Full PASS
GCANCEL1: Ran 5 tests in 0.000s / OK / Full PASS
GCANCEL2: Ran 5 tests in 0.004s / OK / Full PASS
VSLICE1:  Ran 2 tests in 0.039s / OK / Full PASS
LF2:      Ran 6 tests in 0.001s / OK
LF2 Full: [PASS] Tactical P1 verification completed: mode=Full.
LFVAL1:   Ran 7 tests in 0.002s / OK
LFVAL1 Full: [PASS] Tactical P1 verification completed: mode=Full.
```

## Generic mechanical vertical slice — closed

VSLICE1 trusted proof:

```text
exact registered ctx.* permission
 + follower-local deterministic setup
 -> pending LIMIT with stable id
 -> later exact ctx.* invalidation
 -> order.cancel(id=...)
 -> BrokerEmulator
```

No missing Core primitive was demonstrated. Do not expand Core merely to support leader/follower convenience.

## LF2 trusted Add-on tranche

LF2 consumes frozen LF1 evidence + local setup/hard-guard state + explicit relation validity and emits only:

```text
ARM_PENDING
HOLD
HOLD_PENDING
CANCEL_PENDING
```

It remains:

```text
mode = OBSERVATION_ONLY
operational_authority = false
execution_authority = false
```

Trusted deterministic behavior:

- only the LF1-qualified selected follower with passing local setup, hard guard and valid relation may produce `ARM_PENDING`;
- hard guard failure blocks new ARM;
- hard guard failure on an already-active pending state produces `CANCEL_PENDING` evidence;
- explicit relation invalidation produces `CANCEL_PENDING` with the existing client identity;
- unselected/unqualified followers cannot ARM;
- identity and authority mismatches fail closed;
- LF2 itself has no execution/provider/network/persistence authority.

## LFVAL1 trusted evidence-validation tranche

LFVAL1 validates frozen LF2 observation-only evidence across explicit TRAIN / VALIDATION / OOS / HARSH partitions.

Explicit axes:

```text
selection qualified rate
ARM rate
hard-guard pass rate
relation-valid rate
invalid active pending cancellation safety
```

There is no hidden weighted score. Unsafe ARM fails closed. Invalid active pending evidence must already be `CANCEL_PENDING` or validation fails closed. All partitions must share one LF2 policy identity and evidence identities must be globally disjoint.

LFVAL1 remains:

```text
mode = EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
```

A LFVAL1 PASS proves only that the declared observation-evidence contract remains stable across the supplied partitions. It does not prove profitability or authorize trading.

## Defect history preserved

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` failed one focused source-level boundary contract because its docstring named forbidden execution classes. Classification: **product defect (source-level contract defect)**. The test was kept intact; only the docstring was neutralized at `5a6e6e53c089ed108d19fa729cba84874e856388`.

The first post-fix Full run was blocked by a sibling Chart stale contract. Local repo inspection showed the branch itself intentionally contained `PrimaryPaneLayoutSurface` while `STABLE-PANE-003` still expected the old direct `Responsive(stablePanes)` composition. Classification: **test defect (stale Chart contract)**. Only the Chart test was updated at `258fd07ca76214819cec3822b02564e21a1c8680`; after pull, Tactical P1 Full passed.

## Next boundary

LFVAL1 being trusted does **not** grant deployment authority.

The next tranche, if justified, is a separate bounded outcome/backtest evidence layer attached to the already-trusted LF1/LF2/LFVAL1 observation evidence. It must answer whether the relation/orchestration evidence has measurable value without altering Core DSL or granting live selection/execution authority.

Do not add automatic allocation, adaptive learning, new DSL grammar, live selection, or broader ranking merely because LFVAL1 is trusted.

## Remote CI environment

GitHub Actions for earlier LF2 work previously failed before executable job steps were created (`steps=null`). Classification remains `environment issue`; it is independent from the user-local defects that were separately classified and fixed.

## Nonclaims

No profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
