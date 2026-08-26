# E3 Multi-Battle Parameter Seeker Implementation

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-26 KST**

## 1. Authority

This tranche implements E3 from `EVOLVING_MICRO_WARRIOR_PLAN.md`:

> Optimize numeric parameters over one frozen BattleCase set while tactic structure remains fixed.

It does not change Parser, Runtime, indicator semantics, Backtest accounting or BrokerEmulator.

## 2. Trusted prerequisite

E3 begins only after the E3A sidecar boundary was Full-validated by the operator at exact checkout:

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

This makes `06b52962...` the trusted E3A executable checkpoint.

## 3. Implementation

`core/tactical_parameter_seeker.py` adds `MultiBattleParameterSeeker`.

The seeker:

```text
base TacticCandidate
 + declared numeric DSL input space
 + one frozen BattleCase set
        ↓
deterministic grid/random candidate plan
        ↓
change DSL input values only
        ↓
TacticalDiscoveryEngine.evaluate(candidate, same cases)
        ↓
immutable multi-BattleCase profile per candidate
        ↓
TacticalCompetitionEngine.compare(profiles)
        ↓
metric leaderboards + Pareto frontier
```

## 4. Frozen structure / frozen battle contract

E3 v1 deliberately permits only `ParameterSpec(target="dsl")`.

Execution-setting parameters are rejected because changing execution settings would change the frozen BattleCase identity/comparison contract.

DSL parameter replacement uses the existing validated `apply_dsl_parameters()` path, which may replace declared numeric `input` assignments only. E3 does not edit arbitrary expressions or tactic structure.

Every parameter candidate is evaluated against the exact same immutable `BattleCase` tuple. The seeker verifies that every resulting profile retains the same:

```text
case_set_hash
context_policy
```

## 5. Search determinism

Supported methods:

```text
grid
random
```

Grid enumeration is deterministic and fails closed when the declared space exceeds `max_candidates`.

Random search uses an explicit seed and bounded unique combinations. Same inputs, seed, cases and worker-independent tactical profiles produce the same `seek_hash`.

Parallelism is only inside the existing per-candidate `TacticalDiscoveryEngine` BattleCase evaluation. Changing `max_workers` must not change candidate identities, profile run hashes, competition evidence or seek identity.

## 6. No hidden universal score

E3 does **not** reuse the single-symbol Stage 1 seeker's `MAX_RETURN`, `RETURN_DRAWDOWN` or `ROBUST_SCORE` scalar ranking as micro-warrior promotion authority.

Instead it delegates candidate comparison to `TacticalCompetitionEngine`, preserving:

```text
average-return leaderboard
median-return leaderboard
profitable-case-rate leaderboard
worst-MDD leaderboard
profit-factor evidence
cost-per-case evidence
trade-count evidence
complexity evidence
Pareto frontier
```

Output authority is explicitly:

```text
PARETO_NO_HIDDEN_UNIVERSAL_SCORE
```

The seeker does not automatically promote a parameter set or family head.

## 7. Evidence identity

Each parameterized child receives deterministic identity based on:

```text
base candidate hash
parameter values
parameter hash
resulting DSL
unchanged complexity units
```

The search result records:

```text
schema = tactical_parameter_seek/v1
base candidate identity
case_set_hash
context policy
method / seed
parameter space
evaluated candidates
profile run hashes
full tactical profiles
Pareto parameter sets
metric leaderboards
competition evidence
seek_hash
```

## 8. Regression contracts

`test_stage1_tactical_parameter_seeker.py` verifies:

1. grid candidates all retain one frozen `case_set_hash`;
2. comparison uses Pareto/metric evidence and exposes no `best_score`;
3. worker count cannot change seek/competition identity;
4. same random seed produces the same candidate plan and seek identity;
5. execution-setting parameter tuning is rejected in E3 v1.

The test filename is inside the existing `test_stage1_*.py` verifier discovery boundary.

## 9. Nonclaims

Do not claim yet:

- trusted Full PASS for E3;
- that a profitable or strongest parameter set has been found;
- automatic parameter promotion;
- Train/Validation/OOS generalization;
- live-trading readiness;
- parent-context or multi-symbol deployment readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## 10. Next validation boundary

Pull exact current `main` and run:

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

Only after E3 is trusted green should the next executable tranche begin.
