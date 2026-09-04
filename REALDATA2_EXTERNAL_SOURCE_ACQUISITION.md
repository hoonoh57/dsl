# REALDATA2 External Source Acquisition

Status: **EXACT_BYTES_LOCALLY_VERIFIED / SOURCE_IDENTITY_TRUSTED / LFREAL2_NOT_YET_CREATED / RESEARCH_ONLY**

Updated: 2026-09-05 KST

## Purpose

This checkpoint records a second independently identified historical instrument needed before existing MSA2/LF1 follower evidence can be exercised over real external observations. It does not add provider code, parser code, file/network authority, ranking, allocation, execution authority, or deployment authority to DSL Core.

## Source material

```text
instrument: Samsung Electronics
market symbol used for research identity: 005930.KS
source repository: nileshiq/Samsung-Stock-Price
source commit: bcef6f27b803ce89000e2fc336201ddeef7df015
source file: Samsung Dataset.csv
source file Git blob SHA-1: 68e3b6d861b4bfcf39d9c09c6a073c271369d3a9
exact downloaded bytes: 511194
exact downloaded content SHA-256: ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
media format: CSV
columns: Date, Open, High, Low, Close, Adj Close, Volume
first observation: 2000-01-04
last observation: 2024-06-13
records: 6127 data rows
```

The repository README identifies the data as Samsung Electronics historical stock-price data and links the upstream dataset as:

```text
https://www.kaggle.com/datasets/mayankanand2701/samsung-stock-price-dataset
```

Unlike REALDATA1, the GitHub repository does not preserve a provider-download script that generated the CSV. Therefore the supported provenance claim is narrower: exact GitHub file identity plus the repository's stated upstream Kaggle dataset reference. This is not exchange-level or independent market-data authentication.

## Local validation evidence

The exact acquisition tranche was validated from the clean DSL validation checkout. The acquisition contract tests passed, the downloaded bytes reproduced the pinned Git blob identity, and the exact byte count/SHA-256 were recorded.

```text
focused acquisition tests:
  Ran 3 tests in 0.001s
  OK

actual acquisition:
  [PASS] REALDATA2 exact source verified
  bytes=511194
  sha256=ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
```

The later trusted executable/test checkpoint `e44f6846619f9ec6c7bb9725d517d77cc197c802` does not modify the REALDATA2 acquisition files and passed the consolidated Tactical P1 Full verification after the Stage1 native dependency-probe harness was corrected.

## Why this source is admissible for the next gate

REALDATA1 currently provides only `000660.KS`, while existing MSA2/LF1 requires `leader_count < universe symbol count`; with `leader_count=1`, at least two independently identified symbols are required.

REALDATA2 supplies an independently identified Samsung Electronics series. Its available overlap with the trusted REALDATA1 causal series begins at `2024-04-15` and ends at `2024-06-13`. Any future multi-symbol alignment must use exact shared observation dates only. No nearest-time lookup, fill-forward, interpolation, or synthetic second symbol is authorized.

## Causal-field boundary

A later parser/adapter may admit only:

```text
Date, Open, High, Low, Close, Volume
```

`Adj Close` is not required for LFREAL3 causal OHLCV admission and must not silently replace the raw `Close` field.

## Boundary / nonclaims

```text
exact_git_blob_locally_verified = true
content_sha256_locally_verified = true
exact_bytes = 511194
content_sha256 = ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e
lfreal2_manifest_created = false
lfreal3_rows_admitted = false
market_data_authenticity_verified = false
real_data_claim = false
operational_authority = false
execution_authority = false
deployment_authority = false
```

## Next micro-tranche

The exact-byte acquisition gate is closed. The next micro-tranche is only:

```text
REALDATA2 exact original source bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> immutable original-source LFREAL2 manifest
```

Mandatory gate before implementation:

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

The intended LFREAL2 original-source metadata remains research-only and must preserve the exact source identity, including symbol `005930.KS`, timeframe `1d`, first observation `20000104000000`, last observation `20240613000000`, record count `6127`, exact bytes `511194`, and SHA-256 `ae73a5dcc5d1d076cc80d7aa2d95c25fa6e1795bd81657ed9cad7d26dbb2aa6e`.

Only after that LFREAL2 freeze is locally focused + Full trusted may a later micro-tranche parse raw causal OHLCV and attempt existing LFREAL3 admission. If any OHLC row is invalid, classify the external data first; do not weaken LFREAL3 and do not silently correct, clip, interpolate, or delete values under the original manifest.

No Core or LF1/LF2 implementation change is authorized by this checkpoint.
