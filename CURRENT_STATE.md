# Quant DSL Current State

Status: **E2_JMA_FAMILY_CATALOG_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `EVOLVING_MICRO_WARRIOR_PLAN.md` — current micro-warrior evolution doctrine, one-skill progression and capability-budget contract.
2. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — micro-first research order and macro-ready extension seam.
3. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final macro-to-micro runtime/deployment architecture and Tactical Unit methodology.
4. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — micro discovery/competition implementation checkpoint.
5. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
6. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and validated Stage 1 kernel plan.
7. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification policy.
8. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
9. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
10. `PROGRESS_CHECKPOINT_2026-08-26.md` — trusted local Full PASS evidence checkpoints.

## Product direction

Final runtime/deployment remains top-down:

```text
Battlefield Context
 -> Market / Regime
 -> Sector / Group / Narrative
 -> eligible Tactical Unit
 -> symbol selection / ranking
 -> validated evolving micro tactic
 -> common execution policy
 -> BrokerEmulator
```

Current research/development remains bottom-up:

```text
minimal micro tactic
 -> frozen BattleCases
 -> failure analysis
 -> capability gap
 -> one-skill child mutation
 -> numeric re-seek
 -> replay / Validation / OOS / harsh cases
 -> ACCEPT / REJECT / REVIEW
 -> immutable generation memory
 -> repeat
 -> later context attribution / macro deployment
```

Macro intelligence is architecturally reserved but is not life support for weak micro tactics. `NO_TRADE` remains a valid local survival outcome.

## Implemented trusted foundations

### Micro discovery / competition

`core/tactical_discovery.py`

- `BattleCase` identity is case/symbol/date, not symbol alone;
- one tactic executes over frozen multi-symbol/multi-date cases;
- bounded parallel workers preserve deterministic ordering/hashes;
- baseline discovery requires neutral context and uniform execution settings;
- malformed cases fail the run;
- complete per-case backtest evidence remains immutable.

`core/tactical_competition.py`

- only same `case_set_hash` / context-policy tactics compete;
- no hidden universal score;
- per-metric leaderboards and conservative Pareto evidence.

### E0 evolving micro-warrior contracts

Implemented:

- deterministic failure analysis in `core/tactical_failure.py`;
- `SkillSpec`, `CapabilityBudget`, immutable `EvolutionGeneration`;
- one-skill `EvolutionArena` with same-battlefield and survival gates;
- append-only evolution evidence store with explicit family head promotion.

Current failure taxonomy includes:

```text
LOSS
SEVERE_LOSS
DRAWDOWN
ADVERSE_EXCURSION
WHIPSAW
MFE_GIVEBACK
UNRESOLVED_POSITION
```

`NO_TRADE` is abstention by default; an entered but unresolved position is active failure evidence, not abstention.

### E1 Korean regular-session BattleCase contract

`core/battlecase_provider.py` provides the strict E1 boundary:

- exact caller-supplied symbol/date requests;
- explicit `SessionMarketProvider` and explicit `source_authority`;
- no production universe guessing and no dummy/fallback source;
- canonical source/instrument/timeframe metadata validation;
- Korean regular-session clock validation;
- required warm-up/history coverage;
- required current-session bar coverage;
- rejection of requested-day bars after configured `end_time`;
- authoritative source/session-policy identity preserved in frozen evidence.

This is structurally complete while deliberately refusing to guess a concrete deployment database/table.

## Trusted validation checkpoints

### Earlier E0 / E1-E2 foundation

Trusted Windows PowerShell 5.1 Full PASS exists for executable checkpoint:

```text
ac01525223f897f155de63f02529b0a6429a0882
```

Reported result:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

### E1 Korean regular-session contract

Before the trusted run, the operator executed `git pull --ff-only origin main` and received `Already up to date.` Remote `main` HEAD at that boundary was:

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
```

The operator then reported:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E1 is trusted Full-validated at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`.**

The consolidated verifier includes `python -m unittest discover -v -p test_stage1_*.py`, so Stage 1 regression contracts present in that checkout were inside the trusted boundary.

