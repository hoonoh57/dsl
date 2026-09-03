# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_TRUSTED_FULL_PASS / LFREAL2_TRUSTED_FULL_PASS / LFREAL3_TRUSTED_FULL_PASS / REALDATA1_LFREAL3_CAUSAL_DATASET_TRUSTED_LOCAL_FULL_PASS / MULTI_SYMBOL_REALDATA_REQUIRED_FOR_LF1 / REMEDIATION_REQUIRED**  
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
PREVIOUS LOCAL MAIN 2a20f49cd3ae69b1f340496f27b8621d034c98ed
CURRENT LOCAL MAIN  f770742b69137315b14f16ad92ea77ac5881db7c
```

`f770742b69137315b14f16ad92ea77ac5881db7c` is the current trusted executable/test checkpoint because the exact user-local clean validation checkout passed the focused REALDATA1 causal-dataset/LFREAL3 contracts, deterministically derived and admitted the actual 482-row causal dataset, and passed Tactical P1 Full. Later documentation-only commits do not change the trusted executable SHA.

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

REALDATA1 original LFREAL2 freeze at 2a20f49cd3ae69b1f340496f27b8621d034c98ed:
  Ran 12 tests in 0.024s / OK
  dataset_manifest_hash=8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
  [PASS] Tactical P1 verification completed: mode=Full.

REALDATA1 causal-dataset tranche at f770742b69137315b14f16ad92ea77ac5881db7c:
  Ran 22 tests in 0.016s / OK
  original invalid row detected: 20241014000000
  low=184624.15022681453
  close=183735.109375
  low-close=889.0408518145268
  [PASS] REALDATA1 causal dataset derived and admitted
  rows=482
  quarantined=1
  derived_bytes=40493
  derived_sha256=c97624cdc92632ec3e4fab637e37514aadb9e9f9e61b1a4f2dde3a2e6390b76c
  manifest_hash=58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6
  row_bundle_hash=1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2
  [PASS] Tactical P1 verification completed: mode=Full.
```

Two verification-harness defects were exposed during earlier local validation and fixed without weakening product assertions:

1. Windows PowerShell 5.1 native version probing read `$LASTEXITCODE` after `Select-Object`, producing a false failure even when Python returned `Python 3.13.1`; the exit code is now captured before output selection.
2. Tactical preflight invoked native Python imports under `$ErrorActionPreference='Stop'`, causing stderr to terminate the script before the intended fail-closed exit-code branch; native stderr/exit are now captured explicitly and reported without bypassing failure.

The missing `pymysql` module was classified as an environment issue after the harness correctly exposed it.

## REALDATA1 source, original identity, and causal derived identity

Original pinned source:

```text
instrument: SK hynix
symbol: 000660.KS
source repository: hyekong/sk-hynix-news-dataset
source commit: 339f0b6dc15531f374c51f715f12555153054009
source file: sk_hynix_price.csv
pinned source Git blob SHA-1: 84fb250326def7148cce6466026aaecf057e2013
frequency: daily / timeframe=1d
observations: 2024-04-15 .. 2026-04-13
record_count: 483
exact downloaded bytes: 57541
exact downloaded content SHA-256: fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba
original LFREAL2 dataset_manifest_hash: 8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
```

The original source remains immutable. LFREAL3 correctly rejected one source row because `2024-10-14` had `low > close` by about 889.04, which is not floating-point noise. No Core assertion was weakened and no price was clipped, filled, interpolated or corrected.

A separate causal-only derived dataset was therefore created at the edge. Its identity is:

```text
quarantined observation: 20241014000000
quarantined row count: 1
causal record_count: 482
derived_bytes: 40493
derived_sha256: c97624cdc92632ec3e4fab637e37514aadb9e9f9e61b1a4f2dde3a2e6390b76c
derived LFREAL2 dataset_manifest_hash: 58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6
LFREAL3 row_bundle_hash: 1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2
```

The derived dataset contains only causal `date/open/high/low/close/volume` information. Source columns `return`, `next_close`, and `direction` are not admitted. The derivation remains bound to the exact original source identity and explicitly quarantines only the known invalid observation; unexpected additional invalid rows fail closed.

