# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_REMOTE_UNVALIDATED / REMEDIATION_REQUIRED**  
Updated: 2026-08-29 KST

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
 -> LFOUT1 exact frozen-outcome validation
 -> LFREAL1 non-fixture provenance/admission contract
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
LFVAL1            283af6e8ed046324698b9ff49e95f5044131f453
LFOUT1            ca4d5309a658de02f970e341bbf86ad87ab327ae
```

LFREAL1 remote executable checkpoint awaiting local validation:

```text
5aa1da3268f1f3e031aa6d607a4d3a5921f03e58
```

Relevant external Chart contract checkpoint used by trusted Full runs:

```text
cascading-feature-solution/product-completion-mvp
258fd07ca76214819cec3822b02564e21a1c8680
```

## Recent operator evidence

```text
LF1:         Ran 7 tests in 0.058s / OK / Full PASS
GCANCEL1:    Ran 5 tests in 0.000s / OK / Full PASS
GCANCEL2:    Ran 5 tests in 0.004s / OK / Full PASS
VSLICE1:     Ran 2 tests in 0.039s / OK / Full PASS
LF2:         Ran 6 tests in 0.001s / OK
LF2 Full:    [PASS] Tactical P1 verification completed: mode=Full.
LFVAL1:      Ran 7 tests in 0.002s / OK
LFVAL1 Full: [PASS] Tactical P1 verification completed: mode=Full.
LFOUT1:      Ran 7 tests in 0.003s / OK
LFOUT1 Full: [PASS] Tactical P1 verification completed: mode=Full.
```

## Generic mechanical vertical slice — closed

VSLICE1 proved that existing generic exact `ctx.*`, stable pending ids, generic `order.cancel`, and BrokerEmulator semantics are sufficient for the deterministic mechanical slice. No missing Core primitive was demonstrated.

## LF2 / LFVAL1 / LFOUT1 trusted boundary

LF2 remains observation-only orchestration with no execution authority. LFVAL1 validates frozen LF2 evidence across explicit TRAIN / VALIDATION / OOS / HARSH partitions. LFOUT1 joins separately frozen outcomes by exact `evidence_hash` and evaluates explicit outcome axes without replaying tactics or calling execution infrastructure.

LFOUT1 authority remains:

```text
mode = EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
```

LFOUT1 is trusted at `ca4d5309a658de02f970e341bbf86ad87ab327ae` after local focused 7/7 PASS and Tactical P1 Full PASS.

### LFOUT1 defect history

Initial LFOUT1 executable `f95d15f2f66533a616db5a86df9cbe9e1f7c418b` failed two focused tests. Classification: **product defect — signed MAE direction bug**. `mae_pct` is signed adverse excursion, so more negative is worse. Only product logic was corrected; tests and thresholds were unchanged.

## LFREAL1 remote-unvalidated admission tranche

The repository does not currently contain an authoritative real-market LF research dataset. LFREAL1 therefore does not pretend that unit-test fixtures are real evidence. It establishes the admission contract for later externally frozen data.

Required flow:

```text
trusted LF2 evidence
+ exact non-fixture provenance
+ exact post-observation frozen outcome
 -> observation_cutoff == evidence.as_of
 -> outcome_start > evidence.as_of
 -> trusted LFOUT1 outcome validation
 -> RESEARCH_EVIDENCE_ONLY admissibility
```

Blocked provenance declarations include `SYNTHETIC`, `FIXTURE`, `GENERATED`, `MOCK`, and `TEST`. Evidence/provenance/outcome coverage must be exact by `evidence_hash`.

LFREAL1 deliberately outputs:

```text
mode = RESEARCH_EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
source_content_verified = false
real_data_claim = false
```

A future PASS means only that the supplied bundle is structurally admissible under the declared provenance/timing/outcome contract. It does not prove that an external source hash corresponds to genuine market data unless such source material is separately supplied and verified.

LFREAL1 is **not trusted** until the user-local focused test and Tactical P1 Full both pass.

## Earlier defect history preserved

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` had a source-level boundary contract defect; the test was kept and only the product docstring was corrected. A later sibling Chart failure was classified as a stale Chart test contract and fixed only in the Chart test at `258fd07ca76214819cec3822b02564e21a1c8680`.

## Next boundary

First close the LFREAL1 local trust gate. Even then, do not create a fake "real" dataset in tests.

The next useful work requires an actual externally sourced, frozen, hash-identified historical dataset plus a reproducible causal producer for LF1/LF2 evidence and post-observation outcomes. Only then should a real study bundle pass through LFVAL1/LFOUT1/LFREAL1.

Do not add automatic allocation, adaptive learning, new DSL grammar, live selection, or broader ranking merely because the admission contract passes.

## Nonclaims

No real-data LF study, profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
