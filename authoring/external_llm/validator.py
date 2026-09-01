"""Fail-closed validation for untrusted external strategy drafts.

The external model is proposal-only. This module performs deterministic schema,
capability, data identity, axis-boundary, causality, DSL parser/semantic and
compile dry-run validation. It never executes a backtest and never persists a
Strategy/Condition artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

import numpy as np

from authoring.external_llm.manifest import AuthoringManifest, SUPPORTED_STATUSES
from authoring.external_llm.prompt_builder import (
    CORRECTION_TEMPLATE_VERSION,
    PROMPT_BUILDER_VERSION,
    PROMPT_TEMPLATE_VERSION,
    SKILL_VERSION,
)
from axes.axis1_dsl.core.bounded_loops import lower_bounded_loops
from axes.axis1_dsl.core.dsl_parser import DSLParseError, DSLParser
from axes.axis1_dsl.core.dsl_semantic import DSLSemanticAnalyzer, DSLSemanticError
from axes.axis1_dsl.core.multi_output import lower_multi_output
from axes.axis1_dsl.core.user_functions import lower_user_functions
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding
from axes.axis1_dsl.runtime.intrabar_lifecycle import extract_intrabar_handlers


DRAFT_SCHEMA = "external_strategy_draft/v1"
VALIDATOR_VERSION = "external_authoring_validator/v1"
FINAL_STATUSES = frozenset(
    {"ACCEPTED_DRAFT", "REQUIRES_CORRECTION", "BLOCKED_NEEDS_CAPABILITY", "BLOCKED_USER_CLARIFICATION"}
)


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: str
    error_code: str | None = None
    error_message: str | None = None
    root_cause_class: str = "UNKNOWN"
    source_location: str | None = None
    capability_id: str | None = None
    feature_id: str | None = None
    data_source_id: str | None = None
    timeframe: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "root_cause_class": self.root_cause_class,
            "source_location": self.source_location,
            "capability_id": self.capability_id,
            "feature_id": self.feature_id,
            "data_source_id": self.data_source_id,
            "timeframe": self.timeframe,
        }


@dataclass(frozen=True)
class ValidationReport:
    request_id: str
    draft_id: str
    final_status: str
    stages: tuple[StageResult, ...]
    draft: Mapping[str, Any] | None
    manifest_hash: str

    @property
    def accepted(self) -> bool:
        return self.final_status == "ACCEPTED_DRAFT"

    @property
    def final_stage(self) -> StageResult:
        return self.stages[-1]

    def public_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "draft_id": self.draft_id,
            "final_status": self.final_status,
            "accepted": self.accepted,
            "manifest_hash": self.manifest_hash,
            "stages": [item.public_dict() for item in self.stages],
        }


class DraftSchemaError(ValueError):
    def __init__(self, message: str, code: str = "DRAFT_SCHEMA_ERROR", location: str = "$"):
        self.code = str(code)
        self.location = str(location)
        super().__init__(message)


def _stable_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DraftSchemaError(f"non-finite value at {path}", "NONFINITE_VALUE", path)
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise DraftSchemaError(f"bad mapping key at {path}", "BAD_MAPPING_KEY", path)
            result[key] = _safe(item, f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_safe(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise DraftSchemaError(f"opaque value at {path}", "OPAQUE_VALUE", path)


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DraftSchemaError(f"{path} must be object", "BAD_TYPE", path)
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise DraftSchemaError(f"{path} must be array", "BAD_TYPE", path)
    return value


def _text(value: Any, path: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise DraftSchemaError(f"{path} must be string", "BAD_TYPE", path)
    return value


def _exact_keys(value: Mapping[str, Any], required: set[str], path: str) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise DraftSchemaError(f"{path} missing fields: {', '.join(missing)}", "MISSING_FIELD", path)
    if unknown:
        raise DraftSchemaError(f"{path} unknown fields: {', '.join(unknown)}", "UNKNOWN_FIELD", path)


def ingest_external_draft(raw: str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DraftSchemaError("external response must be exactly one JSON object", "INVALID_JSON", "$") from exc
    elif isinstance(raw, Mapping):
        value = dict(raw)
    else:
        raise DraftSchemaError("external draft must be JSON object or JSON text", "BAD_DRAFT_INPUT", "$")
    value = _safe(value)
    root = _mapping(value, "$")
    required = {
        "schema_version", "request_id", "intent_summary", "assumptions", "unresolved_questions",
        "needs_capability", "selection_plan", "strategy_plan", "dsl_code", "projection_requests",
        "data_dependencies", "rationale",
    }
    _exact_keys(root, required, "$")
    if root["schema_version"] != DRAFT_SCHEMA:
        raise DraftSchemaError("unsupported draft schema_version", "BAD_SCHEMA", "$.schema_version")
    _text(root["request_id"], "$.request_id")
    _text(root["intent_summary"], "$.intent_summary", allow_empty=True)
    _text(root["dsl_code"], "$.dsl_code", allow_empty=True)

    assumptions = _list(root["assumptions"], "$.assumptions")
    assumption_ids: set[str] = set()
    for index, item in enumerate(assumptions):
        path = f"$.assumptions[{index}]"
        obj = _mapping(item, path)
        _exact_keys(obj, {"id", "text", "material"}, path)
        identity = _text(obj["id"], f"{path}.id")
        _text(obj["text"], f"{path}.text")
        if not isinstance(obj["material"], bool):
            raise DraftSchemaError("assumption.material must be boolean", "BAD_TYPE", f"{path}.material")
        if identity in assumption_ids:
            raise DraftSchemaError("duplicate assumption id", "DUPLICATE_ID", f"{path}.id")
        assumption_ids.add(identity)

    questions = _list(root["unresolved_questions"], "$.unresolved_questions")
    question_ids: set[str] = set()
    for index, item in enumerate(questions):
        path = f"$.unresolved_questions[{index}]"
        obj = _mapping(item, path)
        _exact_keys(obj, {"id", "text", "blocks_validation"}, path)
        identity = _text(obj["id"], f"{path}.id")
        _text(obj["text"], f"{path}.text")
        if not isinstance(obj["blocks_validation"], bool):
            raise DraftSchemaError("question.blocks_validation must be boolean", "BAD_TYPE", f"{path}.blocks_validation")
        if identity in question_ids:
            raise DraftSchemaError("duplicate question id", "DUPLICATE_ID", f"{path}.id")
        question_ids.add(identity)

    needs = _list(root["needs_capability"], "$.needs_capability")
    needed_ids: set[str] = set()
    for index, item in enumerate(needs):
        path = f"$.needs_capability[{index}]"
        obj = _mapping(item, path)
        _exact_keys(obj, {"capability_id", "reason"}, path)
        identity = _text(obj["capability_id"], f"{path}.capability_id")
        _text(obj["reason"], f"{path}.reason")
        if identity in needed_ids:
            raise DraftSchemaError("duplicate needs_capability id", "DUPLICATE_ID", f"{path}.capability_id")
        needed_ids.add(identity)

    selection = _mapping(root["selection_plan"], "$.selection_plan")
    _exact_keys(selection, {"as_of_policy", "lookback", "universe", "filters", "rankings", "candidate_output", "evidence_required"}, "$.selection_plan")
    if selection["as_of_policy"] != "point_in_time":
        raise DraftSchemaError("selection as_of_policy must be point_in_time", "BAD_AS_OF_POLICY", "$.selection_plan.as_of_policy")
    _mapping(selection["lookback"], "$.selection_plan.lookback")
    _mapping(selection["universe"], "$.selection_plan.universe")
    _list(selection["filters"], "$.selection_plan.filters")
    _list(selection["rankings"], "$.selection_plan.rankings")
    _mapping(selection["candidate_output"], "$.selection_plan.candidate_output")
    _list(selection["evidence_required"], "$.selection_plan.evidence_required")

    strategy = _mapping(root["strategy_plan"], "$.strategy_plan")
    _exact_keys(strategy, {"timeframe", "inputs", "entry", "exit", "risk", "state", "context_dependencies"}, "$.strategy_plan")
    timeframe = _text(strategy["timeframe"], "$.strategy_plan.timeframe")
    if re.fullmatch(r"[0-9]+(?:m|h|d|w|M)", timeframe) is None:
        raise DraftSchemaError("invalid strategy timeframe", "BAD_TIMEFRAME", "$.strategy_plan.timeframe")
    _mapping(strategy["inputs"], "$.strategy_plan.inputs")
    for name in ("entry", "exit", "risk", "state", "context_dependencies"):
        _list(strategy[name], f"$.strategy_plan.{name}")
    for name in ("projection_requests", "data_dependencies"):
        values = _list(root[name], f"$.{name}")
        if any(not isinstance(item, (str, Mapping)) for item in values):
            raise DraftSchemaError(f"$.{name} items must be string/object", "BAD_TYPE", f"$.{name}")
    rationale = _list(root["rationale"], "$.rationale")
    if any(not isinstance(item, str) for item in rationale):
        raise DraftSchemaError("rationale items must be strings", "BAD_TYPE", "$.rationale")
    return dict(root)


def _pass(stage: str) -> StageResult:
    return StageResult(stage=stage, status="PASS", root_cause_class="UNKNOWN")


def _failed(stage: str, code: str, message: str, cause: str, **kwargs: Any) -> StageResult:
    return StageResult(stage=stage, status="FAIL", error_code=code, error_message=message, root_cause_class=cause, **kwargs)


def _blocked(stage: str, code: str, message: str, cause: str, **kwargs: Any) -> StageResult:
    return StageResult(stage=stage, status="BLOCKED", error_code=code, error_message=message, root_cause_class=cause, **kwargs)


def _report(request_id: str, draft: Mapping[str, Any] | None, manifest: AuthoringManifest, stages: list[StageResult], final_status: str) -> ValidationReport:
    if final_status not in FINAL_STATUSES:
        raise ValueError(f"unsupported final status: {final_status}")
    draft_id = "unparsed" if draft is None else _stable_hash(draft)
    return ValidationReport(request_id, draft_id, final_status, tuple(stages), draft, manifest.manifest_hash)


def _require_capability(manifest: AuthoringManifest, capability_id: str) -> StageResult | None:
    item = manifest.capability_by_id.get(capability_id)
    if item is None:
        return _failed("CAPABILITY", "UNKNOWN_CAPABILITY", f"unknown capability id: {capability_id}", "LLM_DRAFT_DEFECT", capability_id=capability_id)
    if item.get("status") not in SUPPORTED_STATUSES:
        return _blocked("CAPABILITY", "UNSUPPORTED_CAPABILITY", f"capability is not executable: {capability_id} ({item.get('status')})", "DSL_CAPABILITY_GAP", capability_id=capability_id)
    return None


def _detected_capabilities(dsl_code: str) -> tuple[str, ...]:
    result: set[str] = set()
    if re.search(r"\bfunction\s+[A-Za-z_]\w*\s*\(", dsl_code):
        result.add("dsl.user_functions")
    if re.search(r"\bfor\s+[A-Za-z_]\w*\s+in\s+range\s*\(", dsl_code):
        result.add("dsl.bounded_loops")
    if re.search(r"(?m)^\s*[A-Za-z_]\w*\s*,\s*[A-Za-z_]\w*\s*=", dsl_code):
        result.add("dsl.multi_output")
    if re.search(r"\bon_tick\s*\{|\bon_fill\s*\{", dsl_code):
        result.add("runtime.intrabar_state")
    return tuple(sorted(result))


def _walk_ids(value: Any, *, key_name: str) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == key_name and isinstance(item, str):
                found.append(item)
            found.extend(_walk_ids(item, key_name=key_name))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_ids(item, key_name=key_name))
    return tuple(found)


def _contains_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        if set(value) & keys:
            return True
        return any(_contains_key(item, keys) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, keys) for item in value)
    return False


def _contains_forbidden_mode(value: Any) -> str | None:
    forbidden = {"nearest", "nearest_time", "previous_nearest", "fill_forward", "fill-forward", "interpolation"}
    if isinstance(value, str) and value.strip().lower() in forbidden:
        return value
    if isinstance(value, Mapping):
        for item in value.values():
            match = _contains_forbidden_mode(item)
            if match is not None:
                return match
    if isinstance(value, list):
        for item in value:
            match = _contains_forbidden_mode(item)
            if match is not None:
                return match
    return None


def _dry_market(size: int = 256) -> tuple[dict[str, np.ndarray], tuple[str, ...]]:
    index = np.arange(size, dtype=float)
    close = 100.0 + index * 0.03 + np.sin(index * 0.19) * 1.7
    base = datetime(2026, 1, 2, 9, 0, 0)
    stamps = tuple((base + timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S") for i in range(size))
    return {
        "open": close - 0.1,
        "high": close + 0.8,
        "low": close - 0.8,
        "close": close,
        "volume": 1000.0 + index,
        "date": np.asarray([float(item[:8]) for item in stamps]),
        "time": np.asarray([float(item[8:]) for item in stamps]),
    }, stamps


def _context_binding(manifest: AuthoringManifest, stamps: Sequence[str]) -> DSLContextSeriesBinding | None:
    if not manifest.context_feature_types:
        return None
    types = manifest.context_types
    values: dict[str, list[Any]] = {}
    for feature_id, kind in types.items():
        sample: Any = 1.0 if kind == "NUMBER" else (False if kind == "BOOLEAN" else "AUTHORING_FIXTURE")
        values[feature_id] = [sample for _ in stamps]
    return DSLContextSeriesBinding.from_prepared(
        target_symbol="AUTHORING_FIXTURE",
        target_times=stamps,
        frame_hash="authoring-dry-run-frame-v1",
        registry_hash=manifest.manifest_hash,
        feature_types=types,
        feature_values=values,
    )


def validate_external_draft(
    raw: str | Mapping[str, Any],
    *,
    request_id: str,
    manifest: AuthoringManifest,
    accepted_assumption_ids: Sequence[str] = (),
) -> ValidationReport:
    request_identity = str(request_id).strip()
    if not request_identity:
        raise ValueError("request_id is required")
    if not isinstance(manifest, AuthoringManifest):
        raise ValueError("manifest must be AuthoringManifest")
    stages: list[StageResult] = []

    try:
        draft = ingest_external_draft(raw)
    except DraftSchemaError as exc:
        stages.append(_failed("SCHEMA", exc.code, str(exc), "LLM_DRAFT_DEFECT", source_location=exc.location))
        return _report(request_identity, None, manifest, stages, "REQUIRES_CORRECTION")
    if draft["request_id"] != request_identity:
        stages.append(_failed("SCHEMA", "REQUEST_ID_MISMATCH", "draft request_id does not match authoring request", "LLM_DRAFT_DEFECT", source_location="$.request_id"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("SCHEMA"))

    for need in draft["needs_capability"]:
        capability_id = need["capability_id"]
        item = manifest.capability_by_id.get(capability_id)
        if item is None:
            stages.append(_failed("CAPABILITY", "UNKNOWN_CAPABILITY", f"unknown needs_capability id: {capability_id}", "LLM_DRAFT_DEFECT", capability_id=capability_id))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
        if item.get("status") in SUPPORTED_STATUSES:
            stages.append(_failed("CAPABILITY", "CAPABILITY_ALREADY_SUPPORTED", f"needs_capability lists an already-supported capability: {capability_id}", "LLM_DRAFT_DEFECT", capability_id=capability_id))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
        stages.append(_blocked("CAPABILITY", "BLOCKED_NEEDS_CAPABILITY", f"draft requires unavailable capability: {capability_id}", "DSL_CAPABILITY_GAP", capability_id=capability_id))
        return _report(request_identity, draft, manifest, stages, "BLOCKED_NEEDS_CAPABILITY")

    for capability_id in _detected_capabilities(draft["dsl_code"]):
        issue = _require_capability(manifest, capability_id)
        if issue is not None:
            stages.append(issue)
            status = "BLOCKED_NEEDS_CAPABILITY" if issue.status == "BLOCKED" else "REQUIRES_CORRECTION"
            return _report(request_identity, draft, manifest, stages, status)
    calls = set(re.findall(r"(?<![\w.])([A-Za-z_]\w*\.[A-Za-z_]\w*)\s*\(", draft["dsl_code"]))
    unknown_calls = sorted(calls - set(manifest.supported_function_names) - set(manifest.order_commands))
    if unknown_calls:
        stages.append(_failed("CAPABILITY", "UNKNOWN_DSL_FUNCTION", f"DSL function/command is not registered: {unknown_calls[0]}", "LLM_DRAFT_DEFECT", capability_id=unknown_calls[0]))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("CAPABILITY"))

    feature_ids = set(_walk_ids(draft["selection_plan"], key_name="feature_id")) | set(_walk_ids(draft["data_dependencies"], key_name="feature_id"))
    for feature_id in sorted(feature_ids):
        if feature_id not in set(manifest.feature_ids):
            stages.append(_failed("DATA_SOURCE", "UNKNOWN_FEATURE_ID", f"feature id is not registered for authoring: {feature_id}", "DATA_CONTRACT_GAP", feature_id=feature_id))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    source_ids = set(_walk_ids(draft["selection_plan"], key_name="data_source_id")) | set(_walk_ids(draft["data_dependencies"], key_name="data_source_id"))
    for source_id in sorted(source_ids):
        if source_id not in set(manifest.data_source_ids):
            stages.append(_failed("DATA_SOURCE", "UNKNOWN_DATA_SOURCE_ID", f"data source id is not registered for authoring: {source_id}", "DATA_CONTRACT_GAP", data_source_id=source_id))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    allowed_dependencies = set(manifest.feature_ids) | set(manifest.data_source_ids) | set(manifest.context_types)
    for dependency in draft["data_dependencies"]:
        if isinstance(dependency, str) and dependency not in allowed_dependencies:
            stages.append(_failed("DATA_SOURCE", "UNKNOWN_DATA_DEPENDENCY", f"data dependency identity is not registered: {dependency}", "DATA_CONTRACT_GAP"))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    context_refs = set(re.findall(r"\bctx\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\b", draft["dsl_code"]))
    context_refs |= set(_walk_ids(draft["strategy_plan"]["context_dependencies"], key_name="context_id"))
    for item in draft["strategy_plan"]["context_dependencies"]:
        if isinstance(item, str):
            context_refs.add(item)
    for context_id in sorted(context_refs):
        if context_id not in manifest.context_types:
            stages.append(_failed("DATA_SOURCE", "UNKNOWN_CONTEXT_ID", f"context id is not registered: {context_id}", "DATA_CONTRACT_GAP", feature_id=context_id))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("DATA_SOURCE"))

    if _contains_key(draft["selection_plan"], {"dsl_code", "order", "order_command", "entry", "exit", "risk", "context_dependencies"}):
        stages.append(_failed("AXIS_BOUNDARY", "BAD_SELECTION_AXIS", "selection_plan contains single-instrument strategy/execution semantics", "AXIS_CONTRACT_GAP"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    if _contains_key(draft["strategy_plan"], {"universe", "rankings", "candidate_output", "as_of_policy", "top_n"}):
        stages.append(_failed("AXIS_BOUNDARY", "BAD_STRATEGY_AXIS", "strategy_plan contains cross-sectional selection semantics", "AXIS_CONTRACT_GAP"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("AXIS_BOUNDARY"))

    forbidden_mode = _contains_forbidden_mode(draft["selection_plan"]) or _contains_forbidden_mode(draft["data_dependencies"])
    if forbidden_mode is not None:
        stages.append(_failed("TIMEFRAME_CAUSALITY", "NON_CAUSAL_LOOKUP_MODE", f"forbidden point-in-time lookup mode: {forbidden_mode}", "DATA_CONTRACT_GAP"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    declared_timeframe = None
    match = re.search(r"\btimeframe\s*=\s*[\"']([^\"']+)[\"']", draft["dsl_code"])
    if match:
        declared_timeframe = match.group(1)
        if declared_timeframe != draft["strategy_plan"]["timeframe"]:
            stages.append(_failed("TIMEFRAME_CAUSALITY", "BAD_STRATEGY_TIMEFRAME", "strategy_plan timeframe does not match DSL timeframe", "LLM_DRAFT_DEFECT", timeframe=draft["strategy_plan"]["timeframe"]))
            return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("TIMEFRAME_CAUSALITY"))

    try:
        intrabar = extract_intrabar_handlers(draft["dsl_code"])
        loops = lower_bounded_loops(intrabar.source)
        functions = lower_user_functions(loops.source)
        multi = lower_multi_output(functions.source)
        document = DSLParser.parse(multi.source)
    except (DSLParseError, ValueError) as exc:
        stages.append(_failed("DSL_PARSER", str(getattr(exc, "code", "DSL_PARSE_ERROR")), str(exc), "LLM_DRAFT_DEFECT", source_location=f"line {getattr(exc, 'line', 1)}"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("DSL_PARSER"))

    try:
        DSLSemanticAnalyzer.analyze(document, context_feature_types=manifest.context_types)
    except DSLSemanticError as exc:
        stages.append(_failed("DSL_SEMANTIC", str(getattr(exc, "code", "DSL_SEMANTIC_ERROR")), str(exc), "LLM_DRAFT_DEFECT", source_location=f"line {getattr(exc, 'line', 1)}"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("DSL_SEMANTIC"))

    market, stamps = _dry_market()
    binding = _context_binding(manifest, stamps)
    try:
        Axis1DSLRuntime.compile(
            draft["dsl_code"],
            market,
            context_binding=binding,
            target_times=stamps if binding is not None else None,
        )
    except Exception as exc:
        stages.append(_failed("COMPILE_DRY_RUN", str(getattr(exc, "code", "COMPILE_DRY_RUN_FAILED")), str(exc), "LLM_DRAFT_DEFECT"))
        return _report(request_identity, draft, manifest, stages, "REQUIRES_CORRECTION")
    stages.append(_pass("COMPILE_DRY_RUN"))

    # Persistence validation is intentionally non-writing. Exact PIT snapshot/hash
    # binding belongs to later AXIS 2/3 product workflows, not to the LLM proposal.
    stages.append(_pass("PERSISTENCE"))

    blocking_questions = [item for item in draft["unresolved_questions"] if item["blocks_validation"]]
    if blocking_questions:
        stages.append(_blocked("ACCEPTANCE", "UNRESOLVED_QUESTION", blocking_questions[0]["text"], "USER_INTENT_AMBIGUITY"))
        return _report(request_identity, draft, manifest, stages, "BLOCKED_USER_CLARIFICATION")
    accepted = set(str(item) for item in accepted_assumption_ids)
    unaccepted = [item for item in draft["assumptions"] if item["material"] and item["id"] not in accepted]
    if unaccepted:
        stages.append(_blocked("ACCEPTANCE", "MATERIAL_ASSUMPTION_NOT_ACCEPTED", unaccepted[0]["text"], "USER_INTENT_AMBIGUITY"))
        return _report(request_identity, draft, manifest, stages, "BLOCKED_USER_CLARIFICATION")
    stages.append(_pass("ACCEPTANCE"))
    return _report(request_identity, draft, manifest, stages, "ACCEPTED_DRAFT")


def validation_errors(report: ValidationReport) -> tuple[dict[str, Any], ...]:
    return tuple(item.public_dict() for item in report.stages if item.status != "PASS")


def build_validation_event(
    report: ValidationReport,
    *,
    iteration: int,
    occurred_at: str,
    previous_draft_id: str | None = None,
    user_request_hash: str | None = None,
    external_model_label: str | None = None,
) -> dict[str, Any]:
    if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
        raise ValueError("iteration must be a non-negative integer")
    if not isinstance(occurred_at, str) or not occurred_at.strip():
        raise ValueError("occurred_at is required")
    final = report.final_stage
    if report.final_status == "ACCEPTED_DRAFT":
        resolution = (False, True, "NONE", "accepted deterministic draft")
    elif report.final_status == "BLOCKED_NEEDS_CAPABILITY":
        resolution = (False, False, "BLOCKED_NEEDS_CAPABILITY", "required capability is unavailable")
    elif report.final_status == "BLOCKED_USER_CLARIFICATION":
        resolution = (False, False, "USER_CLARIFICATION", "human intent confirmation is required")
    else:
        resolution = (True, False, "PROMPT_CORRECTION", "external draft correction required")
    body = {
        "schema_version": "authoring_validation_event/v1",
        "request_id": report.request_id,
        "draft_id": report.draft_id,
        "previous_draft_id": previous_draft_id,
        "iteration": iteration,
        "occurred_at": occurred_at,
        "user_request_hash": user_request_hash,
        "intent_cluster_id": None,
        "versions": {
            "skill_version": SKILL_VERSION,
            "prompt_builder_version": PROMPT_BUILDER_VERSION,
            "prompt_template_version": CORRECTION_TEMPLATE_VERSION if iteration else PROMPT_TEMPLATE_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "external_model_label": external_model_label,
            "axis1_contract_version": report.manifest_hash,
            "axis2_contract_version": None,
            "axis3_contract_version": None,
        },
        "validation": final.public_dict(),
        "resolution": {
            "correction_prompt_generated": resolution[0],
            "next_draft_id": None,
            "resolved": resolution[1],
            "resolution_class": resolution[2],
            "resolution_note": resolution[3],
        },
    }
    body["event_id"] = _stable_hash(body)
    return body
