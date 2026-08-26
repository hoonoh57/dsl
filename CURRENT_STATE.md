# Quant DSL Current State

Status: **E3A_CAUSAL_TACTICAL_OBSERVATION_IMPLEMENTED_AWAITING_TRUSTED_FULL_VALIDATION / REMEDIATION_REQUIRED**  
Updated: 2026-08-26 KST

## Authority

Read in this order:

1. `EVOLVING_MICRO_WARRIOR_PLAN.md` — one-skill evolution doctrine, capability-budget and immutable-generation contract.
2. `ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` — local battlefield observation/memory/learner/resolution-mode sequencing.
3. `MICRO_FIRST_MACRO_READY_ARCHITECTURE.md` — micro-first research order and macro-ready extension seam.
4. `MULTI_LAYER_DSL_ARCHITECTURE.md` — final macro-to-micro runtime/deployment architecture.
5. `MICRO_TACTICAL_DISCOVERY_IMPLEMENTATION.md` — micro discovery/competition implementation checkpoint.
6. `P1_TACTICAL_DATA_IMPLEMENTATION.md` — P1 data/provider/UI/verification boundary.
7. `PRODUCT_IMPLEMENTATION_PLAN.md` — original roadmap and Stage 1 kernel plan.
8. `STAGE1_EXECUTION_POLICY.md` — continuous implementation / verification policy.
9. `QUANT_DSL_PLAYBOOK.md` — official generated-DSL language contract.
10. `DSL_ENGINE_AUDIT.md` — engine trust-boundary criteria.
11. `PROGRESS_CHECKPOINT_2026-08-26.md` — trusted local Full PASS evidence checkpoints.

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

Current micro research is intentionally bottom-up:

```text
minimal tactic family
 -> frozen BattleCases
 -> causal local observations
 -> tactical experience / memory
 -> local survival/opportunity learning
 -> one-skill evolution + numeric re-seek
 -> Validation / OOS / harsh replay
 -> ACCEPT / REJECT / REVIEW
 -> immutable lineage
 -> later macro attribution/deployment
```

Macro intelligence is an amplifier, not life support. A micro warrior must learn local battlefield suitability and retain `NO_TRADE` / `ABSTAIN` authority before macro assistance exists.

## Trusted foundations

### DSL / execution kernel

The typed DSL parser/runtime, indicator implementation, `BacktestEngine`, `BrokerEmulator`, common execution policy, Stage 1 app and Chart SSOT boundary remain trusted lower-level authorities. Learning layers may not bypass or self-modify them.

### Micro discovery / competition

`core/tactical_discovery.py`

- `BattleCase` identity separates symbol/date/case;
- one tactic executes over frozen multi-symbol/multi-date cases;
- bounded workers preserve deterministic order/hashes;
- neutral-context baseline and uniform execution settings are enforced;
- malformed cases fail the run;
- complete per-case backtest evidence remains immutable.

`core/tactical_competition.py`

- only tactics with the same frozen `case_set_hash` and context policy compete;
- no hidden universal score;
- per-metric leaderboards and conservative Pareto evidence remain authoritative.

### E0 evolving micro-warrior contracts

Implemented and previously trusted:

- deterministic failure analysis;
- `SkillSpec` and `CapabilityBudget`;
- immutable `EvolutionGeneration`;
- one-skill `EvolutionArena`;
- conservative ACCEPT / REJECT / REVIEW;
- append-only evolution evidence store with explicit family-head promotion.

Current failure evidence includes:

```text
LOSS
SEVERE_LOSS
DRAWDOWN
ADVERSE_EXCURSION
WHIPSAW
MFE_GIVEBACK
UNRESOLVED_POSITION
```

`NO_TRADE` is abstention by default. An entered but unresolved position is active failure evidence.

### E1 Korean regular-session BattleCase authority

`core/battlecase_provider.py` provides:

- exact caller-supplied symbol/date requests;
- explicit `SessionMarketProvider` and `source_authority`;
- no production universe guessing or dummy source;
- canonical source/instrument/timeframe metadata validation;
- Korean regular-session clock validation;
- warm-up/history and current-session coverage validation;
- rejection of requested-day bars after configured `end_time`;
- authoritative source/session-policy identity in frozen evidence.

Trusted Full checkpoint:

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

`core/tactic_family.py` enforces:

- observed-failure relevance;
- remaining `CapabilityBudget`;
- `requires_skills` prerequisites;
- `excludes_skills` exclusions;
- unknown/self/conflicting dependencies fail closed;
- dependency cycles fail closed.

`core/tactic_family_catalog.py` currently contains only:

```text
JMA_TREND_CROSS_RESUME_V1
```

with bounded skills:

```text
JMA_RANGE_COOLDOWN
JMA_ADX_ENTRY_QUALITY
JMA_CONFIRM_AFTER_RANGE
JMA_FAST_PROFIT_PROTECTION
```

The first E2 Full attempt exposed a **test defect**: a 5m JMA DSL regression test used the default 1d synthetic fixture. The product timeframe mismatch check was correct and was not weakened. The test was remediated with an explicit deterministic 5m fixture.

After pulling the remediated `main`, the operator reported:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E2 is trusted Full-validated at executable checkpoint:**

```text
620f741730b0ae821fc48affd22b5420f38a6cac
```

## Adaptive micro-warrior learning doctrine

