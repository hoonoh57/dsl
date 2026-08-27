# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / MSA1-MSA3 TRUSTED / CTXVAL1 VALIDATION ACTIVE / 2026-08-27 KST**

## 1. Governing rule

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

Instrument DSL remains single-instrument. Multi-symbol chart display, cohort analysis, leader/follower evidence, GROUP publication or context validation does not create peer-symbol execution authority.

Instrument DSL must not directly perform arbitrary cross-symbol requests, peer-symbol runtime reads, universe enumeration, cross-symbol ranking, leader/follower selection, slot/capital allocation or hidden dependence on displayed chart panes.

## 2. Existing scenario vertical slice

`core/multi_symbol.py` remains the earlier deterministic scenario/cohort vertical slice. MSA1-MSA3 do not rewrite or remove it.

New cross-symbol research should use immutable point-in-time snapshot evidence whenever the requirement can be represented without direct peer-symbol access from Instrument DSL.

## 3. Trusted MSA evidence/publication chain

Trusted checkpoints:

```text
MSA1  adaef963dce717b252f2575896a74462c8a277a2
MSA2  3a5a2ece658ead28a1822ef7482a3d284d12e2d6
MSA3  02904728cb0a39669e6809ba21c4e2dd8eb947e3
```

Each exact checkout received its focused regression PASS and Tactical P1 Full PASS.

The trusted chain is:

```text
single-instrument causal state @ exact t
 -> MSA1 immutable InstrumentSignalSnapshot
 -> explicit SnapshotUniverse
 -> MSA2 bounded exact chronological GROUP evidence
 -> MSA3 bounded aggregate registered GROUP parent features
```

MSA1/MSA2 remain observation-only. MSA3 remains research-only publication. None has operational authority.

## 4. MSA1 immutable snapshot seam

MSA1 requires exact `as_of == knowledge_cutoff`, explicit universe membership, finite declared comparison metrics and stable tactic/evidence identity. Missing/extra symbols, time mismatch or undeclared comparison axes fail closed.

Analysis is deterministic per-axis/Pareto evidence with no hidden universal score:

```text
mode = OBSERVATION_ONLY
operational_authority = false
```

## 5. MSA2 bounded group evidence

MSA2 consumes a bounded chronological sequence of exact MSA1 points under one stable explicit universe and stable tactic identity topology.

Policy explicitly declares metric, MAX/MIN direction, favorable threshold, leader count, lookback, max symbols and max points.

It may describe eligible/favorable breadth, current leaders/followers, direction-normalized spread, follower favorable rate and bounded leader persistence. Leader/follower labels are observation evidence only; missing follower aggregates remain explicit null.

## 6. MSA3 registered GROUP publication — trusted research boundary

MSA3 publishes only aggregate values through the Parent Feature Provider seam:

```text
group.<namespace>_comparison_eligible_rate
group.<namespace>_favorable_breadth_rate
group.<namespace>_leader_persistence_rate
group.<namespace>_leader_follower_spread       optional
group.<namespace>_follower_favorable_rate      optional
```

It does not publish peer symbol identities, rank lists, allowed/blocked symbols, max slots, allocation, entry gate, DeploymentDecision or Broker orders.

The source timeline verifies exact MSA2 `result_hash` evidence and forbids nearest/fill-forward. The GROUP result requires an exact configured SECTOR dependency and records its result hash, preserving:

```text
MARKET -> SECTOR -> GROUP
```

MSA3 remains:

```text
publication_state = RESEARCH_ONLY
operational_authority = false
```

## 7. CTXVAL1 validation before deployment — active

Registered publication is not evidence of usefulness. Before any Add-on-derived GROUP feature can become deployment-policy evidence, it must pass the registered context holdout gate.

CTXVAL1 requires:

```text
trusted NEUTRAL micro profiles
exact registered PCTX1 OBSERVED context
registered feature_id + exact manifest_hash
explicit E8 ContextSliceRule
TRAIN
VALIDATION
OOS
HARSH (>=1, adverse_reason required)
```

Each slice is evaluated independently with declared retained-case, return, drawdown, profitable-rate, cost and MFE-giveback tolerances. There is no hidden score.

A slice that looks favorable on TRAIN but regresses on OOS/HARSH is rejected. Passing evidence receives a slice-specific `validation_evidence_hash`, but CTXVAL1 still has:

```text
operational_authority = false
execution_integration = EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER
```

## 8. Explicit universe and causality

Every cross-symbol research run declares its opportunity set and source authority. The Add-on must not silently discover or guess the universe.

Future-close, later winner information, revised future data, nearest-time substitution and fill-forward are prohibited as earlier comparison inputs.

## 9. Observation/publication/validation is still not deployment selection

The required progression is:

```text
immutable observation evidence
 -> bounded registered parent feature
 -> E8 attribution
 -> CTXVAL1 Train / Validation / OOS / Harsh evidence
 -> explicit E8 deployment policy evidence
 -> separately validated execution integration
```

The eventual authority relationship remains:

```text
single-instrument tactic trigger
AND local hard guards
AND optional separately validated Add-on permission
AND common execution policy
 -> BrokerEmulator
```

An Add-on can never bypass local hard guards, execution settings, accounting or Broker authority.

## 10. Default disabled and replaceable

The Add-on remains optional and disabled by default during neutral micro-tactic discovery. Neutral baselines must run independently without it.

The Add-on must be removable or replaceable without changing Instrument DSL syntax, Parser/Runtime, indicator semantics, Backtest accounting, BrokerEmulator or historical single-instrument TacticalProfiles.

## 11. Change-control rule

If a cross-symbol requirement can be expressed as read-only analysis of immutable per-symbol snapshots, keep it in the Add-on. If its conclusion is intended for Instrument DSL consumption, publish only a bounded registered point-in-time parent feature.

Direct peer-symbol syntax in Instrument DSL is not authorized.

## 12. Current nonclaims

Do not claim yet:

- trusted Full PASS for CTXVAL1;
- empirical GROUP parent-feature OOS benefit;
- validated production Add-on deployment selection;
- GROUP feature operational DEPLOYMENT eligibility;
- portfolio allocation authority;
- live-trading readiness;
- repository-wide compliance PASS.

`REMEDIATION_REQUIRED` remains the broader repository status.
