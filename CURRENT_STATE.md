# Quant DSL Current State

Status: **IMPLEMENTED_AWAITING_SYSTEM_VALIDATION / REMEDIATION_REQUIRED**
Updated: 2026-08-25 KST

## Authority

- Product roadmap: `PRODUCT_IMPLEMENTATION_PLAN.md`
- Stage 1 execution policy: `STAGE1_EXECUTION_POLICY.md`
- DSL language contract: `QUANT_DSL_PLAYBOOK.md`
- Engine audit criteria: `DSL_ENGINE_AUDIT.md`

## Current goal

Complete `S1.0 ~ S1.13` as one continuous Stage 1 vertical slice without per-workstream user verification. After all functional wiring and architecture remediation are complete, execute automated operational/stress tests, repair failures, then request one consolidated UI verification.

## Stage 1 workstreams

- [x] S1.0 Authority / State Hygiene
- [~] S1.1 Engine Trust Boundary Remediation
- [~] S1.2 Single-Symbol DSL Capability Completion
- [x] S1.3 Data Contract / Provenance
- [~] S1.4 Backtest Evidence Engine
- [x] S1.5 Immutable Experiment Store
- [~] S1.6 Parameter Seeker
- [x] S1.7 Result Analyzer
- [x] S1.8 Human-Mediated LLM Improvement Loop
- [x] S1.9 Improvement Episode Memory
- [x] S1.10 Target-Return Improvement Loop
- [!] S1.11 Single-Symbol Chart Audit — architecture remediation required
- [~] S1.12 Semi-Automation Product UX
- [~] S1.13 Methodology Validation

Legend:

- `[x]` functionally wired in source.
- `[~]` materially implemented but still awaiting remaining contract work and/or executable validation.
- `[!]` known structural blocker; do not report as complete.

## Implemented Stage 1 vertical capabilities

### Engine / trust boundary

- fail-closed parser and semantic analysis.
- canonical function capability registry used by prompt capability output and semantic arity/type checking.
- broker TIF validation and explicit lifecycle history.
- MARKET/LIMIT/STOP/STOP_LIMIT support path.
- `bar_close` / `next_open` execution policy, including next-open strategy exits.
- OHLC stop/take-profit policy and same-bar re-entry suppression.
- DAY expiry at detected session boundaries.
- deterministic synthetic fixture independent of wall-clock time.
- optional DSL/data timeframe mismatch rejection.
- MFE/MAE and closed-trade evidence.

### Research factory

- canonical OHLCV Data Contract and SHA-256 data provenance.
- immutable market snapshot storage by data hash.
- append-only Experiment lineage and separate mutable current-head pointer.
- Grid/Random Parameter Seeker.
- deterministic candidate hash/seed.
- resumable Seeker session with cursor, cancel/resume, best-so-far and cross-session evaluation cache.
- rule-based Result Analyzer.
- structured Evidence Bundle v2 including signal funnel, MFE/MAE, worst trades and explicit commission/tax/slippage reconstruction.
- human-mediated LLM feedback package.
- raw Prompt/Response audit memory.
- accepted/rejected/invalid Improvement Episode memory.
- repeated hypothesis similarity detection.
- deterministic structural DSL diff summary.
- persistent target-return loop with target/iteration/backtest/no-improvement/plateau termination states.
- A/B/C methodology descriptive statistics, structural iteration success/failure and duplicate-hypothesis metrics.
- quick/full Stage 1 stress harness source.

### Product UX

`/stage1` currently wires:

```text
Strategy DSL
 -> Baseline
 -> immutable Experiment
 -> input discovery
 -> resumable Parameter Seeker
 -> progress / cancel / resume / Top candidates
 -> Result Analyzer
 -> LLM feedback prompt
 -> raw response paste
 -> validation / rerun / structural diff
 -> Improvement Episode
 -> Target Loop
 -> History / Methodology
```

## Known blocking remediation

### 1. Chart ownership — REMEDIATION_REQUIRED

The current Stage 1 prototype page directly loads and calls Lightweight Charts. This conflicts with `PRODUCT_IMPLEMENTATION_PLAN.md` S1.11, which requires DSL to provide Validation/Evidence Bundles while generic chart-native drawing remains in the shared Chart SSOT donor (`hoonoh57/cascading-feature-solution`).

Therefore S1.11 is **not complete**. The direct Stage 1 chart prototype must be replaced by a shared feature-blind Chart surface/adapter integration rather than preserved with a compatibility exception.

### 2. Engine trust boundary still open

Before S1.1/S1.2 can be closed, verify/fix at minimum:

- every strategy MARKET order is represented in reproducible broker lifecycle evidence, not only implicit backtest execution rows.
- explicit DSL order quantity semantics are either implemented correctly or removed from the published capability until implemented.
- function-registry static argument typing remains aligned with actual runtime dispatch for all registered functions.
- final order/accounting golden fixtures reconcile trade PnL, equity and cost definitions.

### 3. Methodology validation boundary

Current methodology output is descriptive IS evidence. Explicit OOS partitioning is not yet present, so no profitability or generalization claim is permitted.

## Remote validation state

GitHub Actions workflows were added for compile, core regression, Stage 1 contract tests and quick stress tests.

Observed remote runs currently fail before any runner step is created:

- job status becomes failure within a few seconds.
- job `steps` is empty.
- downloadable job log is unavailable.
- manually re-running the job reproduces the same pre-step failure.

Classification: **environment issue** until runner/service evidence shows otherwise. It is not counted as a product-test failure and it is not counted as a PASS.

## Do not do

- Do not request user UI verification for each workstream.
- Do not move to Stage 2+ while Stage 1 has known remediation.
- Do not claim profitability, global PASS or Stage 1 completion from source presence.
- Do not preserve the direct chart implementation via allowlist/legacy exception merely to keep UI functioning.
- Do not weaken validators/tests to manufacture green results.

## Next action

1. finish S1.1/S1.2 broker/order/capability trust-boundary remediation.
2. replace the direct Stage 1 chart prototype with the shared generic Chart SSOT integration.
3. complete UI compare/audit surfaces around that shared chart.
4. finish methodology/OOS-ready contracts.
5. run compile/unit/operational/quick-stress/full-stress when an executable runner is available.
6. repair product defects and rerun.
7. only then request one consolidated Stage 1 UI verification.