`ADAPTIVE_MICRO_WARRIOR_LEARNING_ARCHITECTURE.md` makes local learning first-class.

The target decision loop is:

```text
TACTIC OPPORTUNITY
 -> CAUSAL LOCAL OBSERVATION
 -> TACTICAL MEMORY
 -> SURVIVAL / OPPORTUNITY / UNCERTAINTY ESTIMATE
 -> RESOLUTION / EXECUTION MODE SELECTION
 -> ENTER / WAIT / ABSTAIN
 -> ACTUAL + SHADOW EVIDENCE
 -> NEXT TRAINING MEMORY VERSION
```

The warrior should learn local facts such as:

- time-of-day and session phase;
- JMA crossover geometry, slope, spread and acceleration;
- SMA60 slope and price distance;
- recent appreciation / overextension;
- high/low structural progression even when candle bodies are weak;
- volatility, volume and execution-risk proxies;
- later VI/event state when authoritative event data exists;
- later realized self-state from prior closed battles only.

Historical relative features and normalizers must be fitted on Train and frozen for Validation/OOS.

### Adaptive timeframe principle

A tactic may eventually choose among separately validated family modes such as:

```text
JMA_TCR_5M
JMA_TCR_3M
JMA_TCR_1M
JMA_TCR_TICK_N
```

This is **family-level resolution-mode selection**, not runtime mutation of one DSL's `timeframe`.

Current Stage 1 DSL supports one declared base timeframe and only completed higher-timeframe MTF reads. Arbitrary lower-timeframe/tick switching is not a current DSL capability and must not be invented.

Tick mode remains future-only until authoritative tick storage, deterministic aggregation, knowledge-cutoff alignment, warm-up rules and Broker execution semantics are explicitly implemented and verified.

## E3A current executable tranche: causal TacticalObservation

`core/tactical_observation.py` now introduces an immutable JMA/local battlefield sensory snapshot.

Initial observation features include:

### Signal / JMA geometry

```text
jma_fast / jma_slow
jma_spread_pct
jma_fast_slope_pct
jma_slow_slope_pct
jma_spread_velocity_pct
jma_fast_acceleration_pct
jma_cross_up_now / jma_cross_down_now
bars_since_jma_cross_up
jma_spread_atr
```

### Slow trend / location

```text
sma60
sma60_slope_pct
price_to_sma60_pct
price_to_sma60_atr
return_from_session_open_pct
recent_return_3bar_pct
recent_return_6bar_pct
recent_return_12bar_pct
session high/low distance
```

### Volatility / volume / execution proxies

```text
atr_pct
current_range_pct
range_vs_recent
volume_ratio
volume_change_vs_recent_pct
bar_gap_pct
```

### Primitive price geometry

```text
higher_high_ratio
higher_low_ratio
lower_high_ratio
lower_low_ratio
swing_high_slope_pct
swing_low_slope_pct
body_up_ratio
close_location_in_range
wick_asymmetry
breakout_distance_pct
```

This deliberately supplies primitive causal geometry so later learning can discover rising consolidation, trend stair-steps, compression/breakout and similar structures without hard-coding every named chart pattern as a trade rule.

### Time state

```text
minutes_from_open
minutes_to_close
session_progress_ratio
```

The E3A builder uses only the market prefix ending at the requested observation timestamp. Future bars are not inputs.

`test_stage1_tactical_observation.py` adds regression contracts for:

- JMA/trend/time/volatility/price-structure exposure;
- rising high/low structure with weak/mixed candle bodies;
- future-bar mutation cannot change an earlier observation's feature values;
- timeframe mismatch fails closed;
- insufficient warm-up fails closed.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- adaptive local-battlefield learning architecture is authoritative;
- E3A causal TacticalObservation source/tests are implemented.

Do **not** claim yet:

- trusted Full PASS for E3A executable changes;
- TacticalMemory or a trained LocalBattlefieldLearner;
- automatic adaptive 5m/3m/1m/tick deployment;
- learned profitability/generalization;
- live-trading readiness;
- completed macro deployment policy;
- concrete production sector or general 1516 minute authority unless explicitly configured;
- donor repository-wide Chart compliance;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains authoritative for broader repository compliance.

## Revised next sequence

After E3A is trusted green:

1. **E3B TacticalExperience / TacticalMemory** — record every candidate opportunity, actual outcome, optional shadow outcome, support/confidence and immutable memory versions;
2. **E3C LocalBattlefieldLearner / LocalEngagementPolicy** — estimate profitable/severe-loss probability, MFE/MAE/cost/slippage/uncertainty and decide ENTER/WAIT/ABSTAIN;
3. **E3D Multi-Battle Parameter Seeker** — tune numeric parameters on frozen BattleCases while structure remains fixed;
4. **E4 Failure / Opportunity Characterizer** — richer time, range transition, liquidity, latency, VI/event, overextension and re-engagement evidence;
5. **E5 Structural Skill Generator** — propose one bounded legal child from observed gaps;
6. **E6 Train / Validation / OOS / Harsh Arena**;
7. **E7 Evolution Memory / Evidence UI**;
8. **E8 Macro Context Attribution / Deployment**.

Do not begin E3B executable work before the E3A consolidated boundary is green.

## Next automated boundary

```powershell
git pull --ff-only origin main
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as `test defect / product defect / authority drift / environment issue / unknown` before changing code.