```text
content_hash_verified = true
lfreal2_manifest_created = true
lfreal3_rows_admitted = true
market_data_authenticity_verified = false
real_data_claim = false
```

## Trusted research boundary

LF2 remains observation-only orchestration. LFVAL1 validates frozen intent evidence. LFOUT1 validates exact frozen outcomes. LFREAL1 validates non-fixture provenance/timing admission. LFREAL2 freezes caller-provided bytes into deterministic immutable manifests. LFREAL3 binds caller-parsed OHLCV rows to a manifest and produces deterministic cutoff-bounded causal snapshots.

LFREAL3 trusted guarantees remain unchanged:

```text
row_count == manifest.record_count
row.symbol in manifest.symbols
unique (symbol,time)
exact manifest first/last observation boundary
finite/basic-valid OHLCV
visible rows = rows where row.time <= knowledge_cutoff
future_rows_excluded = true
```

No nearest-time lookup, fill-forward, interpolation, provider access, strategy replay, LF semantics, order authority, or deployment authority is added to Core.

Authority/claim boundary remains:

```text
mode = RESEARCH_ROWS_ONLY / CAUSAL_RESEARCH_SNAPSHOT_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
market_data_authenticity_verified = false
real_data_claim = false
```

## Defect history preserved

Initial LFOUT1 executable `f95d15f2f66533a616db5a86df9cbe9e1f7c418b` failed two focused tests. Classification: **product defect — signed MAE direction bug**. Product logic only was corrected; tests and thresholds were unchanged.

Initial LF2 checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219` had a source-level boundary contract defect; the test was kept and only product text was corrected. A later sibling Chart failure was classified as a stale Chart test contract and fixed only in the Chart test at `258fd07ca76214819cec3822b02564e21a1c8680`.

The 2026-09-04 Python version/stderr failures were **test/verification-harness defects**. Missing `pymysql` was an **environment issue**. The REALDATA1 `2024-10-14` OHLC violation is classified as an **external source/data defect**; Core LFREAL3 behaved correctly by rejecting it.

## Next boundary

The REALDATA1 causal-dataset/LFREAL3 admission gate is closed at trusted executable SHA:

```text
f770742b69137315b14f16ad92ea77ac5881db7c
```

Direct LF1/LF2 evidence production is **not yet admissible** from REALDATA1 alone. Existing MSA2/LF1 requires a static exact multi-symbol universe: `GroupEvidencePolicy.leader_count=1` must satisfy `leader_count < len(universe.symbols)`, so at least two symbols are required for any follower evidence. REALDATA1 currently contains only `000660.KS`.

The next research micro-tranche is therefore:

```text
acquire/pin at least one additional compatible causal instrument
 -> exact caller bytes + LFREAL2 manifest per source/dataset
 -> LFREAL3 causal rows with aligned explicit observation points
 -> static explicit multi-symbol universe
 -> only then existing MSA2/LF1 -> LF2
```

Mandatory implementation gate:

```text
owner layer: tools/ research data edge outside Core
existing shared path: LFREAL2 freezer -> LFREAL3 rows -> MSA1/MSA2 -> existing LF1 -> existing LF2
state SSOT: exact source identities + LFREAL2 manifest hashes + LFREAL3 row bundle hashes + explicit static universe topology
create authority: research data/evidence artifacts only
delete authority: none
forbidden: fabricate follower symbols from one instrument; clone/shift one series as another symbol; nearest-time/fill-forward/interpolation; provider/network authority in Core; hidden ranking/allocation; execution/deployment authority
```

Do not create a fake second symbol from `000660.KS` and do not weaken the LF1 multi-symbol contract. A second independently identified causal instrument/source must be pinned and pass the same identity/OHLCV gates before LF1 study begins.

Automatic allocation, adaptive learning, new DSL grammar, live selection, broader ranking, and deployment permission remain deferred.

## Nonclaims

Exact source-byte identity, original LFREAL2 manifest identity, causal derived dataset identity, and LFREAL3 row admission for `000660.KS` are verified locally. Independent market-data authentication remains incomplete. A multi-symbol real-data universe is not yet established, so no actual LF1/LF2 relation/intent study is currently admissible. No profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
