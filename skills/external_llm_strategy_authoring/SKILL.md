# DSL External Strategy Authoring Skill

Version: `dsl-external-authoring-skill/v2-generated-manifest`

Purpose: convert a human trading request into a **structured, untrusted strategy proposal**. This skill has no execution authority.

## 1. Authority

The prompt's `AUTHORING_MANIFEST` is the current machine authority for capabilities, DSL functions, order commands, AXIS 2 feature/data-source IDs, and read-only context IDs.

```text
AUTHORING_MANIFEST > this static skill text
```

Do not rely on a hardcoded capability list in this file. The local prompt builder generates the current supported/unavailable sets from the machine registry so this distribution artifact cannot silently become the execution SSOT.

## 2. Non-negotiable rules

1. Do not invent DSL syntax, function names, capability IDs, feature IDs, data sources, context IDs, order commands, or bridge fields.
2. Use only identities listed in `AUTHORING_MANIFEST`.
3. If a required **listed** capability is unavailable, put its exact ID in `needs_capability`; do not approximate it with invented syntax.
4. Keep cross-sectional symbol selection separate from single-symbol trading execution.
5. Market regime, beta universe, sector strength, peer ranking and other cross-symbol evidence are precomputed point-in-time evidence, not Instrument DSL calculations.
6. Instrument DSL may consume only read-only `ctx.*` identities listed in the manifest.
7. Never use future information, nearest-time lookup, fill-forward, interpolation, or silent defaulting for required evidence.
8. Preserve explicit user timeframes. Never silently convert selection, execution or MTF timeframes.
9. Put material ambiguity in `assumptions` or `unresolved_questions`; do not silently decide trading semantics.
10. Return exactly one JSON object matching `external_strategy_draft/v1`, with no prose outside the object.
11. When validator errors are supplied, preserve the original intent and already-valid fields and change only what is required by those errors.

## 3. Architecture boundaries

```text
AXIS 2 Selection
= who should be considered
= immutable exact-as-of evidence -> filter/rank/top-N -> CandidateSet

AXIS 3 Monetization
= which Condition/Strategy version is used
= CRUD/version/lineage/lifecycle/orchestration

AXIS 1 DSL
= what one selected instrument does
= deterministic indicators/state/logic/orders/risk/MTF/read-only context

Chart
= displays supplied evidence/projections only
```

Do not put universe discovery or peer ranking in AXIS 1 DSL. Do not put DSL order logic in AXIS 2. Do not make AXIS 3 recalculate either selection or DSL semantics.

## 4. Machine-generated prompt material

The local prompt builder supplies at least:

```text
verbatim user request
capability registry hash
supported capability IDs
unavailable capability IDs
supported registered DSL functions
supported order commands
exact AXIS 2 feature IDs
exact data-source IDs
exact ctx feature IDs + types
strict external_strategy_draft/v1 schema
```

Absence from the manifest means **not authorized for this authoring request**. Do not infer a missing identity from this skill text or from general financial knowledge.

## 5. Structured response

Return exactly this top-level shape:

```json
{
  "schema_version": "external_strategy_draft/v1",
  "request_id": "REQUEST_ID_FROM_PROMPT",
  "intent_summary": "",
  "assumptions": [],
  "unresolved_questions": [],
  "needs_capability": [],
  "selection_plan": {
    "as_of_policy": "point_in_time",
    "lookback": {},
    "universe": {},
    "filters": [],
    "rankings": [],
    "candidate_output": {},
    "evidence_required": []
  },
  "strategy_plan": {
    "timeframe": "15m",
    "inputs": {},
    "entry": [],
    "exit": [],
    "risk": [],
    "state": [],
    "context_dependencies": []
  },
  "dsl_code": "",
  "projection_requests": [],
  "data_dependencies": [],
  "rationale": []
}
```

The exact JSON schema embedded in the prompt is authoritative over this illustrative shape.

## 6. Selection rules

`selection_plan` belongs to AXIS 2 and must use exact manifest feature/data-source identities. It may describe point-in-time universe membership, filters, already-frozen ranking/percentile evidence, top-N intent, reference-event evidence and required CandidateSet evidence.

Do not calculate those cross-sectional features inside `dsl_code`. If a reference event is ambiguous (for example first/latest/highest-strength), put the ambiguity in a material assumption or blocking question.

## 7. Strategy rules

`strategy_plan` and `dsl_code` belong to single-instrument execution. Use only currently registered functions and syntax in the prompt manifest. Read-only external evidence may be consumed only through exact listed context IDs.

If the request requires profit-state permissions, entry/exit gating, state transitions, MTF, intrabar behavior, multi-output values, user functions or other advanced features, use them only when the generated capability manifest marks the relevant capability as supported.

Do not infer support from old examples or from this file.

## 8. Time and causality

Keep these identities separate and explicit:

```text
selection/event timeframe
strategy execution timeframe
MTF dependency timeframe
snapshot as_of
knowledge_cutoff
```

Required evidence must be exact-as-of and causal. No nearest/previous-nearest lookup, fill-forward, interpolation, current-value reconstruction of historical evidence, or default-zero substitution is permitted.

## 9. Correction mode

When `VALIDATION_ERRORS` are supplied:

1. Keep the same `request_id`.
2. Preserve the original user intent.
3. Preserve already-valid fields.
4. Correct only reported errors and directly dependent fields.
5. Never bypass an unsupported capability with invented syntax.
6. If correction is impossible because a listed capability is unavailable, return a valid draft with that exact ID in `needs_capability`.
7. If user intent is materially ambiguous, keep it explicit instead of guessing.

## 10. Local acceptance

Your response is still untrusted after generation. The local system independently performs:

```text
strict schema validation
known-capability validation
known feature/data-source/context validation
axis-boundary validation
timeframe/causality validation
DSL parser validation
DSL semantic validation
compile dry-run
non-writing persistence-readiness validation
human acceptance of material assumptions
```

Only the local deterministic pipeline can return `ACCEPTED_DRAFT`. Acceptance does not itself execute a backtest, place an order, or persist/promote a Strategy/Condition version.
