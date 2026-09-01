"""Deterministic aggregation of authoring validation evidence.

This module consumes only ``authoring_validation_event/v1`` data.  It does not
change prompts, skills, validators, DSL code, registries, or axis artifacts.
Recommendations are evidence summaries that always require human approval.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


AUTHORING_EVENT_SCHEMA = "authoring_validation_event/v1"
IMPROVEMENT_REPORT_SCHEMA = "authoring_improvement_report/v1"

VALID_STAGES = frozenset(
    {
        "SCHEMA",
        "CAPABILITY",
        "DATA_SOURCE",
        "AXIS_BOUNDARY",
        "TIMEFRAME_CAUSALITY",
        "DSL_PARSER",
        "DSL_SEMANTIC",
        "COMPILE_DRY_RUN",
        "PERSISTENCE",
        "ACCEPTANCE",
    }
)
VALID_STATUSES = frozenset({"PASS", "FAIL", "BLOCKED"})
ROOT_CAUSES = frozenset(
    {
        "PROMPT_DEFECT",
        "SKILL_GAP",
        "LLM_DRAFT_DEFECT",
        "SCHEMA_DEFECT",
        "VALIDATOR_DEFECT",
        "DSL_PARSER_GAP",
        "DSL_SEMANTIC_GAP",
        "DSL_CAPABILITY_GAP",
        "DATA_CONTRACT_GAP",
        "AXIS_CONTRACT_GAP",
        "USER_INTENT_AMBIGUITY",
        "TEST_DEFECT",
        "ENVIRONMENT_ISSUE",
        "UNKNOWN",
    }
)
RESOLUTION_CLASSES = frozenset(
    {
        "NONE",
        "PROMPT_CORRECTION",
        "SKILL_UPDATE",
        "USER_CLARIFICATION",
        "VALIDATOR_FIX",
        "DATA_CONTRACT_FIX",
        "AXIS_CONTRACT_FIX",
        "DSL_PARSER_TRANCHE",
        "DSL_SEMANTIC_TRANCHE",
        "DSL_CAPABILITY_TRANCHE",
        "BLOCKED_NEEDS_CAPABILITY",
        "CANCELED",
    }
)

_REMEDIATION = {
    "PROMPT_DEFECT": ("PROMPT_WORDING", "Prompt wording/examples"),
    "SKILL_GAP": ("SKILL_MANIFEST", "Skill capability guidance"),
    "LLM_DRAFT_DEFECT": ("CORRECTION_PROMPT", "Correction prompt/diagnostics"),
    "SCHEMA_DEFECT": ("SCHEMA_VALIDATOR", "Authoring schema contract"),
    "VALIDATOR_DEFECT": ("VALIDATOR_FIX", "Deterministic validator"),
    "DSL_PARSER_GAP": ("DSL_PARSER_TRANCHE", "AXIS 1 generic parser capability"),
    "DSL_SEMANTIC_GAP": ("DSL_SEMANTIC_TRANCHE", "AXIS 1 generic semantic capability"),
    "DSL_CAPABILITY_GAP": ("DSL_CAPABILITY_TRANCHE", "AXIS 1 generic DSL capability"),
    "DATA_CONTRACT_GAP": ("DATA_CONTRACT_FIX", "Point-in-time data contract/registry"),
    "AXIS_CONTRACT_GAP": ("AXIS_CONTRACT_FIX", "Cross-axis contract boundary"),
    "USER_INTENT_AMBIGUITY": ("USER_CLARIFICATION", "User intent clarification flow"),
    "TEST_DEFECT": ("TEST_FIX", "Validation/regression tests"),
    "ENVIRONMENT_ISSUE": ("ENVIRONMENT_FIX", "Execution environment"),
    "UNKNOWN": ("MANUAL_REVIEW", "Manual root-cause classification"),
}

_GENERIC_DSL_CAUSES = frozenset({"DSL_PARSER_GAP", "DSL_SEMANTIC_GAP", "DSL_CAPABILITY_GAP"})


class ImprovementAnalysisError(ValueError):
    def __init__(self, message: str, code: str = "IMPROVEMENT_ANALYSIS_ERROR"):
        self.code = str(code)
        super().__init__(message)


def _stable_hash(value: Any) -> str:
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strict_mapping(value: Any, *, required: set[str], optional: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ImprovementAnalysisError(f"{label} must be an object", "BAD_EVENT_SHAPE")
    supplied = set(value)
    missing = sorted(required - supplied)
    unknown = sorted(supplied - required - optional)
    if missing:
        raise ImprovementAnalysisError(f"{label} missing fields: {', '.join(missing)}", "EVENT_MISSING_FIELD")
    if unknown:
        raise ImprovementAnalysisError(f"{label} unknown fields: {', '.join(unknown)}", "EVENT_UNKNOWN_FIELD")
    return value


def _text(value: Any, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ImprovementAnalysisError(f"{label} must be a non-empty string", "BAD_EVENT_VALUE")
    return value


def _nullable_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ImprovementAnalysisError(f"{label} must be string or null", "BAD_EVENT_VALUE")
    return value


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ImprovementAnalysisError(f"{label} must be boolean", "BAD_EVENT_VALUE")
    return value


def validate_validation_event(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize one Step 12 validation event.

    ``event_id`` is verified against the canonical event body so stored evidence
    cannot be silently edited before aggregation.
    """
    root = _strict_mapping(
        value,
        required={
            "schema_version",
            "event_id",
            "request_id",
            "draft_id",
            "iteration",
            "occurred_at",
            "versions",
            "validation",
            "resolution",
        },
        optional={"previous_draft_id", "user_request_hash", "intent_cluster_id"},
        label="event",
    )
    if root["schema_version"] != AUTHORING_EVENT_SCHEMA:
        raise ImprovementAnalysisError("unsupported validation event schema", "BAD_EVENT_SCHEMA")
    _text(root["event_id"], "event.event_id")
    _text(root["request_id"], "event.request_id")
    _text(root["draft_id"], "event.draft_id")
    iteration = root["iteration"]
    if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
        raise ImprovementAnalysisError("event.iteration must be a non-negative integer", "BAD_EVENT_ITERATION")
    _text(root["occurred_at"], "event.occurred_at")
    _nullable_text(root.get("previous_draft_id"), "event.previous_draft_id")
    _nullable_text(root.get("user_request_hash"), "event.user_request_hash")
    _nullable_text(root.get("intent_cluster_id"), "event.intent_cluster_id")

    versions = _strict_mapping(
        root["versions"],
        required={"skill_version", "prompt_builder_version", "prompt_template_version", "validator_version"},
        optional={"external_model_label", "axis1_contract_version", "axis2_contract_version", "axis3_contract_version"},
        label="event.versions",
    )
    for key in ("skill_version", "prompt_builder_version", "prompt_template_version", "validator_version"):
        _text(versions[key], f"event.versions.{key}")
    for key in ("external_model_label", "axis1_contract_version", "axis2_contract_version", "axis3_contract_version"):
        _nullable_text(versions.get(key), f"event.versions.{key}")

    validation = _strict_mapping(
        root["validation"],
        required={"stage", "status", "error_code", "root_cause_class"},
        optional={"error_message", "source_location", "capability_id", "feature_id", "data_source_id", "timeframe"},
        label="event.validation",
    )
    stage = _text(validation["stage"], "event.validation.stage")
    status = _text(validation["status"], "event.validation.status")
    cause = _text(validation["root_cause_class"], "event.validation.root_cause_class")
    if stage not in VALID_STAGES:
        raise ImprovementAnalysisError(f"unsupported validation stage: {stage}", "BAD_EVENT_STAGE")
    if status not in VALID_STATUSES:
        raise ImprovementAnalysisError(f"unsupported validation status: {status}", "BAD_EVENT_STATUS")
    if cause not in ROOT_CAUSES:
        raise ImprovementAnalysisError(f"unsupported root cause: {cause}", "BAD_ROOT_CAUSE")
    error_code = _nullable_text(validation.get("error_code"), "event.validation.error_code")
    if status == "PASS" and error_code is not None:
        raise ImprovementAnalysisError("PASS validation cannot carry error_code", "BAD_EVENT_STATUS_SHAPE")
    if status != "PASS" and (error_code is None or not error_code.strip()):
        raise ImprovementAnalysisError("non-PASS validation requires error_code", "BAD_EVENT_STATUS_SHAPE")
    for key in ("error_message", "source_location", "capability_id", "feature_id", "data_source_id", "timeframe"):
        _nullable_text(validation.get(key), f"event.validation.{key}")

    resolution = _strict_mapping(
        root["resolution"],
        required={"correction_prompt_generated", "resolved", "resolution_class"},
        optional={"next_draft_id", "resolution_note"},
        label="event.resolution",
    )
    _bool(resolution["correction_prompt_generated"], "event.resolution.correction_prompt_generated")
    _bool(resolution["resolved"], "event.resolution.resolved")
    resolution_class = _text(resolution["resolution_class"], "event.resolution.resolution_class")
    if resolution_class not in RESOLUTION_CLASSES:
        raise ImprovementAnalysisError(f"unsupported resolution class: {resolution_class}", "BAD_RESOLUTION_CLASS")
    _nullable_text(resolution.get("next_draft_id"), "event.resolution.next_draft_id")
    _nullable_text(resolution.get("resolution_note"), "event.resolution.resolution_note")

    canonical = json.loads(json.dumps(root, ensure_ascii=False, sort_keys=True, allow_nan=False))
    supplied_id = canonical.pop("event_id")
    expected_id = _stable_hash(canonical)
    if supplied_id != expected_id:
        raise ImprovementAnalysisError("validation event_id hash mismatch", "EVENT_HASH_MISMATCH")
    canonical["event_id"] = supplied_id
    return canonical


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _count_rows(values: Sequence[str], field: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [{field: key, "count": counts[key]} for key in sorted(counts, key=lambda item: (-counts[item], item))]


def _version_rows(events: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for event in events:
        version = str(event["versions"][key])
        groups.setdefault(version, []).append(event)
    rows: list[dict[str, Any]] = []
    for version in sorted(groups):
        items = groups[version]
        non_pass = sum(1 for item in items if item["validation"]["status"] != "PASS")
        accepted = sum(
            1
            for item in items
            if item["validation"]["stage"] == "ACCEPTANCE" and item["validation"]["status"] == "PASS"
        )
        rows.append(
            {
                "version": version,
                "event_count": len(items),
                "non_pass_count": non_pass,
                "non_pass_rate": _rate(non_pass, len(items)),
                "accepted_count": accepted,
            }
        )
    return rows


def _intent_identity(event: Mapping[str, Any]) -> str:
    return str(event.get("intent_cluster_id") or event.get("user_request_hash") or event["request_id"])


@dataclass(frozen=True)
class ImprovementReport:
    review_id: str
    min_recurrence: int
    min_independent_intents_for_dsl: int
    event_set_hash: str
    event_count: int
    request_count: int
    metrics: Mapping[str, Any]
    breakdowns: Mapping[str, Any]
    recommendations: tuple[Mapping[str, Any], ...]
    deferred_candidates: tuple[Mapping[str, Any], ...]
    schema_version: str = IMPROVEMENT_REPORT_SCHEMA

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "review_id": self.review_id,
            "analysis_policy": {
                "min_recurrence": self.min_recurrence,
                "min_independent_intents_for_dsl": self.min_independent_intents_for_dsl,
                "automatic_mutation": False,
                "human_approval_required": True,
            },
            "event_set_hash": self.event_set_hash,
            "event_count": self.event_count,
            "request_count": self.request_count,
            "metrics": dict(self.metrics),
            "breakdowns": dict(self.breakdowns),
            "recommendations": [dict(item) for item in self.recommendations],
            "deferred_candidates": [dict(item) for item in self.deferred_candidates],
        }

    @property
    def report_hash(self) -> str:
        return _stable_hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "report_hash": self.report_hash}


