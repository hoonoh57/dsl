# Adaptive Micro-Warrior Learning Architecture

Status: **OPTIONAL ADAPTIVE SIDECAR RESEARCH ADDENDUM / 2026-08-26 KST**

This document preserves future adaptive-learning possibilities. It is subordinate to `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md` and does **not** define the main implementation critical path.

## 1. Scope

Adaptive research may eventually help a tactic family decide whether a local battlefield resembles situations in which it historically survives and succeeds.

Possible future loop:

```text
TACTIC OPPORTUNITY
 -> CAUSAL LOCAL OBSERVATION
 -> OPTIONAL TACTICAL MEMORY
 -> OPTIONAL SURVIVAL / OPPORTUNITY ESTIMATE
 -> ENTER / WAIT / ABSTAIN OR VALIDATED MODE SELECTION
 -> EVIDENCE
```

None of these steps may rewrite the DSL parser/runtime, bypass hard equipment/safety guards, change Broker accounting or read future data.

## 2. Core DSL is not the learner

The Instrument DSL remains the deterministic tactical-language SSOT.

One DSL candidate has:

- one declared base timeframe;
- registered causal indicator/state capabilities;
- explicit signal logic;
- explicit order intent;
- reproducible Backtest/Broker semantics.

The DSL does not dynamically train models, call arbitrary ML/RL code, mutate itself, request arbitrary lower-timeframe/tick streams, or change its own declared timeframe while running.

Adaptive intelligence, if later implemented, lives outside Core DSL.

## 3. Hard equipment first

A warrior should prefer verified deterministic equipment for known operational boundaries.

Example:

```text
JMS2 range detector
 -> slope below declared absolute threshold
 -> RANGE_GUARD = BLOCK
 -> learner is not consulted
```

The authority order is:

```text
valid source/data
AND hard safety/equipment guards
AND tactic trigger
AND optional learned admissibility
AND common execution policy
```

A learned probability or score can never override a hard BLOCK.

## 4. Causal TacticalObservation seam

`core/tactical_observation.py` may expose immutable point-in-time evidence for research without changing the DSL language.

Possible features include:

### Signal geometry

```text
jma_fast / jma_slow
jma_spread
jma_fast_slope
jma_slow_slope
jma_spread_velocity
jma_fast_acceleration
bars_since_cross
```

### Structural price action

```text
higher_high_ratio
higher_low_ratio
lower_high_ratio
lower_low_ratio
swing_high_slope
swing_low_slope
range expansion/compression
body-direction persistence
close location
wick asymmetry
breakout distance
```

These primitive measurements are preferable to hard-coding every named chart pattern into the language.

### Slow trend / location

```text
sma60_slope
price_to_sma60_pct
price_to_sma60_atr
return_from_open
recent returns
session-high/session-low distance
```

### Volatility / execution risk

```text
atr_pct
range ratio
volume ratio
bar gap proxy
later authoritative slippage/VI evidence
```

### Time state

```text
minutes_from_open
minutes_to_close
session_progress_ratio
```

Every observation must use only information available at or before its timestamp.

## 5. Optional TacticalMemory / learner

TacticalMemory and a LocalBattlefieldLearner are deferred research ideas, not current mainline requirements.

If later justified, memory should be immutable/versioned and models should estimate separate interpretable axes such as:

```text
P(profitable)
P(severe_loss)
expected_MFE
expected_MAE
expected_cost/slippage
uncertainty
support
```

A learner should not collapse all evidence into an unexplained universal score, and it should expose the exact model/memory identity behind a decision.

## 6. Relative historical context

If adaptive learning resumes later, current values may be compared with Train-only historical distributions:

```text
current / trailing mean
same-time-of-day distribution
training z-score / percentile
change from previous signal
change from previous local phase
```

Normalizers must be fitted on Train and frozen for Validation/OOS.

## 7. Adaptive resolution remains orchestration

A family may someday own separately validated modes such as:

```text
JMA_TCR_5M
JMA_TCR_3M
JMA_TCR_1M
```

An external tactical orchestrator may choose among those modes. A running DSL does not mutate its own `timeframe`.

Tick mode remains future-only until authoritative tick data, deterministic aggregation, cutoff alignment, warm-up and Broker semantics exist.

## 8. Training discipline if this research resumes

Adaptive research must preserve chronological causality:

```text
TRAIN -> fit
VALIDATION -> freeze
OOS -> no future refit
HARSH -> adverse slices
```

Every walk-forward refit needs an explicit cutoff and immutable artifact identity. Future observations never change earlier decisions.

## 9. Relationship to mainline development

This sidecar is intentionally **non-blocking**.

The current mainline remains:

```text
E3 Multi-Battle Parameter Seeker
E4 Causal Failure / Opportunity Characterizer
E5 Bounded Structural Skill Generator
E6 Train / Validation / OOS / Harsh Evolution Arena
E7 Evolution Evidence UI
E8 Macro Context Attribution / Deployment
```

`TacticalObservation` may remain available as evidence for E4 or later research. TacticalMemory, LocalBattlefieldLearner and adaptive resolution selection should not be implemented merely because they are possible.

They should resume only when mainline evidence shows a concrete need that cannot be solved more simply with deterministic equipment, existing DSL primitives or tactical infrastructure.

## 10. Promotion rule

No adaptive feature enters Core DSL merely because it works experimentally.

Promotion is governed exclusively by `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`.

The design target is:

```text
Core DSL: stable, deterministic, boring, trustworthy.
Adaptive sidecar: optional, replaceable, experimental.
```
