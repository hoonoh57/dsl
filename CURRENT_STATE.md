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
- `[~]` materially implemented but still awaiting executable validation and/or final consolidated verification.
- `[!]` known structural blocker; do not report as complete.

## Implemented Stage 1 vertical capabilities

### Engine / trust boundary

- fail-closed parser and semantic analysis.
- canonical function capability registry used by prompt capability output and semantic arity/type checking.
- Capability Manifest and runtime dispatch exact-set contract.
- Playbook explicitly withholds current non-capabilities such as partial fills, pyramiding, `on_tick` / `on_fill`, loops/user functions, tuple outputs, multi-symbol requests, lookahead and direct drawing ownership.
- published scalar parameter values are fail-closed at runtime; invalid periods, fractional integer periods, unsupported MA methods, invalid JMA phase and invalid MTF intervals do not silently normalize/fallback.
- broker TIF validation and explicit lifecycle history.
- MARKET/LIMIT/STOP/STOP_LIMIT support path.
- unsupported DSL order `quantity` removed from the published/parser capability rather than preserved as a false feature.
- order argument applicability is fail-closed: invalid MARKET/LIMIT/STOP/STOP_LIMIT argument combinations are rejected.
- order limit/stop expressions receive static numeric type validation.
- `bar_close` / `next_open` execution policy, including next-open strategy exits.
- OHLC stop/take-profit/trailing policy and same-bar re-entry suppression.
- deferred LIMIT/STOP entry submission now obeys the Stage 1 single-position contract: entry signals do not accumulate new pending orders while a position is occupied, and a same-bar exit blocks deferred re-entry while a later eligible signal remains allowed.
- DAY expiry at detected session boundaries.
- deterministic synthetic fixture independent of wall-clock time.
- optional DSL/data timeframe mismatch rejection.
- MFE/MAE and closed-trade evidence.
- strategy MARKET entry/exit, risk exits and pending order fills use `BrokerEmulator` as the authoritative order lifecycle path rather than a separate audit replay.
- execution rows carry authoritative broker `order_id`, signal time, fill time, quantity and fill price.
- pending LIMIT/STOP trade evidence preserves the original order signal time separately from later fill time.
- execution golden fixtures cover broker lifecycle, long accounting/equity reconciliation, next-open signal/fill timing, risk exits, pending-order quantities/timestamps, occupied-position pending suppression and next-open deferred same-bar re-entry suppression.
- full-engine confirmed-bar batch/streaming-prefix contract source covers ordinary indicator calculation, confirmed MTF, persistent `on_bar` state and Broker execution/closed-trade history.

### Research factory

- canonical OHLCV Data Contract and SHA-256 data provenance.
- immutable market snapshot storage by data hash.
- append-only Experiment lineage and separate mutable current-head pointer.
- Grid/Random Parameter Seeker.
- deterministic candidate hash/seed.
- resumable Seeker session with cursor, cancel/resume, best-so-far and cross-session evaluation cache.
- Parameter Sensitivity evidence over completed Seeker candidates, including per-value score distribution and best-vs-runner-up gaps.
- rule-based Result Analyzer.
- structured Evidence Bundle v3 including signal funnel, MFE/MAE, worst trades, MFE giveback, cost components and authoritative broker lifecycle evidence.
- human-mediated LLM feedback package.
- raw Prompt/Response audit memory.
- accepted/rejected/invalid Improvement Episode memory.
- post-Seeker finalized Improvement Episode linking `Before -> LLM structural candidate -> After-Seeker best` when the structural iteration is followed by parameter optimization.
- repeated hypothesis similarity detection.
- deterministic structural DSL diff summary.
- persistent target-return loop with separate observed-best candidate and explicit promoted current-head semantics.
- target loop guards include target/iteration/backtest/no-improvement/plateau plus OOS degradation, no-new-hypothesis and parameter-instability termination states.
- immutable chronological train/holdout split with fixed OOS evaluation registry.
- A/B/C methodology descriptive statistics with OOS availability/result reporting, structural iteration success/failure, regression/overfit and duplicate-hypothesis metrics.
- quick/full Stage 1 stress harness covering deterministic engine and current product-boundary pressure cases.

