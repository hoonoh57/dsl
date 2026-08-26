# E4 Causal Failure / Opportunity Characterizer — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Purpose

E4 is the first deterministic descriptive layer after the trusted Multi-Battle Parameter Seeker.

It does not learn a policy, change DSL structure or create a skill. Its job is narrower:

> Join what the tactic could causally know at an actual entry signal with what happened afterward, while keeping those two domains physically separate.

The execution flow is:

```text
trusted tactical_discovery profile
 + exact frozen BattleCases
 + actual closed-trade signal_time
        ↓
causal TacticalObservation at signal_time
        ↓
compact causal feature subset
        │
        ├────────────── future boundary ──────────────┐
        ↓                                             ↓
causal_features                               realized outcome label
                                              return / MFE / MAE
                                              giveback / exit / holding
        └──────────────────┬──────────────────────────┘
                           ↓
              deterministic descriptive strata
                           ↓
              repeated failure/opportunity evidence
```

## 2. Executable files

```text
core/tactical_characterization.py
test_stage1_tactical_characterization.py
```

No Parser, Semantic, Runtime, Backtest or Broker file is modified by E4.

## 3. Causal/outcome separation

Every trade characterization record has two distinct payloads:

```text
causal_features
future_outcome
```

`causal_features` is built by `JmaLocalObservationBuilder` using the trade's actual `signal_time`. The observation therefore sees only the market prefix ending at that signal timestamp.

`future_outcome` is attached afterward and may include:

```text
return_pct
mfe_pct
mae_pct
giveback_pct
holding_bars
exit_reason
exit_time
```

These outcome values are labels/evidence only. They are not observation inputs.

The implementation exposes two separate identities:

```text
causal_dataset_hash
labeled_dataset_hash
```

Changing only a future trade label must not change `causal_dataset_hash`.

## 4. Compact first-generation characterization axes

The first tranche deliberately avoids feeding the full raw observation into a learner.

Default causal axes are:

```text
minutes_from_open
jma_spread_atr
sma60_slope_pct
price_to_sma60_atr
atr_pct
volume_ratio
higher_high_ratio
higher_low_ratio
```

They cover:

- time position;
- JMA trend/range geometry;
- broader trend direction;
- price overextension;
- volatility;
- volume/liquidity proxy;
- primitive rising-price structure.

This list is descriptive research policy, not a live engagement rule.

## 5. Descriptive strata, not a universal score

For each declared causal feature, E4 creates deterministic value-only quantile cutpoints and reports per-bin evidence such as:

```text
support
profitable_rate
average_return_pct
average_mfe_pct
average_mae_pct
average_giveback_pct
outcome_tag_counts
```

Outcome labels do not determine the bin boundaries; only causal feature values do.

There is no scalar tactic score and no automatic promotion.

The output declares:

```text
selection_policy = DESCRIPTIVE_NO_HIDDEN_UNIVERSAL_SCORE
```

## 6. Failure evidence integration

E4 also carries the existing `TacticalFailureAnalyzer` case-level evidence alongside trade-level characterization.

This preserves the already-trusted distinctions including:

```text
LOSS
SEVERE_LOSS
DRAWDOWN
ADVERSE_EXCURSION
WHIPSAW
MFE_GIVEBACK
UNRESOLVED_POSITION
```

`NO_TRADE` remains abstention by default. A case with no closed trade is not silently converted into a failure by the characterizer.

## 7. Exact evidence identity

The supplied BattleCases must match the profile's `case_id` and `case_hash` exactly.

Any mismatch fails closed before characterization. E4 does not reconstruct or guess a BattleCase from profile metadata.

Trade evidence uses the Backtest-authoritative closed-trade fields, including:

```text
signal_time
entry_time
entry/exit evidence
MFE / MAE
realized return
```

The characterizer does not change those values.

## 8. Regression contract

`test_stage1_tactical_characterization.py` covers:

1. causal features and future outcome labels are separate;
2. future return/MFE mutation cannot change `causal_dataset_hash`;
3. the same mutation does change `labeled_dataset_hash` and characterization identity;
4. profile/BattleCase identity mismatch fails closed;
5. repeated evaluation of the same evidence produces identical hashes and strata;
6. no hidden `score` output is introduced.

The existing Full verifier discovers this regression through the `test_stage1_*.py` pattern.

## 9. Explicit non-goals

E4 does **not** implement:

- TacticalMemory;
- a LocalBattlefieldLearner;
- automatic ENTER/WAIT/ABSTAIN policy;
- automatic feature threshold promotion into a hard guard;
- automatic SkillSpec creation;
- adaptive timeframe selection;
- parent-context `ctx.*` binding;
- multi-symbol deployment selection;
- profitability/generalization claims.

A descriptive pattern must later survive explicit causal validation before it can influence a tactic or deployment rule.

## 10. Next validation boundary

The E4 executable tranche must receive trusted Full validation before E5 executable work begins.

Required operator boundary:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If Full fails, classify the first executable failure as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before changing code.
