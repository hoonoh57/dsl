# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_TRUSTED_FULL_PASS / LFREAL2_TRUSTED_FULL_PASS / LFREAL3_TRUSTED_FULL_PASS / REALDATA1_LFREAL2_MANIFEST_TRUSTED_LOCAL_FULL_PASS / REMEDIATION_REQUIRED**  
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
PREVIOUS LOCAL MAIN 4ebde8647cd0caede3c9cb4e6f210bc5a1f7d630
CURRENT LOCAL MAIN  2a20f49cd3ae69b1f340496f27b8621d034c98ed
```

`2a20f49cd3ae69b1f340496f27b8621d034c98ed` is the current trusted executable/test checkpoint because the exact user-local clean validation checkout passed the focused LFREAL2 freeze contracts, produced the pinned REALDATA1 manifest, and passed Tactical P1 Full. Later documentation-only commits do not change the trusted executable SHA.

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

REALDATA1 acquisition:
  [PASS] exact source verified
  bytes=57541
  sha256=fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba

Live Studio catalog:
  Ran 4 tests in 0.169s / OK

Stage1 native probe + launcher contracts:
  Ran 8 tests in 0.095s / OK
Stage1 preflight:
  [PASS] Stage 1 preflight: Python Python 3.13.1, Node v24.19.0

Tactical launcher contracts:
  Ran 6 tests in 0.033s / OK
Previous Full at 4ebde8647cd0caede3c9cb4e6f210bc5a1f7d630:
  [PASS] Tactical P1 verification completed: mode=Full.

REALDATA1 LFREAL2 freeze focused validation at 2a20f49cd3ae69b1f340496f27b8621d034c98ed:
  Ran 12 tests in 0.024s / OK

REALDATA1 LFREAL2 actual manifest freeze:
  [PASS] REALDATA1 LFREAL2 manifest frozen
  bytes=57541
  sha256=fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba
  dataset_manifest_hash=8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982

Current Full at 2a20f49cd3ae69b1f340496f27b8621d034c98ed:
  [PASS] Tactical P1 verification completed: mode=Full.
```

Two verification-harness defects were exposed during earlier local validation and fixed without weakening product assertions:

1. Windows PowerShell 5.1 native version probing read `$LASTEXITCODE` after `Select-Object`, producing a false failure even when Python returned `Python 3.13.1`; the exit code is now captured before output selection.
2. Tactical preflight invoked native Python imports under `$ErrorActionPreference='Stop'`, causing stderr to terminate the script before the intended fail-closed exit-code branch; native stderr/exit are now captured explicitly and reported without bypassing failure.

A later Tactical preflight correctly exposed the actual environment issue `ModuleNotFoundError: No module named 'pymysql'`. `PyMySQL` was already an official `requirements.txt` dependency, so no product/Core requirement change was made. The final exact local checkout subsequently passed Tactical P1 Full.

## REALDATA1 source, identity, and LFREAL2 manifest status

REALDATA1 source material currently recorded:

```text
instrument: SK hynix
symbol: 000660.KS
source repository: hyekong/sk-hynix-news-dataset
source commit: 339f0b6dc15531f374c51f715f12555153054009
source file: sk_hynix_price.csv
pinned source Git blob SHA-1: 84fb250326def7148cce6466026aaecf057e2013
frequency: daily / LFREAL2 timeframe=1d
observations: 2024-04-15 .. 2026-04-13
LFREAL2 observation keys: 20240415000000 .. 20260413000000
record_count: 483
provider path stated by source: yfinance -> Yahoo Finance
exact downloaded bytes: 57541
exact downloaded content SHA-256: fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba
LFREAL2 dataset_manifest_hash: 8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
```

The acquisition verifier establishes exact content identity for the pinned source bytes. The existing LFREAL2 `ExternalDatasetFreezer` now also freezes those exact caller bytes into a deterministic immutable manifest. Neither step independently establishes market-data authenticity.

```text
content_hash_verified = true
lfreal2_manifest_created = true
market_data_authenticity_verified = false
real_data_claim = false
```

The manifest identity SSOT is now the exact tuple of source declaration + caller-byte content identity embodied by `dataset_manifest_hash=8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982`.

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

The external source includes derived/future-facing columns such as `return`, `next_close`, and `direction`; they must not be admitted as causal observation features. The next edge parser/adapter may admit only `date, open, high, low, close, volume`, assign the already-declared symbol `000660.KS`, and normalize daily dates to the LFREAL3-compatible midnight observation key. It must not modify LFREAL3 Core semantics.

## Defect history preserved

Initial LFOUT1 executable `f95d15f2f66533a616db5a86df9cbe9e1f7c418b` failed two focused tests. Classification: **product defect — signed MAE direction bug**. Product logic only was corrected; tests and thresholds were unchanged.

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` had a source-level boundary contract defect; the test was kept and only product text was corrected. A later sibling Chart failure was classified as a stale Chart test contract and fixed only in the Chart test at `258fd07ca76214819cec3822b02564e21a1c8680`.

The 2026-09-04 local validation failures around Python version probing and Tactical native stderr were classified as **test/verification-harness defects**, not product defects. The missing `pymysql` module was classified as an **environment issue** after the harness correctly exposed it.

## Next boundary

The REALDATA1 LFREAL2 freeze gate is closed at trusted executable SHA:

```text
2a20f49cd3ae69b1f340496f27b8621d034c98ed
```

The next research micro-tranche is now:

```text
trusted LFREAL2 manifest
+ exact REALDATA1 local CSV bytes
 -> edge causal OHLCV-only parser/adapter
 -> existing LFREAL3 CausalRowProducer.admit
 -> deterministic row_bundle_hash / exact boundary validation
```

Mandatory implementation gate:

```text
owner layer: tools/ edge adapter outside Core
existing shared path: LFREAL3 CausalRowProducer.admit
state SSOT: LFREAL2 dataset_manifest_hash + existing LFREAL3 row bundle
create authority: explicit caller source path + manifest path -> parser adapter -> LFREAL3 only
delete authority: none
forbidden: Parser/Runtime/Backtest/Broker/Core provider/file/network authority; future-facing column admission; source-specific LFREAL3 product semantics
```

The edge adapter must fail closed if the supplied manifest identity is not the trusted REALDATA1 LFREAL2 manifest, if source bytes do not match the pinned content SHA-256, if required causal columns are absent/invalid, if row count/time boundaries differ, or if LFREAL3 rejects the rows. It must ignore rather than admit `return`, `next_close`, and `direction` as observations.

Automatic allocation, adaptive learning, new DSL grammar, live selection, broader ranking, and deployment permission remain deferred.

## Nonclaims

Exact REALDATA1 source-byte identity and LFREAL2 immutable manifest identity are now verified locally. Independent market-data authentication is not complete. No LFREAL3 actual-row admission has yet been locally validated for this source, and no real-data LF study, profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
