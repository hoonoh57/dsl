# Quant DSL Current State

Status: **P1_TACTICAL_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `MULTI_LAYER_DSL_ARCHITECTURE.md` — product architecture and Tactical Unit methodology.
2. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — current P1 data/provider/UI/verification boundary.
3. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and validated Stage 1 kernel plan.
4. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification operating policy.
5. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
6. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.

## Product path

The validated single-symbol engine is the instrument-level tactical kernel, not
the final research methodology.

```text
Market Regime / Opportunity Window
 -> eligible Tactical Unit
 -> point-in-time multi-symbol cohort
 -> relative / lead-lag / group evidence
 -> unit-specific DSL tactic
 -> common execution policy
 -> parallel deterministic execution
 -> scenario/cohort/window validation
 -> promote / reject / remember
```

`1516 @ 09:05`, High-Beta, Leading-Sector, Theme/Policy and future
condition-search cohorts are separate Tactical Units and may own different
features, timing contracts and tactics.

## Trusted checkpoint before P1

The P1 branch is based on the P0 multi-layer checkpoint whose trusted local
Windows PowerShell 5.1 verifier returned:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

That PASS remains evidence for the P0 base only. It does not validate later P1
mutations.

## P1 implementation now present

### 1516 exact point-in-time cohort

`core/tactical_providers.py`

- exact `performance_result` group by date/time/condition/hold period;
- `code`, `name`, `search_volume` retained as point-in-time evidence;
- future returns, `max_ret_in_period`, labels and actual future rank isolated as
  post-execution outcomes;
- malformed/inconsistent groups fail closed;
- no nearby cohort or dummy fallback.

### Explicit stored minute market source

`core/tactical_market.py`

- schema-adaptive OHLCV reader;
- strict timeframe and warm-up coverage;
- timestamp/OHLCV integrity checks;
- no production database/table guess;
- source must be explicit or supplied by `TACTICAL_MINUTE_DATABASE` /
  `TACTICAL_MINUTE_TABLE`.

Connected-source audit found no authority for the previously assumed
`minute_candles_5m` production table. A known K150-only minute table in another
research repository is not substituted for general 1516 membership.

### 1516 execution/evaluation

`core/tactical_research.py`

```text
exact frozen cohort
 -> canonical per-symbol bars
 -> capture + 1 second entry authorization
 -> existing MultiSymbolAnalysisEngine / Broker authority
 -> immutable Tactical Scenario/Run
 -> official outcome merge after execution only
 -> retention / precision evidence
```

For a 09:05:00 cohort the common entry gate is 09:05:01. Point-in-time feature
ranking such as `feature:search_volume` never uses future outcome fields.

### High-Beta exact-as-of cohort

`core/tactical_beta_provider.py`

- daily `as_of` cutoff only;
- exact benchmark availability required;
- beta = covariance(benchmark return, symbol return) / benchmark return variance;
- overlap threshold and top-N ranking;
- no nearby-date or future-data fallback;
- production database is explicit or `TACTICAL_DAILY_DATABASE`;
- `daily_candles` is the supported default table contract, overridable by
  `TACTICAL_DAILY_TABLE`.

`tactical_main.py` now exposes exact High-Beta **cohort inspection**. It does not
reuse the same-session 1516 execution timing contract; next-session High-Beta
execution remains a later explicit contract.

### Sector exact membership boundary

`core/tactical_sector_provider.py`

- exact `as_of + sector_id` snapshot;
- explicit database/table only;
- static legacy leader/follower definitions and dummy fallback are not accepted
  as production point-in-time authority.

A concrete production sector snapshot source is still unresolved, so this
provider remains fail-closed until one is explicitly identified.

### Multi-symbol Chart evidence

`core/tactical_chart_document.py`

- generic `chart-document/v1` only;
- comparison symbols selected from point-in-time ranking only;
- exact capture cutoff retained in metadata;
- capture visual region uses two strictly increasing real focus-market bar times;
- missing non-zero cutoff evidence fails closed.

This fixes the prior zero-width `vertical-region` defect. The shared Chart SSOT
remains the only Chart-native rendering owner.

### Tactical UI/API

`tactical_main.py`:

```text
/tactical
GET  /api/stage1/tactical/1516/cohort
POST /api/stage1/tactical/1516/run
GET  /api/stage1/tactical/high-beta/cohort
GET  /api/stage1/tactical/health
```

The 1516 inspection route omits future outcomes. The Tactical UI no longer
pre-fills an undocumented minute DB/table and requires explicit deployment
configuration.

### Validation and operational harness

Implemented:

- `scripts/start_tactical_stack.ps1`
  - Start / Status / Stop / Preflight / Smoke;
  - shared Chart health and Tactical health;
  - Node >= 24 and Python dependency checks;
  - bounded Chart repo discovery;
  - tracked-process-only stop;
  - PowerShell 5.1-safe explicit PID state assignments.
- `scripts/tactical_contract_stress.py`
  - worker-count determinism;
  - larger cohort execution;
  - Chart projection;
  - point-in-time leak rejection;
  - whole-scenario corrupted-data failure.
- `scripts/verify_tactical_p1.ps1`
  - base Stage 1 verification;
  - Tactical preflight;
  - quick/full Tactical stress;
  - isolated-port live Tactical/Chart smoke;
  - final P1 PASS marker only after all prior steps succeed.

New/updated Stage 1-discovered tests cover 1516 providers, market authority,
research orchestration, visible Chart cutoff geometry, High-Beta authority,
sector snapshot semantics, validation manifest behavior and launcher/API
contracts.

No legacy assertion was weakened for this tranche.

## Current validation status

Source remediation and static authority review are complete enough to enter the
trusted executable boundary, but a trusted Windows Full verifier has **not yet
been recorded for P1**.

Therefore do not claim:

- Tactical P1 Full PASS;
- production profitability/generalization;
- live trading readiness;
- a concrete production sector snapshot authority;
- a concrete 1516 minute table unless supplied by deployment configuration;
- donor repository-wide Chart compliance.

`REMEDIATION_REQUIRED` remains authoritative.

## Next action

After this P1 branch is fast-forwarded to `main`, perform one consolidated
trusted Windows verification only:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not begin per-feature UI inspection before that automated boundary is green.
If the verifier fails, classify the first failure as test defect / product defect /
authority drift / environment issue / unknown before changing code.

If the verifier returns:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

record that exact commit as P1 Full-verified and then perform one consolidated
WYSIWYG/UI validation.
