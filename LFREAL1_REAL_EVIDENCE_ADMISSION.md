# LFREAL1 Real-Evidence Admission Contract — Implementation Checkpoint

Status: **TRUSTED_FULL_PASS / 2026-08-29 KST**

## Purpose

LFREAL1 defines the admission boundary for future non-fixture leader/follower research evidence.

It does **not** fetch data, verify an external source exists, claim that real market evidence has already been collected, replay tactics, submit/cancel orders, select stocks, allocate capital, publish deployment gates, or acquire operational authority.

The repository currently contains no authoritative real-market LF study dataset. LFREAL1 therefore prevents synthetic fixture evidence from being mislabeled as a real study and establishes the contract that later externally frozen data must satisfy.

## Admission flow

```text
trusted LF2 frozen evidence
+ declared non-fixture evidence provenance
+ separately frozen post-observation outcomes
 -> exact evidence_hash coverage
 -> exact observation_cutoff == evidence.as_of
 -> strict outcome_start > evidence.as_of
 -> trusted LFOUT1 declared outcome-axis validation
 -> RESEARCH_EVIDENCE_ONLY admissibility result
```

No nearest-time matching, fill-forward, interpolation, silent default, provider lookup, or execution-engine call is permitted.

## Provenance requirements

For every LF2 evidence row, LFREAL1 requires a matching `FrozenEvidenceProvenance` with:

- non-empty `source_id`;
- non-empty `source_hash`;
- declared `source_kind` that is not `SYNTHETIC`, `FIXTURE`, `GENERATED`, `MOCK`, or `TEST`;
- `fixture_only == false`;
- `observation_cutoff` exactly equal to the LF2 `evidence.as_of`.

Each outcome row must also declare:

- `source_id`;
- `source_hash`;
- non-fixture/non-synthetic `source_kind`;
- `horizon_id`;
- `outcome_start` strictly later than `evidence.as_of`;
- `outcome_end >= outcome_start`.

Evidence, provenance, and outcome identities must have exact one-to-one coverage by `evidence_hash`.

## Authority boundary

```text
mode = RESEARCH_EVIDENCE_ONLY
operational_authority = false
execution_authority = false
deployment_authority = false
source_content_verified = false
real_data_claim = false
```

`source_content_verified=false` is deliberate. LFREAL1 validates declarations and temporal/provenance structure only; it cannot prove that a supplied external source hash actually corresponds to a genuine market-data file until such a source is provided to the research pipeline.

A PASS therefore means only **admissible under the declared research-evidence contract**.

## LFOUT1 preservation

LFREAL1 delegates the already-trusted outcome axes to LFOUT1 rather than duplicating or weakening them:

```text
ARM forward-return edge vs non-ARM
ARM MFE edge vs non-ARM
ARM MAE regression vs non-ARM
CANCEL avoided-loss magnitude
holdout ARM return-edge regression vs TRAIN
```

A LFOUT1 FAIL makes LFREAL1 evidence `REJECTED`.

## Trusted executable checkpoint

```text
5aa1da3268f1f3e031aa6d607a4d3a5921f03e58
```

Executable files:

```text
core/multi_symbol_follower_real_evidence.py
test_stage1_multi_symbol_follower_real_evidence.py
```

No Parser, Semantic, Runtime, Backtest, Broker, provider, Chart, LF1, LF2, LFVAL1, or LFOUT1 trusted source semantics were modified.

## Local trust evidence

```text
Ran 7 tests in 0.002s
OK
[PASS] Tactical P1 verification completed: mode=Full.
```

Seven focused tests cover:

1. admissible contract remains research-only with no authority/real-data claim;
2. fixture provenance is rejected;
3. synthetic outcome source is rejected;
4. observation cutoff must exactly equal LF2 `as_of`;
5. outcome window must start strictly after observation;
6. exact provenance coverage is mandatory;
7. trusted LFOUT1 regression rejection remains effective.

The focused tests themselves are contract fixtures; they are **not** real-market evidence.

## Next boundary after trust

A trusted LFREAL1 contract still does not justify deployment.

The next useful step requires an actual externally sourced, frozen, hash-identified historical dataset and a reproducible producer that creates LF1/LF2 evidence without temporal leakage. Only then can a real evidence bundle be admitted and evaluated through LFVAL1/LFOUT1/LFREAL1.

Do not fabricate a "real" dataset inside unit tests merely to move the project forward.

## Nonclaims

No real-data study, profitable leader/follower edge, production selection, allocation, validated deployment gating, adaptive learning authority, live trading readiness, or repository-wide compliance PASS is claimed.

`REMEDIATION_REQUIRED` remains authoritative.
