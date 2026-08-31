"""Deterministic filter/rank/top-N selection over an immutable AXIS 2 snapshot.

This module never computes market features and never calls AXIS 1.  It consumes
only a validated :class:`PointInTimeSnapshot` and a versioned selection spec.
Missing/invalid evidence excludes a symbol explicitly; it is never replaced by
zero, false, a neutral value, nearest-time data, or provider lookups.

Ordering can use either:
- already-frozen ranking evidence (RANK / PERCENTILE); or
- an already-frozen numeric feature value (VALUE).

A VALUE sort creates only a deterministic selection ordering.  It does not
pretend to create or mutate snapshot ranking evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from axes.axis2_selection.snapshots.exact_asof import (
    PointInTimeSnapshot,
    SnapshotRow,
)


AXIS2_SELECTION_SPEC_SCHEMA = "axis2_selection_spec/v1"
AXIS2_CANDIDATE_SET_SCHEMA = "axis2_candidate_set/v1"
METRICS = frozenset({"VALUE", "RANK", "PERCENTILE"})
OPERATORS = frozenset({"EQ", "NE", "GT", "GTE", "LT", "LTE", "IN", "NOT_IN"})
DIRECTIONS = frozenset({"ASC", "DESC"})


class SelectionError(ValueError):
    def __init__(self, message: str, code: str = "AXIS2_SELECTION_ERROR"):
        self.code = str(code)
        super().__init__(message)


def _strict_keys(
    value: Mapping[str, Any],
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
    label: str,
) -> None:
    if not isinstance(value, Mapping):
        raise SelectionError(f"{label} must be a mapping", "BAD_MAPPING")
    supplied = set(value)
    missing = sorted(required - supplied)
    unknown = sorted(supplied - required - optional)
    if missing:
        raise SelectionError(f"{label} missing fields: {', '.join(missing)}", "MISSING_FIELD")
    if unknown:
        raise SelectionError(f"{label} unknown fields: {', '.join(unknown)}", "UNKNOWN_FIELD")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectionError(f"{label} must be a non-empty string", "BAD_TEXT")
    return value.strip()


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 14 or not value.isdigit():
        raise SelectionError(f"{label} must be YYYYMMDDHHMMSS", "BAD_TIMESTAMP")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SelectionError(f"{label} must be a positive integer", "BAD_INTEGER")
    return int(value)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SelectionError(f"{label} must be numeric", "BAD_NUMBER")
    result = float(value)
    if not math.isfinite(result):
        raise SelectionError(f"{label} must be finite", "NONFINITE_VALUE")
    return result


def _primitive(value: Any, label: str) -> Any:
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _finite_number(value, label)
    if isinstance(value, str):
        return value
    raise SelectionError(f"{label} must be a JSON scalar", "BAD_OPERAND")


def _operand(value: Any, operator: str, label: str) -> Any:
    if operator in {"IN", "NOT_IN"}:
        if not isinstance(value, list) or not value:
            raise SelectionError(f"{label} must be a non-empty list", "BAD_OPERAND")
        normalized = tuple(_primitive(item, f"{label}[]") for item in value)
        if len(set((type(item).__name__, repr(item)) for item in normalized)) != len(normalized):
            raise SelectionError(f"{label} contains duplicate values", "DUPLICATE_OPERAND")
        return normalized
    return _primitive(value, label)


def _same_value_type(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool)
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return not isinstance(actual, bool) and not isinstance(expected, bool)
    return type(actual) is type(expected)


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SelectionFilter:
    rule_id: str
    feature_id: str
    metric: str
    operator: str
    operand: Any
    peer_group_id: str | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SelectionFilter":
        _strict_keys(
            value,
            required=frozenset({"rule_id", "feature_id", "metric", "operator", "operand"}),
            optional=frozenset({"peer_group_id"}),
            label="filter",
        )
        metric = _text(value["metric"], "filter.metric").upper()
        operator = _text(value["operator"], "filter.operator").upper()
        if metric not in METRICS:
            raise SelectionError(f"unsupported filter metric: {metric}", "BAD_METRIC")
        if operator not in OPERATORS:
            raise SelectionError(f"unsupported filter operator: {operator}", "BAD_OPERATOR")
        peer = value.get("peer_group_id")
        item = cls(
            rule_id=_text(value["rule_id"], "filter.rule_id"),
            feature_id=_text(value["feature_id"], "filter.feature_id"),
            metric=metric,
            operator=operator,
            operand=_operand(value["operand"], operator, "filter.operand"),
            peer_group_id=None if peer is None else _text(peer, "filter.peer_group_id"),
        )
        item.validate()
        return item

    def validate(self) -> None:
        _text(self.rule_id, "filter.rule_id")
        _text(self.feature_id, "filter.feature_id")
        if self.metric not in METRICS:
            raise SelectionError(f"unsupported filter metric: {self.metric}", "BAD_METRIC")
        if self.operator not in OPERATORS:
            raise SelectionError(f"unsupported filter operator: {self.operator}", "BAD_OPERATOR")
        if self.peer_group_id is not None:
            _text(self.peer_group_id, "filter.peer_group_id")
        if self.metric in {"RANK", "PERCENTILE"} and self.operator in {"IN", "NOT_IN"}:
            for item in self.operand:
                _finite_number(item, "filter.operand[]")
        if self.metric in {"RANK", "PERCENTILE"} and self.operator not in {"IN", "NOT_IN"}:
            _finite_number(self.operand, "filter.operand")

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        operand = list(self.operand) if isinstance(self.operand, tuple) else self.operand
        return {
            "rule_id": self.rule_id,
            "feature_id": self.feature_id,
            "metric": self.metric,
            "operator": self.operator,
            "operand": operand,
            "peer_group_id": self.peer_group_id,
        }


@dataclass(frozen=True)
class SelectionSort:
    feature_id: str
    metric: str
    direction: str
    peer_group_id: str | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SelectionSort":
        _strict_keys(
            value,
            required=frozenset({"feature_id", "metric", "direction"}),
            optional=frozenset({"peer_group_id"}),
            label="sort",
        )
        peer = value.get("peer_group_id")
        item = cls(
            feature_id=_text(value["feature_id"], "sort.feature_id"),
            metric=_text(value["metric"], "sort.metric").upper(),
            direction=_text(value["direction"], "sort.direction").upper(),
            peer_group_id=None if peer is None else _text(peer, "sort.peer_group_id"),
        )
        item.validate()
        return item

    def validate(self) -> None:
        _text(self.feature_id, "sort.feature_id")
        if self.metric not in METRICS:
            raise SelectionError(f"unsupported sort metric: {self.metric}", "BAD_METRIC")
        if self.direction not in DIRECTIONS:
            raise SelectionError(f"unsupported sort direction: {self.direction}", "BAD_DIRECTION")
        if self.peer_group_id is not None:
            _text(self.peer_group_id, "sort.peer_group_id")

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "feature_id": self.feature_id,
            "metric": self.metric,
            "direction": self.direction,
            "peer_group_id": self.peer_group_id,
        }


@dataclass(frozen=True)
class SelectionSpec:
    selection_id: str
    condition_version: str
    snapshot_id: str
    snapshot_hash: str
    as_of: str
    knowledge_cutoff: str
    filters: tuple[SelectionFilter, ...] = ()
    sort: SelectionSort | None = None
    top_n: int | None = None
    symbol_scope: tuple[str, ...] | None = None
    schema_version: str = AXIS2_SELECTION_SPEC_SCHEMA

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SelectionSpec":
        _strict_keys(
            value,
            required=frozenset(
                {
                    "schema_version",
                    "selection_id",
                    "condition_version",
                    "snapshot_id",
                    "snapshot_hash",
                    "as_of",
                    "knowledge_cutoff",
                    "filters",
                    "sort",
                    "top_n",
                    "symbol_scope",
                }
            ),
            label="selection spec",
        )
        if value["schema_version"] != AXIS2_SELECTION_SPEC_SCHEMA:
            raise SelectionError(
                f"unsupported selection schema: {value['schema_version']}", "BAD_SCHEMA"
            )
        if not isinstance(value["filters"], list):
            raise SelectionError("selection filters must be a list", "BAD_FILTERS")
        sort_raw = value["sort"]
        if sort_raw is not None and not isinstance(sort_raw, Mapping):
            raise SelectionError("selection sort must be a mapping or null", "BAD_SORT")
        top_n_raw = value["top_n"]
        if top_n_raw is not None:
            top_n_raw = _positive_int(top_n_raw, "selection.top_n")
        scope_raw = value["symbol_scope"]
        if scope_raw is not None:
            if not isinstance(scope_raw, list) or not scope_raw:
                raise SelectionError("symbol_scope must be a non-empty list or null", "BAD_SYMBOL_SCOPE")
            scope = tuple(sorted(_text(item, "selection.symbol_scope[]") for item in scope_raw))
        else:
            scope = None
        item = cls(
            selection_id=_text(value["selection_id"], "selection.selection_id"),
            condition_version=_text(value["condition_version"], "selection.condition_version"),
            snapshot_id=_text(value["snapshot_id"], "selection.snapshot_id"),
            snapshot_hash=_text(value["snapshot_hash"], "selection.snapshot_hash"),
            as_of=_timestamp(value["as_of"], "selection.as_of"),
            knowledge_cutoff=_timestamp(value["knowledge_cutoff"], "selection.knowledge_cutoff"),
            filters=tuple(SelectionFilter.from_dict(item) for item in value["filters"]),
            sort=None if sort_raw is None else SelectionSort.from_dict(sort_raw),
            top_n=top_n_raw,
            symbol_scope=scope,
            schema_version=AXIS2_SELECTION_SPEC_SCHEMA,
        )
        item.validate()
        return item

    def validate(self) -> None:
        if self.schema_version != AXIS2_SELECTION_SPEC_SCHEMA:
            raise SelectionError(f"unsupported selection schema: {self.schema_version}", "BAD_SCHEMA")
        _text(self.selection_id, "selection.selection_id")
        _text(self.condition_version, "selection.condition_version")
        _text(self.snapshot_id, "selection.snapshot_id")
        _text(self.snapshot_hash, "selection.snapshot_hash")
        _timestamp(self.as_of, "selection.as_of")
        _timestamp(self.knowledge_cutoff, "selection.knowledge_cutoff")
        if not isinstance(self.filters, tuple):
            raise SelectionError("selection filters must be immutable tuple", "BAD_FILTERS")
        ids: list[str] = []
        for item in self.filters:
            if not isinstance(item, SelectionFilter):
                raise SelectionError("selection filters must contain SelectionFilter", "BAD_FILTER")
            item.validate()
            ids.append(item.rule_id)
        if len(ids) != len(set(ids)):
            raise SelectionError("duplicate filter rule_id", "DUPLICATE_RULE_ID")
        if self.sort is not None:
            if not isinstance(self.sort, SelectionSort):
                raise SelectionError("selection sort must be SelectionSort", "BAD_SORT")
            self.sort.validate()
        if self.top_n is not None:
            _positive_int(self.top_n, "selection.top_n")
            if self.sort is None:
                raise SelectionError("top_n requires an explicit sort contract", "TOP_N_REQUIRES_SORT")
        if self.symbol_scope is not None:
            if not isinstance(self.symbol_scope, tuple) or not self.symbol_scope:
                raise SelectionError("symbol_scope must be immutable non-empty tuple", "BAD_SYMBOL_SCOPE")
            normalized = tuple(sorted(_text(item, "selection.symbol_scope[]") for item in self.symbol_scope))
            if normalized != self.symbol_scope:
                raise SelectionError("symbol_scope must be canonical sorted order", "BAD_SYMBOL_SCOPE")
            if len(set(self.symbol_scope)) != len(self.symbol_scope):
                raise SelectionError("duplicate symbol_scope symbol", "DUPLICATE_SYMBOL")

    def canonical_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "selection_id": self.selection_id,
            "condition_version": self.condition_version,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "as_of": self.as_of,
            "knowledge_cutoff": self.knowledge_cutoff,
            "filters": [item.public_dict() for item in self.filters],
            "sort": None if self.sort is None else self.sort.public_dict(),
            "top_n": self.top_n,
            "symbol_scope": None if self.symbol_scope is None else list(self.symbol_scope),
        }

    @property
    def selection_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "selection_hash": self.selection_hash}


@dataclass(frozen=True)
class Candidate:
    symbol: str
    ordinal: int
    evidence: tuple[Mapping[str, Any], ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "ordinal": self.ordinal,
            "evidence": [dict(item) for item in self.evidence],
        }


@dataclass(frozen=True)
class CandidateSet:
    selection_id: str
    condition_version: str
    selection_hash: str
    snapshot_id: str
    snapshot_hash: str
    as_of: str
    knowledge_cutoff: str
    universe_id: str
    source_symbol_count: int
    eligible_count_before_top_n: int
    candidates: tuple[Candidate, ...]
    exclusions: tuple[Mapping[str, Any], ...]
    ordering: Mapping[str, Any] | None
    schema_version: str = AXIS2_CANDIDATE_SET_SCHEMA

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "selection_id": self.selection_id,
            "condition_version": self.condition_version,
            "selection_hash": self.selection_hash,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "as_of": self.as_of,
            "knowledge_cutoff": self.knowledge_cutoff,
            "universe_id": self.universe_id,
            "source_symbol_count": self.source_symbol_count,
            "eligible_count_before_top_n": self.eligible_count_before_top_n,
            "selected_count": len(self.candidates),
            "candidates": [item.public_dict() for item in self.candidates],
            "exclusions": [dict(item) for item in self.exclusions],
            "ordering": None if self.ordering is None else dict(self.ordering),
        }

    @property
    def candidate_set_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "candidate_set_hash": self.candidate_set_hash}


@dataclass
class _WorkingCandidate:
    symbol: str
    evidence: list[dict[str, Any]]
    sort_value: float | None = None


class Axis2SelectionEngine:
    """Filter and order symbols using only one exact immutable snapshot."""

    @staticmethod
    def _validate_binding(snapshot: PointInTimeSnapshot, spec: SelectionSpec) -> None:
        if not isinstance(snapshot, PointInTimeSnapshot):
            raise SelectionError("snapshot must be PointInTimeSnapshot", "BAD_SNAPSHOT")
        snapshot.validate()
        spec.validate()
        if spec.snapshot_id != snapshot.snapshot_id:
            raise SelectionError("selection snapshot_id mismatch", "SNAPSHOT_ID_MISMATCH")
        if spec.snapshot_hash != snapshot.snapshot_hash:
            raise SelectionError("selection snapshot_hash mismatch", "SNAPSHOT_HASH_MISMATCH")
        if spec.as_of != snapshot.as_of:
            raise SelectionError("selection as_of must exactly match snapshot", "AS_OF_MISMATCH")
        if spec.knowledge_cutoff != snapshot.knowledge_cutoff:
            raise SelectionError(
                "selection knowledge_cutoff must exactly match snapshot", "CUTOFF_MISMATCH"
            )

    @staticmethod
    def _source_symbols(snapshot: PointInTimeSnapshot, spec: SelectionSpec) -> tuple[str, ...]:
        available = tuple(sorted({row.symbol for row in snapshot.rows}))
        if spec.symbol_scope is None:
            return available
        available_set = set(available)
        missing = [symbol for symbol in spec.symbol_scope if symbol not in available_set]
        if missing:
            raise SelectionError(
                f"symbol_scope contains symbols absent from snapshot: {', '.join(missing)}",
                "SYMBOL_NOT_IN_SNAPSHOT",
            )
        return spec.symbol_scope

    @staticmethod
    def _resolve_row(
        snapshot: PointInTimeSnapshot,
        symbol: str,
        feature_id: str,
        peer_group_id: str | None,
    ) -> SnapshotRow | None:
        matches = [
            row
            for row in snapshot.rows
            if row.symbol == symbol
            and row.feature_id == feature_id
            and (
                peer_group_id is None
                or (row.ranking is not None and row.ranking.peer_group_id == peer_group_id)
            )
        ]
        if not matches:
            return None
        if len(matches) > 1:
            raise SelectionError(
                f"feature lookup is ambiguous; peer_group_id required: {symbol}/{feature_id}",
                "AMBIGUOUS_FEATURE",
            )
        return matches[0]

    @staticmethod
    def _metric(row: SnapshotRow, metric: str) -> tuple[Any, str]:
        if metric == "VALUE":
            return row.value, row.value_type
        if row.ranking is None:
            raise SelectionError(
                f"ranking evidence required for metric {metric}: {row.symbol}/{row.feature_id}",
                "RANKING_EVIDENCE_REQUIRED",
            )
        if metric == "RANK":
            return row.ranking.rank, "NUMBER"
        if metric == "PERCENTILE":
            return row.ranking.percentile, "NUMBER"
        raise SelectionError(f"unsupported metric: {metric}", "BAD_METRIC")

    @staticmethod
    def _evaluate(actual: Any, operator: str, operand: Any, value_type: str) -> bool:
        if operator in {"GT", "GTE", "LT", "LTE"}:
            if value_type != "NUMBER":
                raise SelectionError(
                    f"ordered comparison requires NUMBER, got {value_type}", "TYPE_MISMATCH"
                )
            left = _finite_number(actual, "feature value")
            right = _finite_number(operand, "filter operand")
            return {
                "GT": left > right,
                "GTE": left >= right,
                "LT": left < right,
                "LTE": left <= right,
            }[operator]
        if operator in {"EQ", "NE"}:
            if not _same_value_type(actual, operand):
                raise SelectionError("filter operand type does not match feature", "TYPE_MISMATCH")
            equal = actual == operand
            return bool(equal if operator == "EQ" else not equal)
        if operator in {"IN", "NOT_IN"}:
            for item in operand:
                if not _same_value_type(actual, item):
                    raise SelectionError("filter IN operand type does not match feature", "TYPE_MISMATCH")
            present = actual in operand
            return bool(present if operator == "IN" else not present)
        raise SelectionError(f"unsupported operator: {operator}", "BAD_OPERATOR")

    @staticmethod
    def _evidence(row: SnapshotRow, *, role: str, metric: str, rule_id: str | None = None) -> dict[str, Any]:
        rank = None if row.ranking is None else row.ranking.public_dict()
        value, _ = Axis2SelectionEngine._metric(row, metric)
        return {
            "role": role,
            "rule_id": rule_id,
            "feature_id": row.feature_id,
            "metric": metric,
            "observed": float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value,
            "value_type": row.value_type if metric == "VALUE" else "NUMBER",
            "validity": row.validity,
            "ranking": rank,
            "provenance": row.provenance.public_dict(),
        }

    @classmethod
    def select(cls, snapshot: PointInTimeSnapshot, spec: SelectionSpec | Mapping[str, Any]) -> CandidateSet:
        plan = spec if isinstance(spec, SelectionSpec) else SelectionSpec.from_dict(spec)
        cls._validate_binding(snapshot, plan)
        symbols = cls._source_symbols(snapshot, plan)
        survivors: list[_WorkingCandidate] = []
        exclusions: list[dict[str, Any]] = []

        for symbol in symbols:
            evidence: list[dict[str, Any]] = []
            failed_rule_ids: list[str] = []
            reason_codes: list[str] = []
            for rule in plan.filters:
                row = cls._resolve_row(snapshot, symbol, rule.feature_id, rule.peer_group_id)
                if row is None:
                    failed_rule_ids.append(rule.rule_id)
                    reason_codes.append("ROW_NOT_FOUND")
                    continue
                if row.validity != "VALID":
                    failed_rule_ids.append(rule.rule_id)
                    reason_codes.append(f"ROW_{row.validity}")
                    continue
                actual, value_type = cls._metric(row, rule.metric)
                passed = cls._evaluate(actual, rule.operator, rule.operand, value_type)
                item = cls._evidence(row, role="FILTER", metric=rule.metric, rule_id=rule.rule_id)
                item["operator"] = rule.operator
                item["operand"] = list(rule.operand) if isinstance(rule.operand, tuple) else rule.operand
                item["passed"] = bool(passed)
                evidence.append(item)
                if not passed:
                    failed_rule_ids.append(rule.rule_id)
                    reason_codes.append("FILTER_FALSE")
            if failed_rule_ids:
                exclusions.append(
                    {
                        "symbol": symbol,
                        "reason_codes": reason_codes,
                        "failed_rule_ids": failed_rule_ids,
                    }
                )
            else:
                survivors.append(_WorkingCandidate(symbol=symbol, evidence=evidence))

        if plan.sort is not None:
            sortable: list[_WorkingCandidate] = []
            sort_exclusions: list[dict[str, Any]] = []
            for item in survivors:
                row = cls._resolve_row(
                    snapshot,
                    item.symbol,
                    plan.sort.feature_id,
                    plan.sort.peer_group_id,
                )
                if row is None:
                    sort_exclusions.append(
                        {
                            "symbol": item.symbol,
                            "reason_codes": ["SORT_ROW_NOT_FOUND"],
                            "failed_rule_ids": [],
                        }
                    )
                    continue
                if row.validity != "VALID":
                    sort_exclusions.append(
                        {
                            "symbol": item.symbol,
                            "reason_codes": [f"SORT_ROW_{row.validity}"],
                            "failed_rule_ids": [],
                        }
                    )
                    continue
                value, value_type = cls._metric(row, plan.sort.metric)
                if value_type != "NUMBER":
                    raise SelectionError("selection sort requires numeric evidence", "SORT_TYPE_MISMATCH")
                item.sort_value = _finite_number(value, "sort value")
                item.evidence.append(cls._evidence(row, role="SORT", metric=plan.sort.metric))
                sortable.append(item)
            survivors = sortable
            exclusions.extend(sort_exclusions)
            survivors.sort(key=lambda item: item.symbol)
            survivors.sort(
                key=lambda item: item.sort_value,
                reverse=plan.sort.direction == "DESC",
            )
        else:
            survivors.sort(key=lambda item: item.symbol)

        eligible_before_top_n = len(survivors)
        if plan.top_n is not None and len(survivors) > plan.top_n:
            dropped = survivors[plan.top_n :]
            survivors = survivors[: plan.top_n]
            exclusions.extend(
                {
                    "symbol": item.symbol,
                    "reason_codes": ["TOP_N_CUTOFF"],
                    "failed_rule_ids": [],
                }
                for item in dropped
            )

        candidates = tuple(
            Candidate(
                symbol=item.symbol,
                ordinal=index + 1,
                evidence=tuple(item.evidence),
            )
            for index, item in enumerate(survivors)
        )
        exclusions_sorted = tuple(sorted(exclusions, key=lambda item: item["symbol"]))
        ordering = None if plan.sort is None else {
            **plan.sort.public_dict(),
            "tie_breaker": "SYMBOL_ASC",
            "top_n": plan.top_n,
            "rank_recomputed": False,
        }
        return CandidateSet(
            selection_id=plan.selection_id,
            condition_version=plan.condition_version,
            selection_hash=plan.selection_hash,
            snapshot_id=snapshot.snapshot_id,
            snapshot_hash=snapshot.snapshot_hash,
            as_of=snapshot.as_of,
            knowledge_cutoff=snapshot.knowledge_cutoff,
            universe_id=snapshot.universe_id,
            source_symbol_count=len(symbols),
            eligible_count_before_top_n=eligible_before_top_n,
            candidates=candidates,
            exclusions=exclusions_sorted,
            ordering=ordering,
        )
