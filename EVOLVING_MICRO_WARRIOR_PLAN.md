# Evolving Micro-Warrior Training Plan

Status: **AUTHORITATIVE MICRO-EVOLUTION ADDENDUM / 2026-08-26 KST**

## 1. Product objective

The minimum verified tactical unit is treated as a reusable war resource.  The objective is not to build a tactic that obeys every deployment order blindly.  It is to breed a compact tactical agent that:

- can survive across many local market environments;
- can refuse low-quality engagement through NO_TRADE;
- learns from repeated battle evidence;
- acquires only capabilities justified by observed failure;
- adds one capability/skill at a time so incremental edge is attributable;
- preserves a bounded personal arsenal / capability budget;
- evolves through immutable generations without modifying the trusted engine;
- can later consume macro battlefield intelligence without depending on it for basic survival.

The long-term probability of individual victory should improve by reducing repeated lethal mistakes and by improving mission execution, not by hiding difficult battles behind ever-more filters.

## 2. Game-style progression model

```text
Generation 0: minimal base capability
  -> fight frozen BattleCases
  -> record win / loss / NO_TRADE / MFE / MAE / cost / drawdown
  -> cluster repeated failure
  -> identify capability gap
  -> propose several small Skill candidates
  -> create one-skill child per candidate
  -> Parameter Seeker tunes only numeric parameters inside that child structure
  -> replay same frozen training contract
  -> Validation / OOS / harsh-case replay
  -> compare child vs parent
  -> ACCEPT / REJECT / REVIEW
  -> only accepted child becomes next generation
```

A future generation repeats the loop from its own new failure evidence.

## 3. Capability is not an indicator

The hierarchy is:

```text
Capability
  -> Skill
      -> Implementation
          -> Parameters
```

Examples:

```text
Capability: RANGE_DEFENSE
  Skill: suppress repeated whipsaw engagement
    Implementation: crossover-density cooldown
      Parameters: density window / threshold / cooldown bars

Capability: PROFIT_PROTECTION
  Skill: reduce MFE giveback
    Implementation: trailing / state-aware exit
      Parameters: activation / distance

Capability: OPENING_OPPORTUNITY
  Skill: recognize early dominant impulse
    Implementation: trading-value acceleration + price impulse
      Parameters: lookback / threshold
```

The system must learn that a capability is missing before selecting the best implementation.  It must not conclude that one named indicator is universally necessary.

## 4. Atomic battle and experience memory

The atomic experience remains `BattleCase`:

```text
case_id
symbol
session_date
market snapshot
knowledge_cutoff
execution settings
BattlefieldContext
metadata
```

The same stock on different dates is a different battle.  Every generation is evaluated on a frozen case set, and complete per-case Backtest evidence remains immutable.

The profile is therefore the experience memory for one generation.  New failure analysis references the parent `run_hash` and `case_set_hash`; it never rewrites the parent.

## 5. Failure analysis

`core/tactical_failure.py` defines the first deterministic failure taxonomy.

Current evidence tags include:

- `LOSS`
- `SEVERE_LOSS`
- `DRAWDOWN`
- `ADVERSE_EXCURSION`
- `WHIPSAW`
- `MFE_GIVEBACK`

`NO_TRADE` is **not a failure by default**.  Abstention may be correct survival behavior.

The analyzer produces:

```text
failure cluster
 -> affected BattleCases
 -> frequency
 -> negative return impact
 -> suggested capability gaps
```

This is intentionally a first-generation taxonomy.  Later characterization may add late-entry, missed-breakout, re-engagement, liquidity, time-of-day and local-leader failure modes when those can be measured causally from available evidence.

## 6. Capability gap and selective acquisition

Each `SkillSpec` declares:

```text
skill_id
capability
implementation
addresses_failure_tags[]
cost
metadata
```

A skill may be tested only if it addresses at least one failure observed in the parent profile under the default promotion contract.

The system does not add all plausible fixes at once.  If the parent shows WHIPSAW failure, candidate children might be:

```text
Parent G0
  + crossover-density cooldown
  + ATR contraction defense
  + minimum JMA separation
  + confirmation delay
```

Each is an independent one-skill child.  This preserves causal attribution of improvement.

## 7. Personal arsenal / CapabilityBudget

A micro warrior has a declared bounded operational budget:

```text
max skills
max complexity units
max indicators
max tunable parameters
max state variables
max decision branches
max setup variants
```

Skill cost is explicit metadata.  The trusted engine does not invent complexity from DSL source length.

A large, fragile implementation that exceeds the declared budget is rejected even if it appears powerful.  The goal is the smallest capability set that solves the broadest set of battles reliably.

## 8. Evolution Arena

`core/tactical_evolution.py` provides the parent-child generation contract.

An upgrade must prove all of the following before automatic acceptance:

