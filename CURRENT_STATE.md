# Quant DSL Current State

Status: **VSLICE1_TRUSTED_FULL_PASS / GENERIC_MECHANICAL_VERTICAL_SLICE_CLOSED / LF2_TRUSTED_FULL_PASS / LFVAL1_TRUSTED_FULL_PASS / LFOUT1_TRUSTED_FULL_PASS / LFREAL1_TRUSTED_FULL_PASS / LFREAL2_TRUSTED_FULL_PASS / LFREAL3_TRUSTED_FULL_PASS / REALDATA1_LFREAL3_CAUSAL_DATASET_TRUSTED_LOCAL_FULL_PASS / REALDATA2_EXACT_SOURCE_TRUSTED_LOCAL_FULL_PASS / REALDATA2_LFREAL2_FREEZE_NEXT / MULTI_SYMBOL_REALDATA_REQUIRED_FOR_LF1 / REMEDIATION_REQUIRED**  
Updated: 2026-09-05 KST

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
PREVIOUS LOCAL MAIN f770742b69137315b14f16ad92ea77ac5881db7c
CURRENT LOCAL MAIN  e44f6846619f9ec6c7bb9725d517d77cc197c802
```

`e44f6846619f9ec6c7bb9725d517d77cc197c802` is the current trusted executable/test checkpoint. The exact user-local clean validation checkout passed the REALDATA2 acquisition contracts and actual exact-byte acquisition evidence inherited unchanged from the prior acquisition tranche, the focused Stage1 native-probe/launcher contracts, Stage1 preflight, and consolidated Tactical P1 Full.

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

REALDATA2 exact-source acquisition:
  focused: Ran 3 tests in 0.001s / OK
  [PASS] REALDATA2 exact source verified
  bytes=511194
  sha256=ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
  pinned Git blob SHA-1=68e3b6d861b4bfcf39d9c09c6a073c271369d3a9

Stage1 harness/environment closure at e44f6846619f9ec6c7bb9725d517d77cc197c802:
  focused launcher/native dependency contracts: Ran 10 tests in 0.038s / OK
  environment repair: numpy 2.5.2 installed into existing validation venv
  [PASS] Stage 1 preflight: Python Python 3.13.1, Node v24.19.0
  transient first Full attempt: Stage 1 full stress failed (exit=-1)
  targeted isolated/prefix reproductions: PASS, including original first 7 Full checks through resumable seeker
  final exact-SHA rerun: [PASS] Tactical P1 verification completed: mode=Full.
```

Verification-harness/environment defect history in this validation line:

1. Windows PowerShell 5.1 native version probing read `$LASTEXITCODE` after `Select-Object`, producing a false failure even when Python returned `Python 3.13.1`; the exit code was corrected to be captured before output selection.
2. Tactical preflight invoked native Python imports under `$ErrorActionPreference='Stop'`, causing stderr to terminate the script before the intended fail-closed exit-code branch; native stderr/exit are captured explicitly.
3. Stage1 preflight still used the old direct native dependency probe. At `e44f6846619f9ec6c7bb9725d517d77cc197c802`, Stage1 now uses the same explicit native capture/fail-closed pattern, with a focused contract test.
4. Missing `pymysql` earlier and missing `numpy` in the clean validation venv here were **environment issues**, not product defects. The existing venv was repaired; no new venv was created.
5. One Full run returned `Stage 1 full stress failed (exit=-1)` with no product assertion output. The suspected resumable-seeker and cumulative-pressure paths were reproduced directly, in pairs, in three-stage combinations, and through the original first seven `Harness.check` calls; all passed. The exact same `e44f684...` checkout then passed consolidated Full. No product or threshold change was made, so the transient abnormal termination is not promoted to a product defect.

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

## REALDATA2 exact source identity

```text
instrument: Samsung Electronics
symbol: 005930.KS
source repository: nileshiq/Samsung-Stock-Price
source commit: bcef6f27b803ce89000e2fc336201ddeef7df015
source file: Samsung Dataset.csv
pinned source Git blob SHA-1: 68e3b6d861b4bfcf39d9c09c6a073c271369d3a9
exact downloaded bytes: 511194
exact downloaded content SHA-256: ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
columns: Date, Open, High, Low, Close, Adj Close, Volume
observations: 2000-01-04 .. 2024-06-13
record_count: 6127
```

