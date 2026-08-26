# Multi-Symbol Add-on Extension Policy

Status: **AUTHORITATIVE OPTIONAL EXTENSION POLICY / 2026-08-26 KST**

## 1. Purpose

The Quant DSL must remain a single-instrument tactical language while preserving a safe extension point for future cross-symbol analysis, ranking and deployment research.

The governing rule is:

> **Multi-symbol capability is an optional Add-on, not an Instrument DSL responsibility.**

Showing many symbols on one chart does not grant one symbol's DSL authority to read, rank or trade from another symbol's runtime state.

## 2. Single-instrument Core boundary

One Instrument DSL candidate owns one declared instrument execution context at a time.

It may consume only the market series and supported causal context explicitly assigned to that instrument contract.

The Instrument DSL must not directly implement:

- arbitrary cross-symbol data requests;
- peer-symbol signal reads;
- universe enumeration;
- cross-symbol ranking;
- capital competition between symbols;
- portfolio slot allocation;
- leader/follower selection across symbols;
- dynamic selection of which symbol should trade;
- hidden dependency on what other chart panes currently display.

These are orchestration / deployment responsibilities.

## 3. Visualization is not authority

A Chart Document or UI may display many symbols, indicators and tactical states together.

That is observation only.

```text
multi-symbol chart display
!=
multi-symbol Instrument DSL authority
```

Chart composition must never become an implicit strategy input.

## 4. Safe Add-on seam

A future multi-symbol analyzer should consume immutable, point-in-time snapshots exported by already-evaluated single-instrument tactics.

Recommended input contract:

```text
InstrumentSignalSnapshot
  symbol
  as_of / knowledge_cutoff
  candidate_hash
  family_id / generation_hash
  tactic_trigger
  hard_guard_state
  local admissibility state
  declared comparison metrics
  source / evidence identity
  snapshot_hash
```

The Add-on reads snapshots. It does not call private Parser/Runtime internals and does not mutate the originating DSL candidate.

Only features explicitly exported in the snapshot contract are visible to the Add-on. Adding a new comparison feature is an Add-on/evidence contract change, not a reason to add cross-symbol syntax to Instrument DSL.

## 5. Explicit universe and time alignment

Every multi-symbol analysis run must declare its opportunity set.

```text
universe_id
symbols[]
as_of
knowledge_cutoff
source authority
policy version/hash
```

The Add-on must not silently discover or guess the universe.

All compared snapshots must be valid at the declared point in time. Future-close, end-of-day winner information or later revised data must not affect an earlier ranking.

Missing, stale or mismatched snapshots must be handled explicitly and fail closed according to the declared policy; they must never be silently substituted.

## 6. Deterministic comparison

If the Add-on ranks symbols, the policy must declare exact comparison fields and deterministic tie-breaking.

Example:

```text
eligible = tactic_trigger AND hard_guards_pass
rank by:
  1. setup_quality DESC
  2. trading_value_state DESC
  3. symbol ASC
max_slots = 2
```

The same snapshots plus the same policy must always produce the same result.

No hidden universal score is required. Multi-axis evidence or Pareto-style selection is allowed when its rules are explicit and reproducible.

## 7. Narrow output contract

The Add-on must not place broker orders directly.

Recommended output:

```text
MultiSymbolAnalysisResult
  universe_id
  as_of
  policy_hash
  ranked_symbols[]
  allowed_symbols[]
  blocked_symbols[]
  priorities
  reasons
  input_snapshot_hashes[]
  result_hash
```

A later orchestration/deployment layer may translate this into an explicit `DeploymentDecision` or `entry_gate`-style admissibility decision.

The authority remains:

```text
single-instrument tactic trigger
AND local hard guards
AND optional Add-on deployment permission
AND common execution policy
 -> BrokerEmulator
```

A multi-symbol Add-on cannot bypass local hard guards, execution settings, position rules, costs or Broker authority.

## 8. Optional Parent Feature Provider role

A Multi-Symbol Add-on may also publish a bounded set of **registered parent-context features** for later read-only consumption by Instrument DSLs.

Examples:

```text
sector.breadth
sector.leader_strength
group.follower_alignment
group.relative_strength
```

In this role the Add-on does not expose peer-symbol runtime state directly to the DSL. It emits an immutable `ContextLayerSnapshot` with explicit `as_of`, source, feature schema/version and snapshot hash.

The allowed flow is:

```text
immutable per-symbol snapshots
 -> Multi-Symbol Add-on analysis
 -> registered parent features
 -> ContextLayerSnapshot
 -> BattlefieldContext
 -> future read-only DSL ctx.* binding
```

Direct DSL syntax for peer-symbol queries remains prohibited. The detailed parent-context contract is defined in `PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`.

## 9. Default disabled and replaceable

The Add-on is optional and disabled by default during baseline micro-tactic discovery.

A tactic's neutral baseline must remain runnable without the Add-on.

The system must be able to replace or remove the Add-on without changing:

- Instrument DSL syntax;
- DSL Parser / Runtime;
- indicator semantics;
- Backtest accounting;
- BrokerEmulator;
- historical single-instrument TacticalProfiles.

A tactic that explicitly requires a registered parent-context feature may become ineligible when its Provider/Add-on is unavailable; missing required context must fail closed rather than be guessed.

## 10. Research before deployment

Cross-symbol analysis should first run in observation-only research mode:

```text
single-instrument results
 -> immutable snapshots
 -> Add-on analysis / ranking
 -> compare hypothetical selection evidence
```

Only after causal Train/Validation/OOS evidence exists may an Add-on be considered for deployment gating or for supplying a parent feature used by an entry rule.

This prevents an attractive relative-strength or peer-comparison idea from immediately becoming live order authority.

## 11. Relationship to macro layers

A multi-symbol Add-on is below or beside later market/sector/group deployment intelligence, not a replacement for it.

A future hierarchy may be:

```text
Market / Sector / Group Parent Feature Providers
 -> BattlefieldContext
 -> Instrument DSL local tactic
 -> optional multi-symbol Add-on ranking
 -> deployment policy
 -> common execution policy
 -> BrokerEmulator
```

The same Add-on may contribute parent features and later perform ranking only when those responsibilities are separately versioned and auditable. Each layer consumes explicit evidence and produces explicit decisions. No layer rewrites the lower layer's historical evidence.

## 12. Change-control rule

Before implementing any cross-symbol feature, ask:

```text
Can the requirement be expressed as read-only analysis of immutable per-symbol snapshots?
```

If yes, it must remain an Add-on.

If the result is intended for Instrument DSL consumption, ask:

```text
Can the Add-on publish a registered point-in-time parent feature instead of giving the DSL peer-symbol access?
```

If yes, use the Parent Feature Provider / Context binding seam.

Direct cross-symbol syntax in Instrument DSL is prohibited unless a future authority change proves that the capability cannot be safely represented through the Add-on/context seam and independently satisfies the Core promotion criteria in `CORE_DSL_FREEZE_ADAPTIVE_SIDECAR_POLICY.md`.

## 13. Success criterion

The architecture is correct when all statements are true:

```text
A single-instrument tactic remains simple, deterministic and independently testable.

A future multi-symbol analyzer can compare those tactics safely without changing Instrument DSL or Broker authority.

Useful cross-symbol conclusions can be inherited as registered parent context without exposing arbitrary peer-symbol access to the DSL.
```
