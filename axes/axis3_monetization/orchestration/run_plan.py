"""AXIS 3 orchestration plan over promoted immutable artifacts.

This layer consumes CandidateSet *data* and AXIS 3-owned stored versions.  It
never imports or calls AXIS 1/2 internals.  The output is a deterministic plan
that Step 11 Bridge routing can later turn into versioned AXIS 1 requests.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from axes.axis3_monetization.crud.versioned_store import (
    Axis3StoreError,
    ConditionVersion,
    StrategyVersion,
    VersionedArtifactStore,
)


AXIS3_RUN_PLAN_SCHEMA = "axis3_strategy_run_plan/v1"
AXIS2_CANDIDATE_SET_SCHEMA = "axis2_candidate_set/v1"


class Axis3OrchestrationError(ValueError):
    def __init__(self, message: str, code: str = "AXIS3_ORCHESTRATION_ERROR"):
        self.code = str(code)
        super().__init__(message)


def _safe(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise Axis3OrchestrationError(f"non-finite value at {path}", "NONFINITE_VALUE")
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise Axis3OrchestrationError(f"bad mapping key at {path}", "BAD_MAPPING_KEY")
            result[key] = _safe(item, f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_safe(item, f"{path}[]") for item in value]
    raise Axis3OrchestrationError(f"opaque value at {path}", "OPAQUE_VALUE")


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(
        _safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Axis3OrchestrationError(f"{label} must be non-empty string", "BAD_TEXT")
    return value.strip()


def _candidate_set(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise Axis3OrchestrationError("candidate_set must be a mapping", "BAD_CANDIDATE_SET")
    payload = _safe(value, "$.candidate_set")
    required = {
        "schema_version",
        "selection_id",
        "condition_version",
        "selection_hash",
        "snapshot_id",
        "snapshot_hash",
        "as_of",
        "knowledge_cutoff",
        "candidate_set_hash",
        "candidates",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise Axis3OrchestrationError(
            f"candidate_set missing fields: {', '.join(missing)}", "CANDIDATE_SET_MISSING_FIELD"
        )
    if payload["schema_version"] != AXIS2_CANDIDATE_SET_SCHEMA:
        raise Axis3OrchestrationError("unsupported candidate_set schema", "BAD_CANDIDATE_SET_SCHEMA")
    supplied_hash = _text(payload["candidate_set_hash"], "candidate_set_hash")
    canonical_body = {key: item for key, item in payload.items() if key != "candidate_set_hash"}
    if _hash(canonical_body) != supplied_hash:
        raise Axis3OrchestrationError("candidate_set hash mismatch", "CANDIDATE_SET_HASH_MISMATCH")
    if not isinstance(payload["candidates"], list):
        raise Axis3OrchestrationError("candidate_set.candidates must be list", "BAD_CANDIDATES")
    ordinals: list[int] = []
    symbols: list[str] = []
    for candidate in payload["candidates"]:
        if not isinstance(candidate, Mapping):
            raise Axis3OrchestrationError("candidate must be mapping", "BAD_CANDIDATE")
        if "symbol" not in candidate or "ordinal" not in candidate:
            raise Axis3OrchestrationError("candidate requires symbol/ordinal", "BAD_CANDIDATE")
        symbol = _text(candidate["symbol"], "candidate.symbol")
        ordinal = candidate["ordinal"]
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal <= 0:
            raise Axis3OrchestrationError("candidate.ordinal must be positive integer", "BAD_ORDINAL")
        symbols.append(symbol)
        ordinals.append(int(ordinal))
    if len(symbols) != len(set(symbols)):
        raise Axis3OrchestrationError("duplicate candidate symbol", "DUPLICATE_CANDIDATE")
    if ordinals != list(range(1, len(ordinals) + 1)):
        raise Axis3OrchestrationError("candidate ordinals must be contiguous ordered 1..N", "BAD_ORDINAL")
    return payload


@dataclass(frozen=True)
class ExecutionIntent:
    symbol: str
    candidate_ordinal: int
    strategy_id: str
    strategy_version: int
    strategy_hash: str
    timeframe: str
    dsl_code: str
    settings: Mapping[str, Any]
    condition_id: str
    condition_version: int
    condition_hash: str
    candidate_set_hash: str
    evidence: tuple[Mapping[str, Any], ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "candidate_ordinal": self.candidate_ordinal,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_hash": self.strategy_hash,
            "timeframe": self.timeframe,
            "dsl_code": self.dsl_code,
            "settings": _safe(self.settings),
            "condition_id": self.condition_id,
            "condition_version": self.condition_version,
            "condition_hash": self.condition_hash,
            "candidate_set_hash": self.candidate_set_hash,
            "evidence": [_safe(item) for item in self.evidence],
        }


@dataclass(frozen=True)
class StrategyRunPlan:
    run_id: str
    strategy_id: str
    strategy_version: int
    strategy_hash: str
    condition_id: str
    condition_version: int
    condition_hash: str
    candidate_set_hash: str
    selection_hash: str
    snapshot_hash: str
    as_of: str
    intents: tuple[ExecutionIntent, ...]
    schema_version: str = AXIS3_RUN_PLAN_SCHEMA

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_hash": self.strategy_hash,
            "condition_id": self.condition_id,
            "condition_version": self.condition_version,
            "condition_hash": self.condition_hash,
            "candidate_set_hash": self.candidate_set_hash,
            "selection_hash": self.selection_hash,
            "snapshot_hash": self.snapshot_hash,
            "as_of": self.as_of,
            "intent_count": len(self.intents),
            "intents": [item.public_dict() for item in self.intents],
        }

    @property
    def plan_hash(self) -> str:
        return _hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "plan_hash": self.plan_hash}


def _require_promoted(
    store: VersionedArtifactStore,
    artifact_type: str,
    artifact_id: str,
    version: int,
) -> None:
    try:
        state = store.state(artifact_type, artifact_id, version)
    except Axis3StoreError as exc:
        raise Axis3OrchestrationError(str(exc), "ARTIFACT_NOT_FOUND") from exc
    if state.status != "PROMOTED":
        raise Axis3OrchestrationError(
            f"{artifact_type} must be PROMOTED: {artifact_id}@{version} ({state.status})",
            "ARTIFACT_NOT_PROMOTED",
        )


def _bind_condition_to_candidate_set(condition: ConditionVersion, candidate_set: Mapping[str, Any]) -> None:
    selection = _safe(condition.selection_spec)
    if selection.get("selection_hash") != candidate_set["selection_hash"]:
        raise Axis3OrchestrationError(
            "Condition selection_hash does not match CandidateSet", "SELECTION_HASH_MISMATCH"
        )
    if selection.get("condition_version") != candidate_set["condition_version"]:
        raise Axis3OrchestrationError(
            "Condition version label does not match CandidateSet", "CONDITION_VERSION_MISMATCH"
        )
    if selection.get("snapshot_hash") != candidate_set["snapshot_hash"]:
        raise Axis3OrchestrationError(
            "Condition snapshot_hash does not match CandidateSet", "SNAPSHOT_HASH_MISMATCH"
        )
    if selection.get("as_of") != candidate_set["as_of"]:
        raise Axis3OrchestrationError("Condition as_of does not match CandidateSet", "AS_OF_MISMATCH")
    if selection.get("knowledge_cutoff") != candidate_set["knowledge_cutoff"]:
        raise Axis3OrchestrationError(
            "Condition knowledge_cutoff does not match CandidateSet", "CUTOFF_MISMATCH"
        )


def build_strategy_run_plan(
    store: VersionedArtifactStore,
    *,
    run_id: str,
    strategy_id: str,
    strategy_version: int,
    condition_id: str,
    condition_version: int,
    candidate_set: Mapping[str, Any],
) -> StrategyRunPlan:
    """Create a deterministic, provider-free execution-intent plan.

    No market bars are fetched here and no execution occurs here.  Step 11 owns
    conversion of each intent into a versioned AXIS 1 Bridge request.
    """
    if not isinstance(store, VersionedArtifactStore):
        raise Axis3OrchestrationError("store must be VersionedArtifactStore", "BAD_STORE")
    run_identity = _text(run_id, "run_id")
    try:
        strategy: StrategyVersion = store.get_strategy(strategy_id, strategy_version)
        condition: ConditionVersion = store.get_condition(condition_id, condition_version)
    except Axis3StoreError as exc:
        raise Axis3OrchestrationError(str(exc), "ARTIFACT_NOT_FOUND") from exc
    _require_promoted(store, "STRATEGY", strategy.strategy_id, strategy.version)
    _require_promoted(store, "CONDITION", condition.condition_id, condition.version)
    if (condition.condition_id, condition.version) not in set(strategy.condition_refs):
        raise Axis3OrchestrationError(
            "selected Condition is not referenced by Strategy version", "CONDITION_NOT_REFERENCED"
        )

    candidates = _candidate_set(candidate_set)
    _bind_condition_to_candidate_set(condition, candidates)

    intents: list[ExecutionIntent] = []
    for candidate in candidates["candidates"]:
        evidence = candidate.get("evidence") or []
        if not isinstance(evidence, list):
            raise Axis3OrchestrationError("candidate.evidence must be list", "BAD_EVIDENCE")
        intents.append(
            ExecutionIntent(
                symbol=_text(candidate["symbol"], "candidate.symbol"),
                candidate_ordinal=int(candidate["ordinal"]),
                strategy_id=strategy.strategy_id,
                strategy_version=strategy.version,
                strategy_hash=strategy.artifact_hash,
                timeframe=strategy.timeframe,
                dsl_code=strategy.dsl_code,
                settings=strategy.canonical_dict()["settings"],
                condition_id=condition.condition_id,
                condition_version=condition.version,
                condition_hash=condition.artifact_hash,
                candidate_set_hash=candidates["candidate_set_hash"],
                evidence=tuple(_safe(item) for item in evidence),
            )
        )

    return StrategyRunPlan(
        run_id=run_identity,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.version,
        strategy_hash=strategy.artifact_hash,
        condition_id=condition.condition_id,
        condition_version=condition.version,
        condition_hash=condition.artifact_hash,
        candidate_set_hash=candidates["candidate_set_hash"],
        selection_hash=candidates["selection_hash"],
        snapshot_hash=candidates["snapshot_hash"],
        as_of=candidates["as_of"],
        intents=tuple(intents),
    )
