# Quant DSL Current State

Status: **EVOLVING_MICRO_WARRIOR_E0_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
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

## Product direction

Two orders remain intentionally different.

### Final runtime / deployment

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

### Current research / development

```text
minimal micro tactic
 -> many independent BattleCases
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

Macro functionality is architecturally reserved now, but the current priority is to breed compact, independently survivable Korean regular-session micro tactics before macro assistance is used for deployment selection.

## Autonomous micro-warrior doctrine

A higher-layer `allowed=true` is permission to operate, not a forced entry.

Actual entry authority remains conjunctive:

```text
higher-layer permission
AND local survival/admissibility
AND tactic trigger
AND common risk/execution policy
```

`NO_TRADE` is a valid survival result. A tactic that only survives because macro filters remove all difficult battles is not yet considered a strong autonomous micro warrior.

The target is not maximum indicator count. Each tactic family must remain inside a declared personal `CapabilityBudget` so the individual tactic can operate its own weapons reliably.

## Macro-ready seam already implemented

`core/battlefield_context.py`

- `ContextLayerSnapshot`
- `BattlefieldContext`
- `DeploymentDecision`

Current micro baseline uses `BattlefieldContext(mode="NEUTRAL")`.

Later market/index, breadth/volatility, sector, high-beta, theme/policy, leader/follower and other point-in-time context can attach as immutable snapshots without rewriting Parser, Runtime, Backtest, BrokerEmulator or historical micro evidence.

## Micro tactical discovery already implemented

`core/tactical_discovery.py`

- `BattleCase` identity is symbol + date/case, not symbol alone;
- one tactic executes over a frozen multi-symbol/multi-date BattleCase set;
- bounded parallel workers preserve input order and deterministic hashes;
- default baseline requires NEUTRAL context and uniform execution settings;
- any malformed case fails the whole discovery run;
- complete per-case Backtest evidence remains available;
- aggregate evidence includes return, MDD, PF, cost, MFE/MAE/giveback, trade/no-trade counts and winner concentration.

`core/tactical_competition.py`

- tactics compete only on the same frozen `case_set_hash` and context policy;
- no hidden universal score;
- per-metric leaderboards + conservative Pareto frontier.

## E0 evolving micro-warrior implementation now present

### Deterministic failure analysis

`core/tactical_failure.py`

Consumes immutable `tactical_discovery/v1` profiles and produces `tactical_failure/v1` evidence.

Initial failure tags:

```text
LOSS
SEVERE_LOSS
DRAWDOWN
ADVERSE_EXCURSION
WHIPSAW
MFE_GIVEBACK
```

For each cluster it records affected BattleCases, frequency, negative return impact and suggested capability gaps.

`NO_TRADE` is explicitly `ABSTENTION_IS_NOT_FAILURE_BY_DEFAULT`.

This taxonomy is intentionally evidence-limited. Late-entry, local-leader, re-engagement, liquidity and time-of-day failure classes are deferred until causal local-state evidence is implemented.

### Personal arsenal / Skill contract

`core/tactical_evolution.py`

`SkillSpec` declares:

```text
skill_id
capability
implementation
addresses_failure_tags
cost
metadata
```

`CapabilityBudget` currently bounds:

```text
skills
complexity units
indicators
parameters
state variables
decision branches
setup variants
```

Costs are declared provenance. The engine does not infer hidden complexity from DSL source length.

### Immutable generations

`EvolutionGeneration` records:

```text
family_id
generation_index
candidate_hash
profile_run_hash
case_set_hash
context_policy_hash
acquired_skills
capability_usage
parent_generation_hash
acquired_from_failure_hash
generation_hash
```

A generation is therefore traceable back to the exact battle profile and exact failure evidence that justified its acquired skill.

### One-skill Evolution Arena

`EvolutionArena.evaluate_upgrade()` accepts exactly one new `SkillSpec` for one parent-child comparison.

Default automatic-promotion invariants:

1. same frozen `case_set_hash`;
2. same context policy;
3. failure report must come from the parent profile;
4. new skill must address an observed parent failure;
5. capability usage must remain inside the declared budget;
6. child must improve at least one material mission/survival axis;
7. no survival axis may regress beyond the declared `PromotionContract` tolerance.

Primary survival axes include profitable-case rate, worst MDD, worst-case return, cost/case and winner concentration. MFE giveback reduction is also recognized as an improvement.

Decisions are:

```text
ACCEPT -> verified child generation may be created
REJECT -> clear regression without compensating improvement
REVIEW -> mixed trade-off; parent remains head
```

There is no opaque weighted score.

### Evolution experience ledger

`core/tactical_evolution_store.py`

Append-only SQLite evidence tables now persist:

- every tactical discovery profile used by an evolution family;
- every failure report;
- every immutable generation;
- every ACCEPT / REJECT / REVIEW decision;
- an explicit mutable family head separate from immutable history.

Recording an accepted child does not silently promote it. Promotion remains an explicit operation.

This preserves losing/rejected experience rather than remembering only winners.

### New regression contracts

Stage1 discovery will include:

- `test_stage1_tactical_evolution.py`
- `test_stage1_tactical_evolution_store.py`

Contracts cover NO_TRADE semantics, observed-failure relevance, one-skill lineage, same-battlefield comparison, survival regression, capability-budget rejection, immutable experience persistence and explicit promotion.

## Tactical P1 infrastructure still present

The earlier P1 slice remains active:

- exact 1516 point-in-time cohort provider with future outcomes isolated;
- explicit stored-minute source contract; no guessed general minute table;
- 1516 capture+1-second execution path through MultiSymbolAnalysisEngine/Broker;
- exact-as-of High-Beta cohort inspection;
- fail-closed exact sector membership boundary;
- multi-symbol Chart Document evidence;
- Tactical UI/API and launcher;
- tactical quick/full stress and consolidated verifier.

The Tactical stress script direct-execution import-root defect was remediated by explicitly adding the repository root before importing `core.*`.

## Trusted validation history

A trusted local Windows PowerShell 5.1 Full verifier PASS exists for the earlier multi-layer P0 checkpoint:

```text
[PASS] Stage 1 verification completed: mode=Full.
```

A later P1 Full attempt found a High-Beta test-fixture defect; the product beta implementation was not changed and the fixture was corrected.

The next P1 run then found a tactical stress harness environment/import defect (`ModuleNotFoundError: core`); the direct-script repository-root setup was fixed.

The E0 evolution mutations were added after that failure and have not yet received a trusted local Full PASS.

## Current validation status

Do not claim yet:

- Tactical P1 / E0 Full PASS;
- any tactic is the strongest or profitable;
- autonomous evolution has produced a superior live tactic;
- production profitability/generalization;
- live trading readiness;
- completed macro deployment rules;
- a concrete production sector snapshot authority;
- a concrete general 1516 minute table unless supplied by deployment configuration;
- donor repository-wide Chart compliance.

`REMEDIATION_REQUIRED` remains authoritative.

## Next implementation sequence after trusted boundary

Continue micro strengthening in this order:

1. authoritative Korean regular-session `BattleCaseProvider`;
2. `TacticFamilyRegistry` + legal `SkillSpec` upgrade tree + CapabilityBudget per family;
3. multi-BattleCase Parameter Seeker adapter;
4. causal Tactical Characterizer for time/range/volatility/liquidity/signal-density/local-leader/entry-latency/re-engagement evidence;
5. bounded structural Skill Generator that proposes one child capability from observed gaps;
6. Train / Validation / OOS / harsh-case Evolution Arena;
7. game-style generation/skill-tree Evidence UI;
8. only then macro/sector/high-beta/theme context attribution and deployment command.

## Next automated boundary

After pulling current `main`, run one consolidated trusted Windows verification:

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

Do not begin per-feature UI inspection before this automated boundary is green.

If it fails, classify the first failure as test defect / product defect / authority drift / environment issue / unknown before changing code.
