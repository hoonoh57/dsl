# LFREAL2 External Frozen Dataset Producer — Implementation Checkpoint

Status: **REMOTE_UNVALIDATED / AWAITING_LOCAL_FOCUSED_AND_FULL_PASS / 2026-08-29 KST**

## Purpose

LFREAL2 defines a research-only producer boundary for externally obtained historical dataset bytes.

It accepts caller-provided raw bytes and creates a deterministic immutable manifest with SHA-256 content identity. It does not read files, call providers, use network access, replay tactics, submit/cancel orders, select stocks, allocate capital, publish deployment gates, or acquire operational authority.

## Freeze flow

```text
caller-provided external historical bytes
+ explicit source declaration
+ symbol/timeframe/time-range/record-count metadata
+ optional expected SHA-256
 -> deterministic content SHA-256
 -> immutable dataset manifest
 -> later provenance input for LFREAL1
```

LFREAL2 deliberately does not parse or semantically validate OHLCV contents yet. This keeps the tranche narrow: content freezing first, causal producer/parser later if justified.

## Fail-closed declaration contract

Required declaration fields:

- non-empty `source_id`;
- non-fixture `source_kind`;
- non-empty `media_format`;
- non-empty `timeframe`;
- at least one unique non-empty symbol;
- `first_observation <= last_observation`;
- positive integer `record_count`.

Blocked source kinds:

```text
SYNTHETIC
FIXTURE
GENERATED
MOCK
TEST
```

The byte payload must be non-empty. If `expected_sha256` is supplied, it must exactly match the calculated SHA-256 or freezing fails closed.

## Authority and claim boundary

```text
mode = RESEARCH_DATASET_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
provider_authority = false
file_io_authority = false
content_hash_verified = true
market_data_authenticity_verified = false
real_data_claim = false
```

`content_hash_verified=true` means only that the emitted SHA-256 corresponds to the exact caller-provided bytes.

`market_data_authenticity_verified=false` and `real_data_claim=false` are deliberate. LFREAL2 cannot prove that those bytes came from a genuine exchange/vendor source merely by hashing them.

## Executable remote checkpoint

```text
10861c232d03937c5ae77e2be32cd1873a5ff977
```

Executable files:

```text
core/multi_symbol_follower_external_dataset.py
test_stage1_multi_symbol_follower_external_dataset.py
```

No Parser, Semantic, Runtime, Backtest, Broker, provider, Chart, LF1, LF2, LFVAL1, LFOUT1 or LFREAL1 trusted semantics were modified.

## Focused regression

Seven tests cover:

1. deterministic manifest identity and research-only authority;
2. fixture/synthetic/generated/mock/test source rejection;
3. empty/non-bytes payload rejection;
4. observation range ordering;
5. symbol uniqueness and positive record count;
6. exact expected SHA-256 verification;
7. byte changes alter content and manifest identity.

The focused test bytes are contract fixtures only; they are not real-market evidence.

## Local trust gate

```powershell
python -m unittest test_stage1_multi_symbol_follower_external_dataset.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Only after both pass locally may the LFREAL2 producer contract become trusted.

## Next boundary after trust

A trusted LFREAL2 contract still does not create a real study. The next useful step requires an actual externally obtained historical dataset file. Once such bytes exist, the project can freeze them with LFREAL2, verify source provenance outside this contract, and only then design a causal row parser/producer that creates LF1/LF2 evidence and strictly post-observation outcomes without leakage.

Do not fabricate data merely to advance the architecture.

## Nonclaims

No external dataset has been collected by this tranche. No real-data LF study, profitable leader/follower edge, production selection, allocation, deployment authority, adaptive learning authority, live trading readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative.
