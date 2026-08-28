# LFREAL3 Causal Row Producer — Implementation Checkpoint

Status: **REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / 2026-08-29 KST**

## Purpose

LFREAL3 defines a narrow research-only admission layer between a trusted-form LFREAL2 immutable dataset manifest and caller-parsed market rows.

It does not read files, call providers, authenticate vendor origin, calculate leader/follower semantics, replay tactics, submit/cancel orders, select stocks, allocate capital, or grant deployment authority.

## Flow

```text
LFREAL2 immutable dataset manifest
+ caller-parsed OHLCV rows
 -> exact manifest row-count / symbol / time-boundary checks
 -> unique (symbol,time) identities
 -> deterministic normalized row bundle
 -> cutoff-bounded causal snapshot
```

The tranche does not yet create LF1/LF2 evidence. It only guarantees that downstream research code can consume a deterministic prefix whose rows satisfy `row.time <= knowledge_cutoff`.

## Fail-closed row contract

Each row requires:

- non-empty symbol;
- YYYYMMDDHHMMSS-compatible time;
- finite open/high/low/close/volume;
- basic OHLC consistency;
- volume >= 0.

The admitted row set must:

- contain exactly `manifest.record_count` rows;
- use only manifest-declared symbols;
- contain no duplicate `(symbol,time)` identity;
- stay within manifest observation bounds;
- have exact minimum/maximum row times equal to manifest first/last observation.

## Causal snapshot rule

```text
visible rows = rows where row.time <= knowledge_cutoff
```

The cutoff itself must lie within the manifest observation range. Future rows are excluded; there is no nearest-time lookup, fill-forward, interpolation, or silent default.

## Authority / claim boundary

```text
row bundle:
  mode = RESEARCH_ROWS_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
  provider_authority = false
  file_io_authority = false
  strategy_authority = false
  market_data_authenticity_verified = false
  real_data_claim = false

snapshot:
  mode = CAUSAL_RESEARCH_SNAPSHOT_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
  future_rows_excluded = true
  market_data_authenticity_verified = false
  real_data_claim = false
```

A PASS proves only the deterministic row-admission and causal-prefix contract. It does not authenticate the external source and does not prove a real-data study.

## Executable remote checkpoint

```text
ab4d798c6648ee382e779af81e759cd11bf1cb13
```

Executable files:

```text
core/multi_symbol_follower_causal_rows.py
test_stage1_multi_symbol_follower_causal_rows.py
```

No Parser, Semantic, Runtime, Backtest, Broker, provider, Chart, LF1, LF2, LFVAL1, LFOUT1, LFREAL1 or LFREAL2 trusted semantics were modified.

## Focused regression

Seven focused tests cover:

1. deterministic research-only row bundle;
2. manifest record count equality;
3. manifest-external symbol rejection;
4. duplicate `(symbol,time)` rejection;
5. exact manifest time-boundary agreement;
6. strict causal prefix snapshot;
7. invalid OHLC and out-of-range cutoff fail closed.

The focused rows are fixtures only and are not real-market evidence.

## Local trust gate

```powershell
python -m unittest test_stage1_multi_symbol_follower_causal_rows.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Only after both pass locally may LFREAL3 become trusted.

## Next boundary after trust

Do not immediately build a broad parser framework. The useful next step remains obtaining actual externally sourced historical bytes. Once those are frozen through LFREAL2 and parsed into LFREAL3 rows, the next narrow tranche can connect causal snapshots to already-trusted LF1/LF2 evidence production and strictly post-observation outcome production.

## Nonclaims

No external real-market dataset has been supplied or authenticated by this tranche. No real-data LF study, profitable leader/follower edge, selection/allocation authority, deployment gating, adaptive learning authority, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative.
