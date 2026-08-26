# Quant DSL Progress Checkpoint — through 2026-08-27 KST

Status: **E6_TRUSTED_FULL_PASS / E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTED_AWAITING_TRUSTED_FULL / CORE_DSL_FREEZE_ACTIVE**

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

E3 tunes declared numeric DSL inputs over exactly one frozen BattleCase set. Structure stays fixed; execution settings are not tuned; comparison uses metric leaderboards and Pareto evidence rather than a hidden universal score.

```text
cc3096c28ea8b9af718a1784df1b17af62bcde9a
[PASS] Tactical P1 verification completed: mode=Full.
```

### E4 Causal Failure / Opportunity Characterizer

E4 separates signal-time causal observations from later realized labels through distinct `causal_dataset_hash` and `labeled_dataset_hash` identities.

The first E4 Full attempt failed at the external Chart SSOT stable-pane contract. Classification: **environment issue**. The local Chart repo was behind remote `main`; no E4 product source or assertion was weakened.

Verified dependency/checkpoint pair:

```text
DSL:
560526b7f5af19462a57fd1e5b433bcbe5596500

Chart SSOT:
7a43f0f52928045904d192deb7d8d532cb4c533e

[PASS] Tactical P1 verification completed: mode=Full.
```

### E5 Bounded Structural Skill Generator

E5 materializes only legal registered one-skill child structures through explicit family renderers and never ranks or promotes children itself.

```text
c1351152d58e4219b9998f0b35b7636f340dc986
[PASS] Tactical P1 verification completed: mode=Full.
```

### E6 Validation / Harsh Arena

E6 replays one fixed parent/child pair across explicit TRAIN / VALIDATION / OOS / HARSH partitions. TRAIN uses the existing EvolutionArena; holdouts use explicit axis-by-axis tolerances. Default `engagement_collapse` blocks a child from appearing robust solely by abandoning every holdout battle when the parent was active.

The operator synchronized `main`, confirmed exact checkout:

```text
ad87a68a1f8d0595f51a3c02bde022a63ea22cc6
```

and ran:

```text
[PASS] Tactical P1 verification completed: mode=Full.
```

Therefore **E6 is trusted Full-green at `ad87a68a1f8d0595f51a3c02bde022a63ea22cc6`.**

Detailed checkpoint:

```text
E6_VALIDATION_HARSH_ARENA_IMPLEMENTATION.md
```

## Stability architecture remains authoritative

```text
CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md
PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
MULTI_SYMBOL_ADDON_EXTENSION_POLICY.md
```

Core remains deterministic and narrow. Parent/cascading intelligence remains preserved through Provider -> immutable Context -> future read-only binding. Arbitrary cross-symbol analysis stays in optional Add-ons. Learned/adaptive components remain sidecars and cannot bypass hard guards/common execution authority.

## E7 executable/UI boundary now added

E7 turns the append-only evolution ledger into an inspectable lineage without adding a second promotion authority.

New core layer:

```text
core/tactical_evolution_lineage.py
```

Projection schema:

```text
tactical_evolution_lineage/v1
```

### Memory sources

Existing `TacticalEvolutionStore` remains authoritative for:

```text
profiles
failures
generations
Train evolution decisions
explicit family head
```

E7 additionally stores E6 `tactical_validation_arena/v1` evidence append-only by `arena_hash`.

Validation evidence requires:

```text
matching family
existing parent generation
ACCEPT / REJECT / REVIEW
promotion_eligible exactly matches ACCEPT
accepted_generation only for ACCEPT
accepted generation parent/child identity matches E6 evidence
```

Recording E6 evidence never calls `promote()`.

### Accepted lineage projection

Each accepted generation exposes:

```text
generation/candidate/profile identity
parent generation
acquired skills
exactly one new skill
capability usage
explicit head flag
compact profile metrics
failure reason tags
Train decision evidence
E6 Validation/OOS/HARSH evidence
```

Projection validates one-skill lineage again at read time. G0 must have no parent/skill, later acquired-skill lists must preserve the parent prefix and add exactly one skill, and stored generation/profile candidate identities must match.

Malformed append-only evidence fails closed rather than being rendered as a valid skill tree.

### Attempts remain separate

Rejected/reviewed attempts are shown independently from accepted generation nodes. This preserves the distinctions among:

```text
Train ACCEPT/REJECT/REVIEW
E6 final validation result
promotion_eligible
accepted generation record
explicit family head
```

There is no universal lineage score.

### Read-only API/UI

`tactical_main.py` adds:

```text
GET /api/stage1/tactical/evolution/{family_id}
```

No evolution promotion write endpoint was added.

`core/templates/tactical.html` and `core/static/tactical.js` add an Evolution Skill Tree / Evidence panel showing:

```text
explicit head
lineage hash
accepted generations
new skill
failure tags
Train / Validation / OOS / HARSH status
compact return/MDD evidence
attempts and holdout failures
whether an attempt became an accepted generation
```

The browser has no `/promote` action. E7 does not change Chart SSOT source or chart-document semantics.

### Regression coverage

New tests:

```text
test_stage1_tactical_evolution_lineage.py
test_stage1_tactical_evolution_ui.py
```

They cover append-only validation evidence, one-skill lineage integrity, explicit-head semantics, deterministic lineage hashes, GET-only UI/API behavior, and absence of automatic promotion controls.

Detailed checkpoint:

```text
E7_EVOLUTION_MEMORY_EVIDENCE_UI_IMPLEMENTATION.md
```

This E7 boundary has **not yet received trusted Full validation**.

## Current validation status

May claim:

- E1 trusted Full PASS at `6e9b2f357080eff904ddd2d5d369c0a9a2d3b14b`;
- E2 trusted Full PASS at `620f741730b0ae821fc48affd22b5420f38a6cac`;
- E3A trusted Full PASS at `06b52962a1b9b1212a11202ccef1f27b8d7f40c0`;
- E3 trusted Full PASS at `cc3096c28ea8b9af718a1784df1b17af62bcde9a`;
- E4 trusted Full PASS at `560526b7f5af19462a57fd1e5b433bcbe5596500` with Chart SSOT `7a43f0f52928045904d192deb7d8d532cb4c533e`;
- E5 trusted Full PASS at `c1351152d58e4219b9998f0b35b7636f340dc986`;
- E6 trusted Full PASS at `ad87a68a1f8d0595f51a3c02bde022a63ea22cc6`;
- E7 source/tests/read-only Tactical UI are implemented awaiting Full;
- Core DSL Freeze / sidecar/provider/Add-on boundaries remain authoritative.

Do not claim yet:

- trusted Full PASS for E7;
- that any real JMA generation has passed E6 or been promoted;
- autonomous family-head promotion;
- a strongest/profitable generation;
- trained TacticalMemory/learner;
- adaptive lower-timeframe/tick deployment;
- parent-context DSL binding or functioning multi-symbol deployment Add-on;
- macro context attribution/deployment;
- production generalization/live readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.

## Immediate boundary

Do not begin E8 Macro Context Attribution / Deployment executable work before E7 is trusted green.

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
