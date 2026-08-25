# Quant DSL Current State

Status: **SYSTEM_VALIDATED_PENDING_CONSOLIDATED_UI / REMEDIATION_REQUIRED**
Updated: 2026-08-26 KST

## Authority

- Product roadmap: `PRODUCT_IMPLEMENTATION_PLAN.md`
- Stage 1 execution policy: `STAGE1_EXECUTION_POLICY.md`
- DSL language contract: `QUANT_DSL_PLAYBOOK.md`
- Engine audit criteria: `DSL_ENGINE_AUDIT.md`

## Current goal

Stage 1 `S1.0 ~ S1.13` source implementation and trusted automated system validation have completed as one continuous vertical slice. The remaining Stage 1 gate is one consolidated WYSIWYG/UI verification of the integrated product. Do not reopen per-workstream manual validation.

## Stage 1 workstreams

- [x] S1.0 Authority / State Hygiene
- [x] S1.1 Engine Trust Boundary Remediation
- [x] S1.2 Single-Symbol DSL Capability Completion
- [x] S1.3 Data Contract / Provenance
- [x] S1.4 Backtest Evidence Engine
- [x] S1.5 Immutable Experiment Store
- [x] S1.6 Parameter Seeker
- [x] S1.7 Result Analyzer
- [x] S1.8 Human-Mediated LLM Improvement Loop
- [x] S1.9 Improvement Episode Memory
- [x] S1.10 Target-Return Improvement Loop
- [~] S1.11 Single-Symbol Chart Audit
- [~] S1.12 Semi-Automation Product UX
- [x] S1.13 Methodology Validation Infrastructure

Legend:

- `[x]` functionally wired and covered by the trusted automated Stage 1 validation boundary.
- `[~]` automated contracts are green but final consolidated WYSIWYG/UI verification is still required.
- `[!]` known structural blocker; do not report as complete.

## Trusted automated validation checkpoint

On 2026-08-26 KST, the trusted local Windows PowerShell 5.1 verifier completed successfully with:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

The successful `Full` sequence is:

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

This is the first trusted end-to-end automated Stage 1 system-validation PASS. It closes the prior `IMPLEMENTED_AWAITING_SYSTEM_VALIDATION` state.

It does **not** mean:

- donor `cascading-feature-solution` repository-wide global compliance is PASS;
- live trading readiness is established;
- profitability/generalization has been proven;
- consolidated human WYSIWYG verification is complete.

## Validation remediation completed during the trusted Full run

The Full-run failure/repair sequence was handled without weakening product assertions or adding compatibility bypasses.

### Core/runtime contract drift

- DSL/data timeframe mismatch remains fail-closed; stale fixtures were updated to declare the intended timeframe rather than weakening the engine.
- Broker golden tests were reconciled to the current authoritative `BrokerOrder`/`BrokerEmulator` contract.
- authoritative broker history remains under `diagnostics.broker_history`; no legacy top-level compatibility alias was introduced.
- MTF tests use the current numeric market contract rather than restoring obsolete runtime arguments.
- JMA golden expectations were reconciled to the current `chart_base_trading` reference behavior rather than changing the runtime to obsolete fixture values.
- state variables updated by `on_bar` are now executable inputs to dependent post-state assignments through explicit assignment dependency partitioning.
- structured strategy analysis remains structured; legacy `summary` compatibility was not restored.

### Broker/accounting fixtures

- single-round-trip golden fixtures were corrected so they do not accidentally emit an additional legitimate later entry.
- same-bar re-entry suppression remains enforced while later eligible entry signals remain allowed.
- accounting reconciliation, fees/tax/slippage, lifecycle evidence and signal-time/fill-time separation remain strict.

### Stage 1 snapshot identity

- `data_hash` is the identity of canonical `time/OHLCV` rows.
- instrument/source/partition metadata is contextual provenance and may differ while referencing identical row content.
- snapshot persistence compares canonical rows for an existing hash rather than rejecting the same rows solely because `_meta` differs.
- a claimed hash that does not match the actual canonical rows fails closed.
- load revalidates stored row content against the requested hash.

### Windows PowerShell 5.1 verifier reliability