## E2 current tranche: first production-style family catalog

E2 now moves beyond the generic registry foundation, but only for one family in this tranche.

### Generic legal skill-tree enforcement

`core/tactic_family.py` now additionally enforces:

- `requires_skills` prerequisites;
- `excludes_skills` mutual exclusions;
- unknown dependency references fail closed;
- self-dependencies fail closed;
- conflicting require/exclude references fail closed;
- dependency cycles fail closed;
- runtime legal-skill selection honors acquired prerequisites/exclusions in addition to observed failure relevance and remaining `CapabilityBudget`.

This remains feature-blind evolution infrastructure; it does not modify Parser, Runtime, Backtest or BrokerEmulator.

### JMA trend/crossover/resume family

`core/tactic_family_catalog.py` introduces only:

```text
JMA_TREND_CROSS_RESUME_V1
```

The Generation-0 DSL is a compact long-only 5-minute JMA crossover/resume base using the official DSL capabilities (`ta.sma`, `ta.jma`, crossover/crossunder).

Declared bounded arsenal:

```text
max skills             = 3
max complexity units   = 8
max indicators         = 5
max parameters         = 12
max state variables    = 2
max branches           = 7
max setup variants     = 2
```

Declared legal skills:

```text
JMA_RANGE_COOLDOWN
  -> RANGE_DEFENSE
  -> WHIPSAW / DRAWDOWN

JMA_ADX_ENTRY_QUALITY
  -> ENTRY_QUALITY
  -> LOSS / ADVERSE_EXCURSION / WHIPSAW

JMA_CONFIRM_AFTER_RANGE
  -> ENGAGEMENT_DISCIPLINE
  -> LOSS / SEVERE_LOSS / WHIPSAW
  -> requires JMA_RANGE_COOLDOWN

JMA_FAST_PROFIT_PROTECTION
  -> PROFIT_PROTECTION
  -> MFE_GIVEBACK / UNRESOLVED_POSITION
```

Each skill carries explicit implementation intent, parameter bounds/defaults and declared capability cost. The catalog itself does not rewrite DSL; a later structural generator must instantiate exactly one legal child and the existing Evolution Arena judges the resulting evidence.

`build_default_tactic_family_registry()` currently returns **only this one family**. Adding VWAP, opening-range, pullback/re-breakout, volatility-expansion or trading-value families is a separate executable tranche after this boundary is trusted green.

### E2 regression contracts

`test_stage1_tactic_family_catalog.py` covers:

- default registry contains only the first JMA family;
- Generation-0 JMA DSL executes through `BacktestEngine`;
- G0 legal skills are failure-relevant and prerequisite-safe;
- post-range confirmation unlocks only after range defense is acquired;
- dependency cycles fail closed;
- unknown dependency references fail closed.

## Current validation status

May claim:

- trusted Tactical P1 Full PASS at executable checkpoint `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E1 Korean regular-session contract is trusted green at that checkpoint;
- E2 first JMA family catalog and generic legal-tree enforcement are implemented in source.

Do **not** claim yet:

- trusted Full PASS for the new E2 executable mutations;
- that JMA or any tactic is strongest/profitable;
- that autonomous evolution has produced a superior live tactic;
- production profitability/generalization or live-trading readiness;
- a concrete production sector snapshot authority;
- a concrete general 1516 minute table unless supplied by deployment configuration;
- donor repository-wide Chart compliance;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance and is separate from checkpoint-level Tactical P1 verification.

## Next sequence

Do not add another tactic family yet.

After the E2 JMA boundary is trusted green:

1. decide whether the next micro-tranche is a second family catalog or the E3 multi-BattleCase Parameter Seeker adapter based on the authoritative evolution plan;
2. keep every family inside its own explicit `CapabilityBudget`;
3. continue one-skill evidence gating and immutable generation history;
4. only after robust micro generations exist, proceed to causal characterizer / structural generator / OOS harsh arena / macro attribution.

## Next automated boundary

Pull current `main` and run:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first failure as `test defect / product defect / authority drift / environment issue / unknown` before changing code.
