# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_TRUSTED_FULL_PASS / LFREAL2_TRUSTED_FULL_PASS / LFREAL3_REMOTE_UNVALIDATED / REMEDIATION_REQUIRED**  
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
 -> LFREAL2 caller-bytes immutable external-dataset manifest
 -> LFREAL3 manifest-bound deterministic causal row snapshots
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
LFREAL1           5aa1da3268f1f3e031aa6d607a4d3a5921f03e58
LFREAL2           10861c232d03937c5ae77e2be32cd1873a5ff977
```

LFREAL3 remote executable checkpoint awaiting local validation:

```text
ab4d798c6648ee382e779af81e759cd11bf1cb13
```

Relevant external Chart contract checkpoint used by trusted Full runs:

```text
cascading-feature-solution/product-completion-mvp
258fd07ca76214819cec3822b02564e21a1c8680
```

## Recent operator evidence

```text
LF1:          Ran 7 tests in 0.058s / OK / Full PASS
GCANCEL1:     Ran 5 tests in 0.000s / OK / Full PASS
GCANCEL2:     Ran 5 tests in 0.004s / OK / Full PASS
VSLICE1:      Ran 2 tests in 0.039s / OK / Full PASS
LF2:          Ran 6 tests in 0.001s / OK
LF2 Full:     [PASS] Tactical P1 verification completed: mode=Full.
LFVAL1:       Ran 7 tests in 0.002s / OK
LFVAL1 Full:  [PASS] Tactical P1 verification completed: mode=Full.
LFOUT1:       Ran 7 tests in 0.003s / OK
LFOUT1 Full:  [PASS] Tactical P1 verification completed: mode=Full.
LFREAL1:      Ran 7 tests in 0.002s / OK
LFREAL1 Full: [PASS] Tactical P1 verification completed: mode=Full.
LFREAL2:      Ran 7 tests in 0.001s / OK
LFREAL2 Full: [PASS] Tactical P1 verification completed: mode=Full.
```

## Trusted research boundary

LF2 remains observation-only orchestration. LFVAL1 validates frozen intent evidence. LFOUT1 validates exact frozen outcomes. LFREAL1 validates non-fixture provenance/timing admission. LFREAL2 freezes caller-provided external historical bytes into a deterministic SHA-256 manifest.

LFREAL2 deliberately remains research-only and proves byte identity only, not external market-data authenticity.

## LFREAL3 remote-unvalidated causal row tranche

LFREAL3 binds caller-parsed OHLCV rows to an LFREAL2 v1 manifest and creates deterministic causal snapshots.

Required admission:

```text
row_count == manifest.record_count
row.symbol in manifest.symbols
unique (symbol,time)
rows stay within manifest observation range
min(row.time) == manifest.first_observation
max(row.time) == manifest.last_observation
finite/basic-valid OHLCV
```

Causal snapshot rule:

```text
visible rows = rows where row.time <= knowledge_cutoff
future_rows_excluded = true
```

No nearest-time lookup, fill-forward, interpolation, provider access, file I/O, strategy replay, LF semantics, order authority, or deployment authority is added.

LFREAL3 deliberately keeps:

```text
mode = RESEARCH_ROWS_ONLY / CAUSAL_RESEARCH_SNAPSHOT_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
market_data_authenticity_verified = false
real_data_claim = false
```

LFREAL3 is **not trusted** until user-local focused tests and Tactical P1 Full both pass.

## Defect history preserved

Initial LFOUT1 executable `f95d15f2f66533a616db5a86df9cbe9e1f7c418b` failed two focused tests. Classification: **product defect — signed MAE direction bug**. Product logic only was corrected; tests and thresholds were unchanged.

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` had a source-level boundary contract defect; the test was kept and only product text was corrected. A later sibling Chart failure was classified as a stale Chart test contract and fixed only in the Chart test at `258fd07ca76214819cec3822b02564e21a1c8680`.

## Next boundary

First close the LFREAL3 local trust gate.

Even a trusted LFREAL3 still does not mean an external real dataset has been acquired or authenticated. The next useful real study step requires actual externally obtained historical bytes, frozen by LFREAL2, parsed into LFREAL3 rows, and then consumed by a narrow exact-as-of LF1/LF2 producer plus strictly post-observation outcome producer.

Until real source material exists, automatic allocation, adaptive learning, new DSL grammar, live selection, broader ranking, and deployment permission remain closed.

## Nonclaims

No external real-market dataset has yet been collected or authenticated by this repository. No real-data LF study, profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