- native commands such as Python unittest may emit normal progress to stderr; verifier native execution now judges success/failure by `$LASTEXITCODE` rather than treating normal stderr progress as a terminating PowerShell error.
- failed commands retain expanded diagnostic context instead of surfacing only an unrelated final `... ok` line.
- Chart repo resolution supports explicit path, environment, sibling and bounded workspace discovery.
- when the verifier owns smoke-test ports implicitly, it isolates smoke execution from unrelated services by selecting free ports; explicitly supplied ports retain fail-closed collision behavior.
- existing unrelated services are not killed or commandeered by validation.

## Implemented Stage 1 vertical capabilities

### Engine / trust boundary

- fail-closed parser and semantic analysis.
- canonical function capability registry used by prompt capability output and semantic arity/type checking.
- Capability Manifest and runtime dispatch exact-set contract.
- Playbook explicitly withholds current non-capabilities such as partial fills, pyramiding, `on_tick` / `on_fill`, loops/user functions, tuple outputs, multi-symbol requests, lookahead and direct drawing ownership.
- published scalar parameter values are fail-closed at runtime; invalid periods, fractional integer periods, unsupported MA methods, invalid JMA phase and invalid MTF intervals do not silently normalize/fallback.
- broker TIF validation and explicit lifecycle history.
- MARKET/LIMIT/STOP/STOP_LIMIT support path.
- unsupported DSL order `quantity` remains unpublished rather than being represented as a false capability.
- order argument applicability is fail-closed.
- order limit/stop expressions receive static numeric type validation.
- `bar_close` / `next_open` execution policy, including next-open strategy exits.
- OHLC stop/take-profit/trailing policy and same-bar re-entry suppression.
- deferred LIMIT/STOP submission obeys the Stage 1 single-position contract.
- DAY expiry at detected session boundaries.
- deterministic synthetic fixture independent of wall-clock time.
- DSL/data timeframe mismatch rejection when data timeframe is declared.
- MFE/MAE and closed-trade evidence.
- strategy MARKET entry/exit, risk exits and pending order fills use `BrokerEmulator` as authoritative lifecycle.
- execution rows preserve broker `order_id`, signal time, fill time, quantity and fill price.
- confirmed-bar batch/streaming-prefix parity covers ordinary indicators, confirmed MTF, persistent `on_bar` state, Broker executions and closed trades.
- representative regression covers long trend, short reversal, confirmed MTF + state, and deferred STOP_LIMIT/OCO single-position behavior.

### Research factory

- canonical OHLCV Data Contract and SHA-256 data provenance.
- immutable content-addressed market snapshot storage.
- append-only Experiment lineage and separate mutable current-head pointer.
- Grid/Random Parameter Seeker.
- deterministic candidate hash/seed.
- resumable Seeker session with cursor, cancel/resume, best-so-far and cross-session evaluation cache.
- Parameter Sensitivity evidence.
- rule-based Result Analyzer.
- structured Evidence Bundle including signal funnel, MFE/MAE, worst trades, giveback, costs and broker lifecycle evidence.
- human-mediated LLM feedback package.
- raw Prompt/Response audit memory.
- accepted/rejected/invalid Improvement Episode memory.
- post-Seeker finalized Improvement Episode linking `Before -> LLM structural candidate -> After-Seeker best`.
- repeated hypothesis similarity detection.
- deterministic structural DSL diff summary.
- persistent target-return loop with observed-best candidate separate from explicit promoted current-head.
- target loop guards for iteration/backtest/no-improvement/plateau/OOS degradation/no-new-hypothesis/parameter instability.
- immutable chronological train/holdout split with fixed OOS evaluation registry.
- A/B/C methodology descriptive statistics and OOS reporting.
- quick/full Stage 1 stress harness.

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

## Chart ownership boundary

The Stage 1 page does not load or call Lightweight Charts directly.

Current ownership path:

```text
Stage 1 experiment/backtest evidence
 -> `core/stage1_chart_document.py` semantic Chart Document projection
 -> Stage 1 iframe/postMessage protocol
 -> shared feature-blind Chart Document viewer
 -> `hoonoh57/cascading-feature-solution` Chart SSOT renderer/surface
```

