# LFREAL3 Causal Row Producer — Implementation Checkpoint

Status: **TRUSTED FULL PASS / RESEARCH_ONLY / 2026-08-29 KST**

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

The tranche does not create LF1/LF2 evidence. It only guarantees that downstream research code can consume a deterministic prefix whose rows satisfy `row.time <= knowledge_cutoff`.

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

## Trusted executable checkpoint

```text
ab4d798c6648ee382e779af81e759cd11bf1cb13
```

Executable files:

```text
core/multi_symbol_follower_causal_rows.py
test_stage1_multi_symbol_follower_causal_rows.py
```

No Parser, Semantic, Runtime, Backtest, Broker, provider, Chart, LF1, LF2, LFVAL1, LFOUT1, LFREAL1 or LFREAL2 trusted semantics were modified.

## Local trust evidence

User-local validation on 2026-08-29 KST:

```text
Ran 7 tests in 0.001s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Focused tests cover:

1. deterministic research-only row bundle;
2. manifest record count equality;
3. manifest-external symbol rejection;
4. duplicate `(symbol,time)` rejection;
5. exact manifest time-boundary agreement;
6. strict causal prefix snapshot;
7. invalid OHLC and out-of-range cutoff fail closed.

The focused rows are fixtures only and are not real-market evidence.

## Next boundary after trust

Stop architecture expansion here unless real source material appears.

The useful next step requires actual externally sourced historical bytes. Once such bytes are available:

```text
external historical bytes
 -> LFREAL2 freeze/content hash
 -> independent source-origin verification
 -> LFREAL3 deterministic rows/snapshots
 -> narrow exact-as-of LF1/LF2 evidence producer
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

Do not fabricate a "real" dataset or add broader parser/provider infrastructure merely to continue development.

## Nonclaims

No external real-market dataset has been supplied or authenticated by this tranche. No real-data LF study, profitable leader/follower edge, selection/allocation authority, deployment gating, adaptive learning authority, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative.
