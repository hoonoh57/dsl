# Adaptive Micro-Warrior Learning Architecture

Status: **AUTHORITATIVE MICRO-LEARNING ADDENDUM / 2026-08-26 KST**

This addendum extends the evolving micro-warrior doctrine without weakening the trusted DSL/runtime/backtest/broker boundaries.

## 1. Objective

A micro warrior must do more than emit a signal. It must learn whether the current local battlefield resembles environments in which it historically survives and succeeds, and it must be able to choose among pre-validated tactical modes without requiring macro market-regime assistance.

Target loop:

```text
TACTIC OPPORTUNITY
 -> CAUSAL LOCAL OBSERVATION
 -> TACTICAL MEMORY
 -> SURVIVAL / OPPORTUNITY / UNCERTAINTY ESTIMATE
 -> RESOLUTION + EXECUTION MODE SELECTION
 -> ENTER / WAIT / ABSTAIN
 -> ACTUAL + SHADOW EVIDENCE
 -> NEXT TRAINING MEMORY VERSION
```

The warrior never rewrites the trusted engine and never reads future data.

## 2. Responsibility boundaries

### Instrument DSL

The DSL remains the tactical-language SSOT. One DSL candidate describes one concrete tactic implementation at one declared base timeframe and uses only supported causal capabilities.

The DSL does not dynamically rewrite its own timeframe, request arbitrary lower-timeframe/tick data, call external ML code, or mutate itself during a backtest.

### Adaptive learning layer

The adaptive layer lives above DSL execution and below future macro command. It observes point-in-time local evidence, evaluates learned suitability and chooses only among explicitly declared, independently validated tactic-family modes.

### Execution/accounting

`BacktestEngine` and `BrokerEmulator` remain the sole fill/accounting authority. Learning cannot bypass common entry gates, slippage, costs, position rules or execution policy.

## 3. Causal TacticalObservation

Every candidate engagement point may produce an immutable observation:

```text
case_id
symbol
session_date
timestamp
knowledge_cutoff
family_id
generation_hash
resolution_mode
feature_schema_version
features
observation_hash
```

Every feature must be computable from information known at or before the observation timestamp and knowledge cutoff.

### Signal geometry

For JMA-family tactics, examples include:

```text
jma_fast
jma_slow
jma_spread
jma_fast_slope
jma_slow_slope
jma_spread_velocity
jma_fast_acceleration
bars_since_cross
cross_strength
```

Absolute-price features should normally be normalized by price, ATR, range or a training-window distribution.

### Structural price action

The learner should receive primitive geometry rather than depend only on hard-coded named patterns:

```text
higher_high_ratio
higher_low_ratio
lower_high_ratio
lower_low_ratio
swing_high_slope
swing_low_slope
range_compression_ratio
range_expansion_ratio
body_direction_persistence
close_location_in_range
wick_asymmetry
breakout_distance
pullback_depth
recovery_strength
```

This allows later models to learn structures corresponding to triangle contraction, rising consolidation, trend stair-steps, pullback/re-breakout and other recurring patterns. Named pattern labels may be added later for explainability, but are not the primary authority.

### Slow trend / location

Examples:

```text
sma60_slope
sma60_acceleration
price_to_sma60_pct
price_to_sma60_atr
bars_above_sma60
bars_since_sma60_reclaim
session_high_distance
session_low_distance
return_from_open
recent_return_3bar
recent_return_6bar
recent_return_12bar
overextension_percentile
```

### Volatility / liquidity / execution risk

Examples:

```text
atr_pct
realized_range_pct
range_percentile
volume_ratio
volume_acceleration
trading_value_ratio
spread_proxy
bar_gap_proxy
signal_to_expected_fill_move
recent_slippage_proxy
```

The learner must explicitly model whether the current resolution is too coarse for local volatility and execution latency.

### Time state

Time is a first-class local battlefield feature rather than a hard-coded session filter:

```text
minutes_from_open
minutes_to_close
session_progress_ratio
bars_since_signal
bars_since_last_entry
bars_since_last_exit
bars_since_last_loss
```

The learner may discover that a symbol/family performs better in particular session phases, but deployment requires support/confidence and OOS validation rather than a hand-written time rule.

### Event state

Where authoritative event data exists, causal features may include:

```text
vi_active
bars_since_vi_release
return_before_vi
range_after_vi
volume_after_vi
post_vi_structure_stability
```

Only events already known by the observation timestamp may be used.

### Tactical self-state

Only realized history before the observation is legal:

```text
prior_closed_trade_return
recent_closed_trade_return_mean
recent_profit_factor
realized_equity_drawdown
consecutive_losses
consecutive_wins
entries_today
cooldown_state
```