### Product UX

`/stage1` currently wires:

```text
Strategy DSL
 -> Baseline
 -> immutable train Experiment (+ optional fixed holdout)
 -> input discovery
 -> resumable Parameter Seeker
 -> progress / cancel / resume / Top candidates
 -> parameter sensitivity
 -> Result Analyzer / Evidence
 -> LLM feedback prompt
 -> raw response paste
 -> validation / rerun / structural diff
 -> Improvement Episode
 -> re-Seeker / finalized post-Seeker Episode
 -> Target Loop
 -> History / Experiment A/B Compare / Methodology
 -> explicit OOS evaluation
 -> shared Chart SSOT audit viewer
```

### Integrated Stage 1 stack launcher

`scripts/start_stage1_stack.ps1` is the Windows/PowerShell 5.1 orchestration boundary for the complete Stage 1 UI stack.

It does not copy or implement Chart rendering. The ownership path remains two repositories:

```text
hoonoh57/dsl
  -> uvicorn stage1_main:app
  -> /stage1
  -> semantic Chart Document

sibling hoonoh57/cascading-feature-solution
  -> node scripts/serve.mjs
  -> shared Chart Document viewer / Chart SSOT
```

Launcher contracts:

- default sibling Chart repo discovery with explicit `-ChartRepo` override.
- Node.js >= 24 preflight because the donor Chart repo declares that engine requirement.
- Python import/dependency preflight.
- dependency installation only when `-InstallDependencies` is explicitly supplied.
- exact Stage 1 and Cascade health endpoint verification.
- fail-closed rejection when either requested port is occupied by an unexpected service.
- direct `node scripts/serve.mjs` and `python -m uvicorn stage1_main:app` process ownership; no chart-library duplication.
- partial-start failure cleanup.
- temporary PID/log state outside the repository.
- guarded stop: persisted PIDs are terminated only when their Windows command line still matches the expected Stage 1/Cascade process marker.
- browser opens `/stage1?chartSsot=<shared-chart-origin>` only after both health checks succeed.
- `Start`, `Status`, `Stop`, `Preflight`, and `Smoke` actions.
- Smoke runs the live HTTP vertical workflow and uses a literal `[PASS]` prefix check rather than PowerShell wildcard matching.

`test_stage1_stack_launcher.py` statically fixes the orchestration/Chart ownership boundary, live-smoke wiring, literal success-prefix rule and PowerShell 5.1-safe source constraints.

### Stage 1 verification orchestrator

`scripts/verify_stage1.ps1` is the intended trusted Windows/PowerShell 5.1 single entry point for automated Stage 1 system validation.

Default `Full` sequence:

```text
launcher Preflight
 -> Python compileall
 -> core regression
 -> all test_stage1_*.py contracts
 -> scoped shared-Chart SSOT contracts
 -> quick stress
 -> full stress
 -> live integrated operational smoke
 -> one final [PASS] line
```

`Quick` skips only full stress. Dependency installation remains explicit via `-InstallDependencies`.

The scoped Chart step deliberately does **not** run or claim donor-repository-wide compliance. It directly executes only Stage 1 dependency contracts:

- `chart_document_renderer.test.mjs`
- `chart_drawing_primitives_contract.test.mjs`
- `chart_drawing_ssot_boundary.test.mjs`
- `responsive_chart_surface.test.mjs`
- `stable_pane_identity_surface.test.mjs`

This keeps Stage 1 Chart dependency validation separate from the donor repository's global compliance status.

## Current remediation / validation gaps

### 1. Shared Chart SSOT integration — source-wired, executable/WYSIWYG validation pending

The Stage 1 page does not load or call Lightweight Charts directly.

Current ownership path is:

```text
Stage 1 experiment/backtest evidence
 -> `core/stage1_chart_document.py` semantic Chart Document projection
 -> Stage 1 iframe/postMessage protocol
 -> shared feature-blind Chart Document viewer
 -> `hoonoh57/cascading-feature-solution` Chart SSOT renderer/surface
```

