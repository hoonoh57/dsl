# E5 Bounded Structural Skill Generator — Implementation Checkpoint

Status: **IMPLEMENTED / AWAITING TRUSTED FULL VALIDATION / 2026-08-27 KST**

## 1. Trusted predecessor

E4 Causal Failure / Opportunity Characterizer was operator-validated at exact DSL checkout:

```text
560526b7f5af19462a57fd1e5b433bcbe5596500
```

with Chart SSOT checkout:

```text
7a43f0f52928045904d192deb7d8d532cb4c533e
```

and:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

The first E4 Full attempt failed in the external Chart SSOT stable-pane contract. It was classified as **environment issue** because the local `cascading-feature-solution` checkout was behind its remote `main`; no DSL/E4 product or test assertion was weakened. After fast-forwarding the Chart repo to the exact SHA above, the same E4 DSL SHA passed Full.

Therefore E4 is trusted Full-green at `560526b7f5af19462a57fd1e5b433bcbe5596500` under the verified Chart dependency above.

## 2. E5 objective

E5 must turn observed capability gaps into bounded one-skill child structures without allowing a model or orchestration layer to rewrite the trusted engine or invent arbitrary DSL capabilities.

The executable seam is:

```text
trusted parent EvolutionGeneration
 + exact parent TacticCandidate
 + tactical_failure/v1 report
 + matching tactical_characterization/v1 evidence
 + TacticFamily legal skill tree / CapabilityBudget
        ↓
legal registered skill set
        ↓
explicit family renderer
        ↓
one-skill child proposal(s)
        ↓
E3 numeric Parameter Seeker when parameters exist
        ↓
TacticalDiscovery replay
        ↓
EvolutionArena ACCEPT / REJECT / REVIEW
```

E5 itself never promotes a family head.

## 3. New executable

`core/tactical_skill_generator.py`

Schema:

```text
tactical_skill_generator/v1
```

The first renderer supports only the currently registered family:

```text
JMA_TREND_CROSS_RESUME_V1
```

Unsupported families fail closed until an explicit renderer is introduced and validated in a separate tranche.

## 4. Evidence lock

`BoundedStructuralSkillGenerator` requires all inputs to describe the same parent generation:

```text
parent_generation.family_id == family.family_id
parent_generation.candidate_hash == parent_candidate.candidate_hash
failure_report.profile_run_hash == parent_generation.profile_run_hash
failure_report.case_set_hash == parent_generation.case_set_hash
characterization.profile_run_hash == parent_generation.profile_run_hash
characterization.case_set_hash == parent_generation.case_set_hash
characterization.family_id == family.family_id
characterization.generation_hash == parent_generation.generation_hash
characterization.case_failure_analysis.failure_hash == failure_report.failure_hash
```

Any mismatch fails closed.

This prevents a skill proposal from being justified by evidence from another candidate, generation or BattleCase universe.

## 5. Legal skill authority

The generator does not create its own capability list. It calls the existing `TacticFamilySpec.legal_skills(...)` authority, which already enforces:

- observed failure relevance;
- not already acquired;
- `requires_skills` prerequisites;
- `excludes_skills` constraints;
- `CapabilityBudget` limits.

The generator may produce all currently legal children in stable catalog order or one explicitly requested legal skill.

There is no automatic ranking or universal skill score.

Output policy:

```text
LEGAL_REGISTERED_SKILLS_ONLY_NO_AUTOMATIC_RANKING
```

## 6. Explicit JMA structural renderers

The first E5 tranche has four explicit transformations corresponding exactly to the E2 catalog.

### JMA_RANGE_COOLDOWN

Adds:

```dsl
input cooldown_bars = 10
cooldown_ok = ta.bars_since(ta.crossunder(fast, slow)) > cooldown_bars
```

and appends `cooldown_ok` to the existing `long_entry` expression.

Declared parameter manifest remains bounded by the catalog:

```text
cooldown_bars: int, 1..30, default 10
```

### JMA_ADX_ENTRY_QUALITY

Adds:

```dsl
input adx_length = 14
input adx_threshold = 20
entry_strength = ta.adx(adx_length)
```

and appends `entry_strength > adx_threshold` to the existing `long_entry` expression.

Declared bounds:

```text
adx_length: int, 5..40, default 14
adx_threshold: number, 10..40, default 20
```

### JMA_CONFIRM_AFTER_RANGE

This skill remains illegal until `JMA_RANGE_COOLDOWN` is already acquired.

Adds:

```dsl
input confirm_bars = 2
range_confirmed = state.persist(fast > slow and close > fast, confirm_bars)
```

and appends `range_confirmed` to the existing `long_entry`, preserving the already-installed range cooldown structure.

Declared bounds:

```text
confirm_bars: int, 2..8, default 2
```

### JMA_FAST_PROFIT_PROTECTION

Parameter-free structural mutation:

```text
existing long_exit
OR close < fast
```

No synthetic parameter is created merely to force an E3 search.

## 7. Source-mutation boundary

E5 may mutate only the candidate DSL string and proposal metadata.

It may not modify:

```text
Parser
Semantic
Runtime
Indicator implementations
Backtest accounting
BrokerEmulator
BattleCase evidence
family skill registry
CapabilityBudget
failure/characterization evidence
```

The renderer uses strict assignment matching and fails if expected parent structure is absent/ambiguous or if a generated variable name already exists.

Generated DSL is parsed through the existing `DSLParser`; regression tests also execute generated candidates through `BacktestEngine` so E5 cannot depend on hidden renderer-only syntax.

## 8. Parameter Seeker handoff

E5 does not choose numeric values beyond the catalog default required to materialize a valid child structure.

Each proposal exposes a `parameter_manifest` with only declared DSL parameters. A subsequent E3 search may choose an explicit bounded candidate grid inside those ranges.

```text
E5 chooses structure
E3 tunes declared numbers
```

For parameter-free skills, the child proceeds directly to replay.

## 9. Proposal-only evidence

Each proposal records:

```text
parent candidate/generation identity
failure_hash
characterization_hash
skill_id
capability
relevant failure tags
projected CapabilityBudget usage
parameter manifest
child candidate/hash
proposal_hash
```

Top-level output records a deterministic `generator_hash`.

The promotion policy is explicitly:

```text
PROPOSAL_ONLY_REQUIRES_REPLAY_AND_EVOLUTION_ARENA
```

No `best`, `score`, `decision`, ACCEPT or family-head mutation is produced by E5.

## 10. Regression coverage

`test_stage1_tactical_skill_generator.py` verifies:

- only currently legal registered skills are proposed;
- no automatic ranking/score/promotion output exists;
- range-defense rendering preserves parent structure and exposes only the catalog numeric input;
- generated DSL reaches the trusted Backtest path;
- dependency skill `JMA_CONFIRM_AFTER_RANGE` is illegal before range cooldown and legal afterward;
- applying a dependency skill preserves previously acquired structure;
- mismatched E4 characterization fails closed;
- generator/proposal/candidate identity is deterministic.

The existing Full verifier runs `test_stage1_*.py`, so this regression joins the normal Tactical P1 Full boundary automatically.

## 11. Nonclaims

This tranche does **not** establish:

- that any proposed child is better than its parent;
- a winning parameter set;
- automatic skill choice;
- automatic promotion;
- LLM autonomy over DSL source;
- Train/Validation/OOS/harsh generalization;
- profitability or live readiness.

## 12. Next boundary

Do not start E6 until this E5 executable boundary receives trusted Full validation at an exact repository SHA.