`core/stage1_chart_document.py` contains Quant/experiment semantics only. Generic chart drawing remains owned by the shared Chart axis.

The Stage 1 verifier directly executes only the scoped shared-Chart dependency contracts required by Stage 1:

- `chart_document_renderer.test.mjs`
- `chart_drawing_primitives_contract.test.mjs`
- `chart_drawing_ssot_boundary.test.mjs`
- `responsive_chart_surface.test.mjs`
- `stable_pane_identity_surface.test.mjs`

These scoped contracts passed inside the trusted `Full` verifier. This must not be described as donor repository-wide compliance.

## Integrated Stage 1 stack launcher

`scripts/start_stage1_stack.ps1` remains the Windows/PowerShell 5.1 orchestration boundary for the complete Stage 1 UI stack.

It owns process lifecycle and health orchestration only; it does not copy or implement Chart rendering.

Launcher contracts include:

- Node.js >= 24 and Python dependency preflight.
- dependency installation only with explicit `-InstallDependencies`.
- exact Stage 1 and Cascade health verification.
- fail-closed rejection for explicitly requested occupied ports.
- direct `node scripts/serve.mjs` and `python -m uvicorn stage1_main:app` process ownership.
- partial-start failure cleanup.
- temporary PID/log state outside the repository.
- guarded stop by process command-line marker.
- `Start`, `Status`, `Stop`, `Preflight`, and `Smoke` actions.
- literal `[PASS]` smoke-success prefix contract.

## Methodology boundary

The automated Stage 1 validation proves the implementation and deterministic validation boundaries executed successfully on the trusted Windows environment. It does not prove that any strategy is profitable or generalizes to unseen markets.

Immutable chronological OOS partitioning, fixed split identity, OOS evaluation and methodology summaries are implemented and validated as infrastructure. Profitability/generalization claims require later research evidence, not Stage 1 implementation PASS.

## Hosted validation note

Earlier GitHub Actions attempts failed before executable steps were available (`steps=[]`). Those runs remain classified as environment/service issues and are neither product failures nor PASS evidence.

The trusted local Windows PowerShell 5.1 `Full` verifier PASS now supplies the executable Stage 1 system-validation evidence that was previously missing. There was no need to weaken assertions to compensate for hosted-runner failures.

## Remaining Stage 1 gate

Only the consolidated human WYSIWYG/UI verification remains before Stage 1 can be closed as a product milestone.

The consolidated UI verification should exercise the integrated paved road rather than isolated implementation details:

1. launch the complete Stage 1 stack through the supported launcher;
2. create/run a baseline strategy and inspect metrics/evidence;
3. discover parameters and run/resume a Seeker;
4. inspect parameter sensitivity and candidate comparison;
5. generate LLM feedback, apply one structural candidate and run the post-structural Seeker path;
6. inspect Improvement Episode lineage and explicit promotion behavior;
7. run fixed OOS evaluation and methodology view;
8. inspect the exact experiment in the shared Chart SSOT viewer, including panes/markers/references and responsive behavior;
9. verify history/A-B comparison and that the UI exposes no unsupported capability or hidden auto-promotion.

Any UI defect found in this pass must be repaired as one final UI remediation tranche, followed by rerunning the affected automated boundary and the Full verifier if the change touches system behavior.

## Do not do

- Do not return to per-workstream user verification.
- Do not move to Stage 2+ until the consolidated Stage 1 UI gate is closed.
- Do not claim profitability, live-trading readiness or donor-wide Chart compliance from the Stage 1 Full PASS.
- Do not restore direct chart-library ownership in Stage 1.
- Do not duplicate generic chart drawing in DSL/UI code.
- Do not weaken validators/tests to manufacture green results.
- Do not treat OOS infrastructure as profitability evidence.
- Do not auto-promote an observed best candidate without the explicit promotion contract.

## Next action

1. perform one consolidated Stage 1 WYSIWYG/UI verification against the integrated paved road above;
2. record all UI findings together rather than validating each workstream separately;
3. repair any UI defects in one final remediation tranche;
4. rerun the affected automated contracts and, when system behavior changed, `scripts/verify_stage1.ps1 -Mode Full`;
5. update this state to Stage 1 closed only after the consolidated UI gate is green; then consider Stage 2.
