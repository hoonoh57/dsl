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
- [~] S1.11 Single-Symbol Chart Audit
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
- unsupported DSL order `quantity` removed from the published/parser capability rather than preserved as a false feature.
- `bar_close` / `next_open` execution policy, including next-open strategy exits.
- OHLC stop/take-profit policy and same-bar re-entry suppression.
- DAY expiry at detected session boundaries.
- deterministic synthetic fixture independent of wall-clock time.
- optional DSL/data timeframe mismatch rejection.
- MFE/MAE and closed-trade evidence.
- Evidence Bundle v3 includes explicit commission/tax/slippage reconstruction plus MARKET lifecycle audit replay through the deterministic BrokerEmulator.

### Research factory

- canonical OHLCV Data Contract and SHA-256 data provenance.
- immutable market snapshot storage by data hash.
- append-only Experiment lineage and separate mutable current-head pointer.
- Grid/Random Parameter Seeker.
- deterministic candidate hash/seed.
- resumable Seeker session with cursor, cancel/resume, best-so-far and cross-session evaluation cache.
- rule-based Result Analyzer.
- structured Evidence Bundle v3 including signal funnel, MFE/MAE, worst trades, MFE giveback, cost components and order-lifecycle evidence.
- human-mediated LLM feedback package.
- raw Prompt/Response audit memory.
- accepted/rejected/invalid Improvement Episode memory.
- repeated hypothesis similarity detection.
- deterministic structural DSL diff summary.
- persistent target-return loop with target/iteration/backtest/no-improvement/plateau termination states.
- immutable chronological train/holdout split with fixed OOS evaluation registry.
- A/B/C methodology descriptive statistics with OOS availability/result reporting, structural iteration success/failure and duplicate-hypothesis metrics.
- quick/full Stage 1 stress harness source.

### Product UX

`/stage1` currently wires:

```text
Strategy DSL
 -> Baseline
 -> immutable train Experiment (+ optional fixed holdout)
 -> input discovery
 -> resumable Parameter Seeker
 -> progress / cancel / resume / Top candidates
 -> Result Analyzer / Evidence
 -> LLM feedback prompt
 -> raw response paste
 -> validation / rerun / structural diff
 -> Improvement Episode
 -> Target Loop
 -> History / Methodology
 -> explicit OOS evaluation
 -> shared Chart SSOT audit viewer
```

## Current remediation / validation gaps

### 1. Shared Chart SSOT integration — source-wired, validation pending

The Stage 1 page no longer loads or calls Lightweight Charts directly.

Current ownership path is:

```text
Stage 1 experiment/backtest evidence
 -> `core/stage1_chart_document.py` semantic Chart Document projection
 -> Stage 1 iframe/postMessage protocol
 -> shared feature-blind Chart Document viewer
 -> `hoonoh57/cascading-feature-solution` Chart SSOT renderer/surface
```

`core/stage1_chart_document.py` contains Quant/experiment semantics only. It requests bars, generic series, markers, references and regions; it does not import or call a chart library.

`test_stage1_chart_boundary.py` now fails if the Stage 1 HTML/JS reintroduces direct chart-library rendering APIs, and asserts the shared Chart Document protocol/origin boundary.

S1.11 remains `[~]`, not complete, until executable contract tests and consolidated WYSIWYG verification succeed. The shared donor repository itself also remains globally `REMEDIATION_REQUIRED`; using its Chart SSOT does not convert that global state to PASS.

### 2. Engine trust boundary still open

Before S1.1/S1.2 can be closed, verify/fix at minimum:

- strategy MARKET execution must have one authoritative order lifecycle rather than relying permanently on a separate audit replay representation.
- final registry/static-type/runtime-dispatch alignment across all published functions.
- final order/accounting golden fixtures reconcile trade PnL, equity and cost definitions.
- remaining DSL 2.0 gaps that are inside Stage 1 scope must be explicitly implemented or explicitly withheld from the Capability Manifest.

### 3. Methodology validation boundary

Immutable chronological OOS partitioning is now implemented and fixed per root. This is necessary evidence infrastructure, not a profitability/generalization claim.

Stage 1 still requires executable OOS/methodology validation across representative strategies before any product or profitability conclusion.

## Remote validation state

GitHub Actions workflows cover compile, core regression, Stage 1 contracts, chart-boundary contracts and quick stress tests.

Latest observed remote runs after the Chart ownership tranche again fail before any runner step is created:

- both `stage1-ci` and `stage1-system-ci` terminate as failure within seconds.
- returned workflow jobs have `steps = []`.
- no Python checkout/setup/test step executes.
- previous attempts showed the same pre-step behavior and job-log retrieval was unavailable.

Classification: **environment issue** until GitHub runner/service/account evidence shows otherwise. It is not counted as a product-test failure and it is not counted as a PASS. Assertions/tests have not been weakened to compensate.

## Do not do

- Do not request user UI verification for each workstream.
- Do not move to Stage 2+ while Stage 1 has known remediation.
- Do not claim profitability, global PASS or Stage 1 completion from source presence.
- Do not restore direct chart-library ownership in Stage 1 via compatibility/legacy exceptions.
- Do not duplicate generic chart drawing in DSL/UI code; missing generic primitives belong to the shared Chart axis.
- Do not weaken validators/tests to manufacture green results.
- Do not treat OOS infrastructure presence as OOS success.

## Next action

1. restore an executable automated-validation path for the current micro-tranche, or run the same tests in an available trusted runner without changing product assertions.
2. once the Chart ownership boundary contract is executable-green, continue S1.1 MARKET/Broker single-lifecycle remediation.
3. complete remaining registry/runtime capability alignment and accounting golden fixtures.
4. run compile/unit/operational/quick-stress/full-stress.
5. repair product defects and rerun.
6. only then request one consolidated Stage 1 WYSIWYG verification.
