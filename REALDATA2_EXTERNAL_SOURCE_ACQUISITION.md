# REALDATA2 External Source Acquisition

Status: **CANDIDATE_SOURCE_PINNED / EXACT_BYTES_NOT_YET_LOCALLY_VERIFIED / RESEARCH_ONLY**

Updated: 2026-09-04 KST

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
repository file size: 511194 bytes
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

## Why this candidate is admissible for the next gate

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
exact_git_blob_locally_verified = false
content_sha256_locally_verified = false
lfreal2_manifest_created = false
lfreal3_rows_admitted = false
market_data_authenticity_verified = false
real_data_claim = false
operational_authority = false
execution_authority = false
deployment_authority = false
```

## Next micro-tranche

1. Download exact bytes from the pinned GitHub commit.
2. Recompute Git blob SHA-1 from the downloaded bytes and require exact match to `68e3b6d861b4bfcf39d9c09c6a073c271369d3a9`.
3. Report exact byte count and SHA-256 from the user-local validation environment.
4. Only after that exact-byte checkpoint may REALDATA2 be frozen through the existing LFREAL2 `ExternalDatasetFreezer`.

No Core or LF1/LF2 implementation change is authorized by this checkpoint.
