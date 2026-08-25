# Quant DSL Current State

Status: **STAGE1_CONTINUOUS_BUILD_IN_PROGRESS**
Updated: 2026-08-25 KST

## Authority

- Product roadmap: `PRODUCT_IMPLEMENTATION_PLAN.md`
- Stage 1 execution policy: `STAGE1_EXECUTION_POLICY.md`
- DSL language contract: `QUANT_DSL_PLAYBOOK.md`
- Engine audit criteria: `DSL_ENGINE_AUDIT.md`

## Current goal

Complete `S1.0 ~ S1.13` as one continuous Stage 1 vertical slice without per-workstream user verification. After all 14 workstreams are connected, execute automated operational/stress tests, fix defects, then request one consolidated UI verification.

## Stage 1 workstreams

- [x] S1.0 Authority / State Hygiene
- [~] S1.1 Engine Trust Boundary Remediation
- [ ] S1.2 Single-Symbol DSL Capability Completion
- [ ] S1.3 Data Contract / Provenance
- [ ] S1.4 Backtest Evidence Engine
- [ ] S1.5 Immutable Experiment Store
- [ ] S1.6 Parameter Seeker
- [ ] S1.7 Result Analyzer
- [ ] S1.8 Human-Mediated LLM Improvement Loop
- [ ] S1.9 Improvement Episode Memory
- [ ] S1.10 Target-Return Improvement Loop
- [ ] S1.11 Single-Symbol Chart Audit
- [ ] S1.12 Semi-Automation Product UX
- [ ] S1.13 Methodology Validation

Legend: `[x]` functionally wired, `[~]` actively being remediated, `[ ]` pending in the continuous build.

## Known trust-boundary remediation already applied in current build

- Broker TIF validation and explicit lifecycle history.
- Backtest accounting rewritten around explicit long/short cash flows, entry+exit costs, closed-trade net PnL and MFE/MAE evidence.
- `next_open` strategy exits scheduled against the previous confirmed signal and filled at the next open.
- DAY order expiration is wired to detected session boundaries.
- optional DSL/data timeframe mismatch rejection.
- deterministic synthetic fixture no longer depends on current wall-clock time.

These items are implementation progress only; they are not global PASS evidence until the Stage 1 system test suite runs.

## Do not do during Stage 1 continuous build

- Do not request user UI verification for each workstream.
- Do not switch priority to Stage 2+ multi-symbol/beta/sector/portfolio work.
- Do not claim profitability or product completion from individual green tests.
- Do not weaken validators/tests to make a failure green.

## Next action

Continue S1.1/S1.2 trust + DSL capability work, then connect S1.3~S1.13 without waiting for user verification. After all 14 are wired, create and run the Stage 1 operational/stress-test plan.
