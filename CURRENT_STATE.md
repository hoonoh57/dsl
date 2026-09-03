# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_TRUSTED_FULL_PASS / LFREAL2_TRUSTED_FULL_PASS / LFREAL3_TRUSTED_FULL_PASS / REMOTE_EXECUTABLE_TAIL_UNVALIDATED / REMEDIATION_REQUIRED**  
Updated: 2026-09-04 KST

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

Before executable changes, establish the owning layer, existing shared-engine path, state SSOT, object create/delete authority, and adjacent-layer prohibitions. Then use one-boundary micro-tranches with focused verification, Full verification, and checkpointing. Do not weaken guards/assertions to obtain PASS.

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
LFREAL3           ab4d798c6648ee382e779af81e759cd11bf1cb13
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
LFREAL3:      Ran 7 tests in 0.001s / OK
LFREAL3 Full: [PASS] Tactical P1 verification completed: mode=Full.
```

## Remote tail awaiting local validation

The last trusted executable point remains LFREAL3 `ab4d798c6648ee382e779af81e759cd11bf1cb13`.

The following later executable/test changes exist on `main` but have no recovered user-local PASS and therefore remain `REMOTE_UNVALIDATED`:

```text
314a815300c64b492ce455f315d9e5b2cb861d6f  REALDATA1 source/provenance checkpoint
59c5fc4fb839593deff201028ed1ada5965abe42  pinned exact-byte acquisition verifier
95a1f3cedf9c8f4506bb2d59f02b14f8bbb90e60  first Live Studio verification catalog
3a49177a15888922c48c68efd91beac1abcba4a6  focused Live Studio catalog tests
```

Later documentation-only reconciliation commits do not promote those executable changes to trusted state.

REALDATA1 source material currently recorded:

```text
instrument: SK hynix
symbol: 000660.KS
source repository: hyekong/sk-hynix-news-dataset
source file: sk_hynix_price.csv
pinned source Git blob SHA-1: 84fb250326def7148cce6466026aaecf057e2013
frequency: daily
observations: 2024-04-15 .. 2026-04-13
record_count: 483
provider path stated by source: yfinance -> Yahoo Finance
```

This establishes source-origin evidence only. Exact caller-byte SHA-256/LFREAL2 manifest and independent market-data authenticity remain unverified.

## Trusted research boundary

LF2 remains observation-only orchestration. LFVAL1 validates frozen intent evidence. LFOUT1 validates exact frozen outcomes. LFREAL1 validates non-fixture provenance/timing admission. LFREAL2 freezes caller-provided external historical bytes into a deterministic SHA-256 manifest. LFREAL3 binds caller-parsed OHLCV rows to that manifest and produces deterministic cutoff-bounded causal snapshots.

LFREAL3 trusted guarantees:

```text
row_count == manifest.record_count
row.symbol in manifest.symbols
unique (symbol,time)
exact manifest first/last observation boundary
finite/basic-valid OHLCV
visible rows = rows where row.time <= knowledge_cutoff
future_rows_excluded = true
```

No nearest-time lookup, fill-forward, interpolation, provider access, file I/O, strategy replay, LF semantics, order authority, or deployment authority is added.

Authority/claim boundary remains:

```text
mode = RESEARCH_ROWS_ONLY / CAUSAL_RESEARCH_SNAPSHOT_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
market_data_authenticity_verified = false
real_data_claim = false
```

The external source includes derived/future-facing columns such as `return`, `next_close`, and `direction`; they must not be admitted as causal observation features. A later parser/adapter may admit only the raw causal OHLCV fields needed by LFREAL3.

## Defect history preserved

Initial LFOUT1 executable `f95d15f2f66533a616db5a86df9cbe9e1f7c418b` failed two focused tests. Classification: **product defect — signed MAE direction bug**. Product logic only was corrected; tests and thresholds were unchanged.

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` had a source-level boundary contract defect; the test was kept and only product text was corrected. A later sibling Chart failure was classified as a stale Chart test contract and fixed only in the Chart test at `258fd07ca76214819cec3822b02564e21a1c8680`.

## Next boundary

**Do not add another executable tranche until the current remote tail is locally validated.**

Required validation order on the current pulled `main`:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\acquire_realdata1_source.ps1
python -m unittest -v test_live_validation_catalog.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

The acquisition verifier must confirm the pinned Git blob identity and report SHA-256 over the exact downloaded bytes. Focused catalog tests must pass. Tactical P1 Full must pass. Only then may the exact current SHA be promoted to trusted local state.

After that gate, the next research micro-tranche is:

```text
verified exact REALDATA1 bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> immutable content_sha256 + dataset_manifest_hash
 -> causal OHLCV-only parser/adapter boundary
 -> LFREAL3 admission focused validation
```

Do not modify LFREAL2 product logic merely to accommodate this source. Do not add provider/file/network authority or real-data-specific semantics to Parser/Runtime/Backtest/Broker.

Automatic allocation, adaptive learning, new DSL grammar, live selection, broader ranking, and deployment permission remain deferred.

## Nonclaims

External source material and provenance have been located, but exact LFREAL2 content freezing and independent market-data authentication are not complete. No real-data LF study, profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