The completed full-backtest equity curve is never an input to earlier decisions.

## 4. Relative context

The warrior should learn current conditions relative to its own symbol/history:

```text
current / trailing mean
current / same-time-of-day training history
training-window z-score
training-window percentile
change from previous signal
change from previous local phase
change from previous price-rise episode
```

Historical normalizers are fitted on Train only and frozen for Validation/OOS.

## 5. TacticalExperience and shadow evidence

Record every candidate opportunity, not only executed trades:

```text
TacticalExperience
  observation
  tactic_trigger
  decision = ENTER | WAIT | ABSTAIN
  chosen_resolution_mode
  actual_execution_evidence
  realized_outcome
  optional_shadow_outcome
```

Executed outcomes retain return, MFE, MAE, giveback, cost, slippage and holding-time evidence.

For research, abstained opportunities may be counterfactually replayed under the exact frozen execution contract. Shadow outcomes remain separate from actual realized PnL. This reduces selection bias and lets the system test whether abstention was beneficial.

## 6. TacticalMemory

Memory is immutable and versioned per training checkpoint. Recommended hierarchy:

```text
family prior
 -> symbol adaptation
    -> recent-memory adaptation
```

Memory records at least long-term estimate, recent estimate, support count, confidence, training cutoff and memory hash. Recent drift can reduce confidence or change deployment preference, but online adaptation must be explicitly defined and validated.

## 7. LocalBattlefieldLearner

The first learner should be conservative and interpretable rather than immediately using opaque reinforcement learning.

For each observation and eligible mode estimate separate axes:

```text
P(profitable)
P(severe_loss)
expected_return
expected_MFE
expected_MAE
expected_giveback
expected_cost
expected_slippage
uncertainty
support
```

Do not require one opaque universal score. A declared `LocalEngagementPolicy` converts evidence into `ENTER`, `WAIT` or `ABSTAIN` with reasons and exact model/memory identity.

## 8. Adaptive resolution / timeframe

Adaptive timeframe is a tactic-family mode-selection problem, not in-place DSL mutation.

A family may eventually declare bounded modes such as:

```text
JMA_TCR_5M
JMA_TCR_3M
JMA_TCR_1M
JMA_TCR_TICK_N
```

Each mode requires explicit source/aggregation authority, DSL candidate or validated equivalent structure, execution settings, warm-up, capability cost and independent validation evidence.

Current Stage 1 DSL has one declared base timeframe. Its MTF capability reads completed higher-timeframe data only. It does not support arbitrary dynamic lower-timeframe or tick switching. Therefore lower-resolution adaptation belongs to orchestration/data/evidence contracts until a future DSL capability is explicitly designed and verified.

At an observation timestamp the learner may compare mode-specific survival/opportunity/slippage/uncertainty estimates and select one already-validated mode. Faster resolution is not automatically better; noise, whipsaw, cost and complexity must remain visible.

Tick mode is future-only until authoritative tick data, deterministic aggregation, knowledge-cutoff alignment, warm-up and Broker execution semantics exist. Minute bars must never be silently relabeled as tick evidence.

## 9. Training and validation discipline

Learning must preserve chronological causality:

```text
TRAIN
  fit normalizers / memory / model
VALIDATION
  freeze fitted artifacts
OOS
  no refit from future evidence
HARSH
  test adverse volatility, time, slippage, VI/event and overextension slices
```

If walk-forward adaptation is enabled, every refit has an explicit cutoff and new immutable model/memory hash. Future observations never change an earlier decision.

## 10. Revised evolution phases

After E2 is trusted green, micro-learning proceeds as:

```text
E3A Causal TacticalObservation
E3B TacticalExperience / TacticalMemory
E3C LocalBattlefieldLearner + LocalEngagementPolicy
E3D Multi-Battle Parameter Seeker
E4  Failure / Opportunity Characterizer
E5  Structural Skill Generator
E6  Train / Validation / OOS / Harsh Arena
E7  Evolution Memory / Evidence UI
E8  Macro Context Attribution / Deployment
```

This ordering supersedes only the sequencing detail of the earlier E3/E4 plan. It does not weaken one-skill evolution, frozen BattleCase comparison, capability budgets or macro separation.

## 11. Success criterion

A mature micro warrior should be able to say, from its own causal experience:

```text
A tactic trigger exists,
but this local battlefield is historically hostile -> ABSTAIN.

A tactic trigger exists,
this symbol/time/structure resembles high-survival experience -> ENGAGE.

The 5m mode is too coarse under current volatility/slippage evidence,
and a separately validated 3m mode has better survival evidence -> choose 3m.
```

Macro regime intelligence may later improve these decisions, but the local warrior must first learn to choose favorable battles without macro life support.