The exact GitHub byte identity is locally verified. Provenance remains narrower than REALDATA1 because the repository does not preserve the provider-generation script; it only identifies the historical dataset and an upstream Kaggle reference. This does not authenticate the observations as exchange-grade market data.

`Adj Close` must not silently replace raw `Close`. Future causal admission may use only `Date/Open/High/Low/Close/Volume` and must pass the existing LFREAL3 OHLC rules without tolerance weakening or price correction.

```text
exact_git_blob_locally_verified = true
content_sha256_locally_verified = true
lfreal2_manifest_created = false
lfreal3_rows_admitted = false
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

The later Stage1 dependency-probe failure was also a **test/verification-harness defect** and was corrected only in the Stage1 launcher/harness contract. Missing `numpy` was an **environment issue**. The one-off Stage1 Full `exit=-1` could not be reproduced under targeted stress diagnostics and the exact same executable later passed Full, so it remains a transient abnormal termination rather than a product-defect claim.

## Next boundary

The current trusted executable/test checkpoint is:

```text
e44f6846619f9ec6c7bb9725d517d77cc197c802
```

REALDATA1 causal LFREAL3 is closed/trusted. REALDATA2 exact-byte acquisition is also closed/trusted, but REALDATA2 has **not** yet been frozen through LFREAL2 and has **not** yet passed LFREAL3 causal-row admission.

The next micro-tranche is only:

```text
REALDATA2 exact original bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> immutable REALDATA2 original-source manifest
```

Mandatory implementation gate:

```text
owner layer: tools/ edge adapter outside Core
existing shared path: LFREAL2 ExternalDatasetFreezer
state SSOT: pinned REALDATA2 exact source identity -> immutable LFREAL2 manifest
create authority: caller bytes -> existing freezer only
delete authority: none
forbidden:
  Core/Parser/Runtime/Backtest/Broker provider/file/network authority
  source-specific semantics in Core
  Adj Close replacing raw Close
  causal-row derivation or LFREAL3 admission in the same tranche
  nearest-time/fill-forward/interpolation
```

Expected original-source identity to bind in that LFREAL2 tranche:

```text
symbol: 005930.KS
timeframe: 1d
first_observation: 20000104000000
last_observation: 20240613000000
record_count: 6127
exact_bytes: 511194
content_sha256: ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
```

Only after the exact original REALDATA2 LFREAL2 freeze is focused + Full trusted may a later micro-tranche parse raw `Date/Open/High/Low/Close/Volume` and attempt existing LFREAL3 admission. If any source row violates LFREAL3, classify the external data first and preserve the original source/manifest; do not weaken OHLC guards or silently correct values.

Direct LF1/LF2 evidence production remains **not yet admissible**. Existing MSA2/LF1 requires `leader_count < len(universe.symbols)`; the second symbol must complete its own LFREAL2/LFREAL3 causal admission before an explicit aligned multi-symbol universe exists. Exact shared observation dates only; no nearest-time, fill-forward, interpolation, cloning, or shifting.

Automatic allocation, adaptive learning, new DSL grammar, live selection, broader ranking, and deployment permission remain deferred.

## Nonclaims

Exact source-byte identity is locally verified for REALDATA1 and REALDATA2. Original/derived LFREAL2 identity and LFREAL3 causal admission are trusted for REALDATA1 only. REALDATA2 does not yet have a trusted LFREAL2 manifest or LFREAL3 row bundle, so a multi-symbol real-data universe is still not established.

Independent market-data authentication remains incomplete. No actual LF1/LF2 relation/intent study, profitable leader/follower edge, production leader selection, validated deployment gating, live provider/broker readiness, or repository-wide compliance PASS is claimed.

`market_data_authenticity_verified = false` and `real_data_claim = false` remain authoritative for both external sources.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

Any executable failure must first be classified as `test defect`, `product defect`, `authority drift`, `environment issue`, or `unknown`.