def analyze_validation_events(
    events: Sequence[Mapping[str, Any]],
    *,
    review_id: str,
    min_recurrence: int = 2,
    min_independent_intents_for_dsl: int = 2,
) -> ImprovementReport:
    """Aggregate validation events into metrics and non-executing recommendations."""
    identity = str(review_id).strip()
    if not identity:
        raise ImprovementAnalysisError("review_id is required", "BAD_REVIEW_ID")
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence) or not events:
        raise ImprovementAnalysisError("events must be a non-empty sequence", "BAD_EVENT_SET")
    for value, label in (
        (min_recurrence, "min_recurrence"),
        (min_independent_intents_for_dsl, "min_independent_intents_for_dsl"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ImprovementAnalysisError(f"{label} must be a positive integer", "BAD_ANALYSIS_THRESHOLD")

    canonical_events = [validate_validation_event(item) for item in events]
    event_ids = [item["event_id"] for item in canonical_events]
    if len(event_ids) != len(set(event_ids)):
        raise ImprovementAnalysisError("duplicate validation event_id", "DUPLICATE_EVENT")
    canonical_events.sort(key=lambda item: (item["request_id"], item["iteration"], item["event_id"]))

    per_request: dict[str, list[Mapping[str, Any]]] = {}
    iteration_keys: set[tuple[str, int]] = set()
    for event in canonical_events:
        key = (event["request_id"], int(event["iteration"]))
        if key in iteration_keys:
            raise ImprovementAnalysisError("duplicate request iteration", "DUPLICATE_REQUEST_ITERATION")
        iteration_keys.add(key)
        per_request.setdefault(event["request_id"], []).append(event)

    initial_events = [item for item in canonical_events if item["iteration"] == 0]
    first_pass_accepted = sum(
        1
        for item in initial_events
        if item["validation"]["stage"] == "ACCEPTANCE" and item["validation"]["status"] == "PASS"
    )
    max_iterations = [max(int(item["iteration"]) for item in items) for items in per_request.values()]
    failures = [item for item in canonical_events if item["validation"]["status"] != "PASS"]
    blocked = [item for item in canonical_events if item["validation"]["status"] == "BLOCKED"]

    repeated_failures = 0
    for items in per_request.values():
        seen: set[tuple[Any, ...]] = set()
        for event in items:
            validation = event["validation"]
            if validation["status"] == "PASS":
                continue
            fingerprint = (
                validation["root_cause_class"],
                validation.get("error_code"),
                validation.get("capability_id"),
                validation.get("feature_id"),
                validation.get("data_source_id"),
            )
            if fingerprint in seen:
                repeated_failures += 1
            seen.add(fingerprint)

    stage_rows: list[dict[str, Any]] = []
    for stage in sorted({item["validation"]["stage"] for item in canonical_events}):
        items = [item for item in canonical_events if item["validation"]["stage"] == stage]
        non_pass = sum(1 for item in items if item["validation"]["status"] != "PASS")
        stage_rows.append(
            {
                "stage": stage,
                "event_count": len(items),
                "non_pass_count": non_pass,
                "non_pass_rate": _rate(non_pass, len(items)),
            }
        )

    error_codes = [str(item["validation"]["error_code"]) for item in failures if item["validation"].get("error_code")]
    root_causes = [str(item["validation"]["root_cause_class"]) for item in failures]
    blocked_capabilities = [
        str(item["validation"]["capability_id"])
        for item in failures
        if item["validation"].get("capability_id")
        and (
            item["validation"].get("error_code") == "BLOCKED_NEEDS_CAPABILITY"
            or item["validation"]["root_cause_class"] == "DSL_CAPABILITY_GAP"
        )
    ]

    request_rows: list[dict[str, Any]] = []
    for request_id in sorted(per_request):
        items = per_request[request_id]
        last = max(items, key=lambda item: (item["iteration"], item["event_id"]))
        request_rows.append(
            {
                "request_id": request_id,
                "event_count": len(items),
                "max_iteration": max(int(item["iteration"]) for item in items),
                "last_stage": last["validation"]["stage"],
                "last_status": last["validation"]["status"],
            }
        )

    metrics = {
        "first_pass_observed_requests": len(initial_events),
        "first_pass_accepted_requests": first_pass_accepted,
        "first_pass_acceptance_rate": _rate(first_pass_accepted, len(initial_events)),
        "mean_correction_iterations": round(sum(max_iterations) / len(max_iterations), 6),
        "non_pass_event_count": len(failures),
        "non_pass_event_rate": _rate(len(failures), len(canonical_events)),
        "blocked_event_count": len(blocked),
        "capability_block_rate": _rate(
            sum(1 for item in failures if item["validation"]["root_cause_class"] == "DSL_CAPABILITY_GAP"),
            len(canonical_events),
        ),
        "parser_failure_rate": _rate(
            sum(1 for item in failures if item["validation"]["stage"] == "DSL_PARSER"),
            len(canonical_events),
        ),
        "semantic_failure_rate": _rate(
            sum(1 for item in failures if item["validation"]["stage"] == "DSL_SEMANTIC"),
            len(canonical_events),
        ),
        "schema_failure_rate": _rate(
            sum(1 for item in failures if item["validation"]["stage"] == "SCHEMA"),
            len(canonical_events),
        ),
        "unknown_feature_rate": _rate(
            sum(1 for item in failures if item["validation"].get("error_code") == "UNKNOWN_FEATURE_ID"),
            len(canonical_events),
        ),
        "ambiguous_intent_rate": _rate(
            sum(1 for item in failures if item["validation"]["root_cause_class"] == "USER_INTENT_AMBIGUITY"),
            len(canonical_events),
        ),
        "repeat_error_rate": _rate(repeated_failures, len(failures)),
    }

    breakdowns = {
        "stage": stage_rows,
        "error_codes": _count_rows(error_codes, "error_code"),
        "root_causes": _count_rows(root_causes, "root_cause_class"),
        "blocked_capabilities": _count_rows(blocked_capabilities, "capability_id"),
        "prompt_template_versions": _version_rows(canonical_events, "prompt_template_version"),
        "skill_versions": _version_rows(canonical_events, "skill_version"),
        "validator_versions": _version_rows(canonical_events, "validator_version"),
        "requests": request_rows,
    }

    recommendations: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    by_cause: dict[str, list[Mapping[str, Any]]] = {}
    for event in failures:
        by_cause.setdefault(event["validation"]["root_cause_class"], []).append(event)

    for cause in sorted(by_cause):
        items = by_cause[cause]
        request_ids = sorted({str(item["request_id"]) for item in items})
        intent_ids = sorted({_intent_identity(item) for item in items})
        codes = sorted({str(item["validation"].get("error_code") or "") for item in items if item["validation"].get("error_code")})
        action_class, target = _REMEDIATION[cause]
        base = {
            "root_cause_class": cause,
            "action_class": action_class,
            "target": target,
            "evidence_count": len(items),
            "request_count": len(request_ids),
            "independent_intent_count": len(intent_ids),
            "error_codes": codes,
            "requires_human_approval": True,
            "automatic_mutation": False,
        }
        if len(items) < min_recurrence:
            deferred.append({**base, "defer_reason": "BELOW_RECURRENCE_THRESHOLD"})
            continue
        if cause in _GENERIC_DSL_CAUSES and len(intent_ids) < min_independent_intents_for_dsl:
            deferred.append({**base, "defer_reason": "INSUFFICIENT_INDEPENDENT_INTENTS_FOR_DSL_CHANGE"})
            continue
        recommendations.append(base)

    recommendations.sort(key=lambda item: (-int(item["evidence_count"]), item["root_cause_class"], item["action_class"]))
    deferred.sort(key=lambda item: (-int(item["evidence_count"]), item["root_cause_class"], item["action_class"]))
    event_set_hash = _stable_hash(sorted(event_ids))

    return ImprovementReport(
        review_id=identity,
        min_recurrence=min_recurrence,
        min_independent_intents_for_dsl=min_independent_intents_for_dsl,
        event_set_hash=event_set_hash,
        event_count=len(canonical_events),
        request_count=len(per_request),
        metrics=metrics,
        breakdowns=breakdowns,
        recommendations=tuple(recommendations),
        deferred_candidates=tuple(deferred),
    )
