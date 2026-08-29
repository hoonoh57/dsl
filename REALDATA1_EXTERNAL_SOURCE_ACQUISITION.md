# REALDATA1 External Source Acquisition

Status: **SOURCE_BYTES_LOCATED / PROVENANCE_RECORDED / NOT_YET_LFREAL2_FROZEN / RESEARCH_ONLY**

Updated: 2026-08-29 KST

## Purpose

This checkpoint records the first externally obtained non-fixture historical market-data source material after the LFREAL3 architecture freeze. It does not add provider code, parser code, file I/O authority, strategy replay, leader/follower semantics, execution authority, or deployment authority to DSL Core.

## Source material

```text
instrument: SK hynix
market symbol: 000660.KS
source repository: hyekong/sk-hynix-news-dataset
source file: sk_hynix_price.csv
source file Git blob SHA-1: 84fb250326def7148cce6466026aaecf057e2013
media format: CSV
frequency: daily
first observation: 2024-04-15
last observation: 2026-04-13
records: 483 data rows
```

The source repository's acquisition script explicitly uses `yfinance` with ticker `000660.KS` and requests the range `start="2024-04-14", end="2026-04-14"`. The resulting CSV contains daily `date, open, high, low, close, volume` plus derived columns `return, next_close, direction`.

## Provenance evidence

Acquisition implementation observed in the external source repository:

```text
source code file: get_sk_price.py
source code Git blob SHA-1: 598f9156407495c3cbb45dc2884b9d6d5ca412ee
provider path stated by source: yfinance -> Yahoo Finance
requested ticker: 000660.KS
requested date range: 2024-04-14 <= request < 2026-04-14
```

This is source-origin evidence only. It is not independent exchange-level authentication.

## Boundary / nonclaims

```text
lfreal2_content_sha256_frozen = false
lfreal2_manifest_created = false
lfreal3_rows_admitted = false
market_data_authenticity_verified = false
real_data_claim = false
operational_authority = false
execution_authority = false
deployment_authority = false
```

The external CSV includes derived future-facing fields such as `next_close`. Those columns MUST NOT be admitted as causal observation features. A later parser/adapter, if needed, must remain outside Core authority and must admit only the raw causal OHLCV observation fields required by LFREAL3.

## Next micro-tranche

1. Obtain the exact external CSV bytes without rewriting encoding or line endings.
2. Compute SHA-256 over those exact caller bytes and pass them to existing LFREAL2 `ExternalDatasetFreezer`.
3. Record the resulting immutable manifest without changing LFREAL2 product logic.
4. Only after the manifest is frozen, parse causal OHLCV rows and test LFREAL3 admission.

No architecture expansion is authorized by this checkpoint.
