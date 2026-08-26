# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **E4_TRUSTED_FULL_PASS / E5_BOUNDED_STRUCTURAL_SKILL_GENERATOR_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

## Trusted Full checkpoints

### Earlier E0 / initial foundation

```text
ac01525223f897f155de63f02529b0a6429a0882
[PASS] Tactical P1 verification completed: mode=Full.
```

### E1 Korean regular-session BattleCase contract

```text
6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b
[PASS] Tactical P1 verification completed: mode=Full.
```

### E2 JMA family / legal skill tree

The initial E2 failure was classified as **test defect** because a 5m regression used a 1d synthetic fixture. Product timeframe fail-close behavior was preserved.

```text
620f741730b0ae821fc48affd22b5420f38a6cac
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3A causal TacticalObservation sidecar

Future-only market mutation may change full BattleCase provenance but cannot change an earlier observation's causal prefix identity or features.

```text
06b52962a1b9b1212a11202ccef1f27b8d7f40c0
[PASS] Tactical P1 verification completed: mode=Full.
```

### E3 Multi-Battle Parameter Seeker

E3 tunes declared numeric DSL inputs over exactly one frozen BattleCase set. Structure stays fixed; execution settings are not tuned; all candidates remain on the same case/context contract; comparison uses metric leaderboards and Pareto evidence rather than a hidden universal score.

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore E3 is trusted Full-green at the SHA above.

### E4 Causal Failure / Opportunity Characterizer

E4 joins actual entry signal-time causal observations to later realized labels while keeping those domains separately hashed:

```text
causal_dataset_hash
labeled_dataset_hash
```

Changing future labels alone cannot change `causal_dataset_hash`.

The first E4 Full attempt failed at the external Chart SSOT stable-pane contract. Classification: **environment issue**. The local Chart repo was behind its remote `main`; no DSL/E4 source or test was changed to manufacture a pass.

The Chart repo was then fast-forwarded to:

```text
7a43f0f52928045904d192deb7d8d532cb4c533e
Preserve stable pane contract with price markers
```

The exact E4 DSL checkout remained:

```text
560526b7f5af19462a57fd1e5b433bcbe5596500
```

and the operator reran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E4 is trusted Full-green at `560526b7f5af19462a57fd1e5b433bcbe5596500` with verified Chart SSOT dependency `7a43f0f52928045904d192deb7d8d532cb4c533e`.**

## Stability architecture remains authoritative

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
```

Core remains deterministic and narrow. Parent/cascading intelligence remains preserved through Provider -> immutable Context -> future read-only binding. Arbitrary cross-symbol analysis stays in optional Add-ons. Learned/adaptive components remain sidecars and cannot override hard guards/common execution authority without a future explicit contract.

## E5 executable boundary now added

`core/tactical_skill_generator.py` implements the first **Bounded Structural Skill Generator**.

The E5 evidence flow is:

```text
trusted parent EvolutionGeneration
 + exact parent TacticCandidate
 + tactical_failure/v1
 + matching tactical_characterization/v1
 + TacticFamily legal skill tree / CapabilityBudget
        ↓
TacticFamilySpec.legal_skills(...)
        ↓
explicit family renderer
        ↓
one registered skill per child proposal
        ↓
optional E3 numeric search
        ↓
replay
        ↓
EvolutionArena ACCEPT / REJECT / REVIEW
```

E5 itself produces proposals only and never promotes a family head.

### First supported family

```text
JMA_TREND_CROSS_RESUME_V1
```

Explicit renderers correspond exactly to the E2 catalog:

```text
JMA_RANGE_COOLDOWN
JMA_ADX_ENTRY_QUALITY
JMA_CONFIRM_AFTER_RANGE
JMA_FAST_PROFIT_PROTECTION
```

Another family requires a separately implemented and validated renderer.

### Evidence lock

All of the following must match the same parent generation:

```text
family_id
parent candidate_hash
profile_run_hash
case_set_hash
generation_hash
failure_hash attached to characterization
```

Mismatch fails closed.

### Legal-skill boundary

The existing family registry remains authoritative for:

- observed failure relevance;
- already acquired skills;
- prerequisites;
- exclusions;
- CapabilityBudget.

No LLM or E5 code may bypass that authority.

### Structural boundary

The renderer may modify candidate DSL only through explicit registered transforms. Expected assignments and generated names are strict/fail-closed. Parent skill structure is preserved when a dependent skill is added.

Generated parameter inputs are limited to the catalog manifest:

```text
cooldown_bars
adx_length
adx_threshold
confirm_bars
```

`JMA_FAST_PROFIT_PROTECTION` remains parameter-free.

Generated DSL is parsed by the existing parser and regression tests execute generated candidates through the existing Backtest engine.

### No hidden selection or promotion

Output policies:

```text
LEGAL_REGISTERED_SKILLS_ONLY_NO_AUTOMATIC_RANKING
PROPOSAL_ONLY_REQUIRES_REPLAY_AND_EVOLUTION_ARENA
```

E5 does not output a universal `score`, `best`, promotion `decision`, ACCEPT or head mutation.

### Regression coverage

`test_stage1_tactical_skill_generator.py` covers:

- legal registered skills only;
- no automatic ranking/promotion;
- range/ADX structural rendering;
- dependency enforcement for `JMA_CONFIRM_AFTER_RANGE`;
- preservation of already acquired range structure;
- exact E4 characterization/failure identity matching;
- deterministic proposal/candidate/generator hashes;
- execution of generated DSL through `BacktestEngine`.

Detailed implementation checkpoint:

```text
E5_BOUNDED_STRUCTURAL_SKILL_GENERATOR_IMPLEMENTATION.md
```

This E5 boundary has **not yet received trusted Full validation**.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- E4 trusted Full PASS at `560526b7f5af19462a57fd1e5b433bcbe5596500` with Chart SSOT `7a43f0f52928045904d192deb7d8d532cb4c533e`;
- E5 source/tests are implemented awaiting Full;
- Core DSL Freeze / sidecar/provider/Add-on boundaries remain authoritative.

Do not claim yet:

- trusted Full PASS for E5;
- a strongest/profitable generated child;
- automatic structural skill selection or promotion;
- completed Train/Validation/OOS/harsh arena;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Immediate boundary

Do not begin E6 executable work before E5 is trusted green.

Run:

```powershell
git pull --ff-only origin main
git rev-parse HEAD
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

If it fails, classify the first executable failure as exactly one of:

```text
test defect
product defect
authority drift
environment issue
unknown
```

before editing.