`core/stage1_chart_document.py` contains Quant/experiment semantics only. It requests bars, generic series, markers, references and regions; it does not import or call a chart library.

The donor `ChartDocumentRenderer` supports generic line/histogram series, extra panes, markers, horizontal references, trend lines, vertical/horizontal regions and highlight regions. `ChartCore` owns canonical price/volume bars and marker routing.

S1.11 remains `[~]`, not complete, until the scoped executable Chart contracts, live integrated smoke and consolidated WYSIWYG verification succeed. The shared donor repository itself remains a separate global compliance subject; Stage 1 dependency success must not be reported as donor-wide PASS.

### 2. Engine trust boundary — source remediation advanced, executable validation open

The known Stage 1 source contracts now include authoritative Broker lifecycle, accounting golden fixtures, confirmed-bar batch/streaming-prefix parity, capability/runtime exact-set checks, explicit future-capability withholding and scalar-parameter fail-closed validation.

The newly audited deferred-entry path also enforces the single-position and same-bar re-entry policy in source and golden fixtures.

Still required before S1.1/S1.2 closure:

- execute registry/static-type/runtime-dispatch and parameter-value fail-closed contracts on a trusted runner.
- execute accounting/order golden fixtures, including the deferred-entry cases, and confirm all reconciliation assertions.
- execute full-engine confirmed-bar batch/streaming-prefix parity.
- classify and repair any actual failures without weakening assertions or adding compatibility exceptions.

Future DSL 2.0 items explicitly withheld by the current Playbook are not silently promoted into Stage 1 completion criteria.

### 3. Methodology validation boundary

Immutable chronological OOS partitioning is implemented and fixed per root. This is necessary evidence infrastructure, not a profitability/generalization claim.

Stage 1 still requires executable OOS/methodology and stress validation before any product or profitability conclusion. Representative-strategy regression coverage must remain part of the final automated validation set.

## Remote validation state

GitHub Actions workflows cover compile, core regression, Stage 1 contracts, stack/verifier contracts and quick stress source paths.

Latest observed source-validation attempts through the scoped Chart verifier checkpoint:

- `stage1-ci` run 94: job created but no executable steps were returned; checkout/test execution did not start.
- `stage1-system-ci` run 88: same pre-execution failure pattern.
- immediately preceding pending-order runs 92/86 also returned `steps=[]`.

Classification: **environment issue** until GitHub runner/service/account evidence shows otherwise. It is not counted as a product-test failure and it is not counted as a PASS. Assertions/tests have not been weakened to compensate.

## Do not do

- Do not request user UI verification for each workstream.
- Do not move to Stage 2+ while Stage 1 has known remediation/validation work.
- Do not claim profitability, global PASS or Stage 1 completion from source presence.
- Do not restore direct chart-library ownership in Stage 1 via compatibility/legacy exceptions.
- Do not duplicate generic chart drawing in DSL/UI code; missing generic primitives belong to the shared Chart axis.
- Do not conflate scoped Stage 1 Chart dependency tests with donor repository-wide compliance.
- Do not weaken validators/tests to manufacture green results.
- Do not treat OOS infrastructure presence as OOS success.
- Do not auto-promote a merely observed best candidate into the applied current-head without the explicit promotion contract.

## Next action

1. continue static source audit for any remaining Stage 1 trust-boundary or representative-regression gaps while hosted execution remains unavailable.
2. when a trusted Windows PowerShell 5.1 executor is available, run `scripts/verify_stage1.ps1 -Mode Full` as the single automated validation entry point.
3. classify any failure as test defect / product defect / authority drift / environment issue / unknown, repair product defects without assertion weakening, and rerun the full sequence.
4. only after automated compile/contracts/scoped-Chart/quick/full-stress/live-smoke are green (or an environmental dependency is explicitly isolated) request one consolidated Stage 1 WYSIWYG verification.
5. perform any final UI remediation tranche, rerun the affected automated boundary, checkpoint state, and only then consider Stage 2.