1. parent and child use the same frozen `case_set_hash`;
2. context policy is identical;
3. failure evidence came from the parent profile;
4. exactly one new SkillSpec is being evaluated;
5. the skill addresses an observed parent failure;
6. declared capability usage remains within the CapabilityBudget;
7. the child improves at least one material mission/survival axis;
8. no declared survival axis exceeds its allowed regression tolerance.

Primary survival checks include:

- profitable-case rate;
- worst MDD;
- worst case return;
- cost per case;
- winner concentration.

Improvement evidence can include:

- average / median return;
- profitable-case rate;
- worst MDD / worst case;
- lower cost;
- lower MFE giveback;
- lower winner concentration.

There is no opaque universal score.

## 9. ACCEPT / REJECT / REVIEW

```text
ACCEPT
  survival contract satisfied
  AND at least one material improvement
  -> child becomes Generation N+1

REJECT
  survival regression exists
  AND no material compensating improvement
  -> child discarded

REVIEW
  mixed trade-off
  -> parent remains head
  -> child may remain on evidence frontier for explicit mission review
```

A child with higher peak return but materially worse worst-case survival is not automatically promoted.

## 10. Immutable lineage

Every accepted generation records:

```text
family_id
generation_index
candidate_hash
profile_run_hash
case_set_hash
context_policy_hash
acquired_skills[]
capability_usage
parent_generation_hash
acquired_from_failure_hash
generation_hash
```

The trusted Parser, Runtime, Indicator implementation, Backtest accounting, BrokerEmulator and validation assertions are outside the mutation boundary.

Only DSL structure, tactic-family parameters and declared tactic metadata/policy may evolve.

## 11. Local autonomy before macro intelligence

The micro warrior must learn local survival from its own battle evidence:

- attack when local setup quality is high;
- reduce engagement when whipsaw/range evidence rises;
- protect realized edge when giveback is excessive;
- abstain when evidence is insufficient;
- later learn re-engagement when local conditions improve.

Macro intelligence remains a separate battlefield reconnaissance layer.  It may improve deployment selection, but it must not be life support for a tactic that collapses under ordinary hostile local conditions.

## 12. Implementation phases

### E0 — Evolution contracts — implemented in this tranche

- deterministic failure analyzer;
- capability-gap hints;
- `SkillSpec`;
- `CapabilityBudget`;
- immutable `EvolutionGeneration`;
- one-skill `EvolutionArena`;
- conservative survival-gated promotion;
- regression tests.

### E1 — Authoritative BattleCase Provider

Build a Korean regular-session battle universe with explicit source authority and enough warm-up history.  No production dummy fallback.

### E2 — Tactic Family / Skill Registry

Start with compact families such as:

- JMA trend/crossover/resume;
- VWAP reclaim;
- opening-range breakout;
- pullback / re-breakout;
- volatility expansion;
- trading-value confirmation.

For each family define base capability, legal one-skill upgrades and cost metadata.

### E3 — Multi-Battle Parameter Seeker

Optimize numeric parameters over one frozen BattleCase set rather than one stock.  Structure remains fixed during the Seeker phase.

### E4 — Failure Characterizer

Add causal local-state features for:

- time-of-day;
- trend/range transition;
- volatility/liquidity;
- signal density / whipsaw;
- local leader/lagger behavior;
- entry latency;
- MFE capture / giveback;
- re-engagement quality.

### E5 — Structural Skill Generator

LLM proposes bounded one-skill child structures only from the observed capability gap and legal skill registry.  The LLM cannot modify trusted engine code.

### E6 — Validation / Harsh Arena

Replay parent and child across Train / Validation / OOS plus deliberately adverse case slices.  The parent remains the head until the child passes promotion.

### E7 — Evolution Memory / UI

Show the lineage as a game-style skill tree:

```text
G0 Base
  -> WHIPSAW failure
G1 + Range Defense
  -> MFE giveback
G2 + Profit Protection
  -> Late opening entry
G3 + Opening Opportunity
```

Each node must expose why the skill was acquired and the exact parent-vs-child evidence.

### E8 — Macro Context Attribution

Only after independently robust micro generations exist, attach market/sector/high-beta/theme context and measure incremental deployment edge.

## 13. Success criterion

The system succeeds when a tactic family can begin with a minimal base DSL and repeatedly perform:

```text
FIGHT
 -> OBSERVE
 -> FAILURE CLUSTER
 -> CAPABILITY GAP
 -> ONE-SKILL MUTATION
 -> SEEK
 -> REPLAY
 -> OOS / HARSH VALIDATION
 -> ACCEPT / REJECT / REVIEW
 -> REMEMBER
 -> FIGHT AGAIN
```

without source-code surgery and without changing the trusted execution engine.

The target is not invulnerability.  The target is a steadily improving, compact tactical resource whose repeated experience reduces avoidable failure and increases the probability of surviving and achieving its local mission.
