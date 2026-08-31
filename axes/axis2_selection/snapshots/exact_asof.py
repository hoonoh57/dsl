"""Immutable exact-as-of snapshot contract for AXIS 2 selection.

AXIS 2 consumes already-precomputed point-in-time evidence.  This module owns
only the frozen data contract and deterministic validation/hash rules; it does
not call providers, AXIS 1, databases, ranking engines, or the frozen legacy
core.

The contract is deliberately fail-closed:
- snapshot/as-of/cutoff timestamps are exact 14-digit timestamps;
- every row provenance uses the same knowledge cutoff and formula version;
- source observations cannot occur after the knowledge cutoff;
- missing/invalid values remain explicit None and are never default-filled;
- rank evidence, when supplied, is already frozen evidence rather than an
  instruction to calculate a rank during snapshot validation;
- exact lookup never performs nearest-time, interpolation, or carry-forward.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping


AXIS2_SNAPSHOT_SCHEMA = "axis2_point_in_time_snapshot/v1"
VALUE_TYPES = frozenset({"NUMBER", "BOOLEAN", "STRING"})
VALIDITY_STATES = frozenset({"VALID", "MISSING", "INVALID"})


class ExactAsOfSnapshotError(ValueError):
    def __init__(self, message: str, code: str = "AXIS2_SNAPSHOT_ERROR"):
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
        raise ExactAsOfSnapshotError(f"{label} must be a mapping", "BAD_MAPPING")
    supplied = set(value)
    missing = sorted(required - supplied)
    unknown = sorted(supplied - required - optional)
    if missing:
        raise ExactAsOfSnapshotError(
            f"{label} missing fields: {', '.join(missing)}", "MISSING_FIELD"
        )
    if unknown:
        raise ExactAsOfSnapshotError(
            f"{label} unknown fields: {', '.join(unknown)}", "UNKNOWN_FIELD"
        )


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactAsOfSnapshotError(f"{label} must be a non-empty string", "BAD_TEXT")
    return value.strip()


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 14 or not value.isdigit():
        raise ExactAsOfSnapshotError(
            f"{label} must be YYYYMMDDHHMMSS", "BAD_TIMESTAMP"
        )
    return value


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ExactAsOfSnapshotError(f"{label} must be a positive integer", "BAD_INTEGER")
    return int(value)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExactAsOfSnapshotError(f"{label} must be numeric", "BAD_NUMBER")
    number = float(value)
    if not math.isfinite(number):
        raise ExactAsOfSnapshotError(f"{label} must be finite", "NONFINITE_VALUE")
    return number


@dataclass(frozen=True)
class FeatureProvenance:
    source_ref: str
    observed_as_of: str
    knowledge_cutoff: str
    formula_version: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FeatureProvenance":
        _strict_keys(
            value,
            required=frozenset(
                {"source_ref", "observed_as_of", "knowledge_cutoff", "formula_version"}
            ),
            label="provenance",
        )
        item = cls(
            source_ref=_nonempty_text(value["source_ref"], "provenance.source_ref"),
            observed_as_of=_timestamp(value["observed_as_of"], "provenance.observed_as_of"),
            knowledge_cutoff=_timestamp(
                value["knowledge_cutoff"], "provenance.knowledge_cutoff"
            ),
            formula_version=_nonempty_text(
                value["formula_version"], "provenance.formula_version"
            ),
        )
        item.validate()
        return item

    def validate(self) -> None:
        _nonempty_text(self.source_ref, "provenance.source_ref")
        observed = _timestamp(self.observed_as_of, "provenance.observed_as_of")
        cutoff = _timestamp(self.knowledge_cutoff, "provenance.knowledge_cutoff")
        _nonempty_text(self.formula_version, "provenance.formula_version")
        if observed > cutoff:
            raise ExactAsOfSnapshotError(
                "provenance observation occurs after knowledge cutoff",
                "FUTURE_OBSERVATION",
            )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "source_ref": self.source_ref,
            "observed_as_of": self.observed_as_of,
            "knowledge_cutoff": self.knowledge_cutoff,
            "formula_version": self.formula_version,
        }


@dataclass(frozen=True)
class RankingEvidence:
    ranking_method: str
    eligible_count: int
    rank: int
    percentile: float
    peer_group_id: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RankingEvidence":
        _strict_keys(
            value,
            required=frozenset(
                {"ranking_method", "eligible_count", "rank", "percentile", "peer_group_id"}
            ),
            label="ranking",
        )
        item = cls(
            ranking_method=_nonempty_text(value["ranking_method"], "ranking.ranking_method"),
            eligible_count=_positive_integer(value["eligible_count"], "ranking.eligible_count"),
            rank=_positive_integer(value["rank"], "ranking.rank"),
            percentile=_finite_number(value["percentile"], "ranking.percentile"),
            peer_group_id=_nonempty_text(value["peer_group_id"], "ranking.peer_group_id"),
        )
        item.validate()
        return item

    def validate(self) -> None:
        _nonempty_text(self.ranking_method, "ranking.ranking_method")
        eligible = _positive_integer(self.eligible_count, "ranking.eligible_count")
        rank = _positive_integer(self.rank, "ranking.rank")
        percentile = _finite_number(self.percentile, "ranking.percentile")
        _nonempty_text(self.peer_group_id, "ranking.peer_group_id")
        if rank > eligible:
            raise ExactAsOfSnapshotError(
                f"ranking.rank exceeds eligible_count: {rank} > {eligible}",
                "RANK_OUT_OF_RANGE",
            )
        if percentile < 0.0 or percentile > 100.0:
            raise ExactAsOfSnapshotError(
                "ranking.percentile must be within 0..100", "PERCENTILE_OUT_OF_RANGE"
            )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "ranking_method": self.ranking_method,
            "eligible_count": self.eligible_count,
            "rank": self.rank,
            "percentile": float(self.percentile),
            "peer_group_id": self.peer_group_id,
        }


@dataclass(frozen=True)
class SnapshotRow:
    symbol: str
    feature_id: str
    value_type: str
    value: Any
    validity: str
    provenance: FeatureProvenance
    ranking: RankingEvidence | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SnapshotRow":
        _strict_keys(
            value,
            required=frozenset(
                {"symbol", "feature_id", "value_type", "value", "validity", "provenance"}
            ),
            optional=frozenset({"ranking"}),
            label="row",
        )
        ranking_raw = value.get("ranking")
        item = cls(
            symbol=_nonempty_text(value["symbol"], "row.symbol"),
            feature_id=_nonempty_text(value["feature_id"], "row.feature_id"),
            value_type=_nonempty_text(value["value_type"], "row.value_type").upper(),
            value=value["value"],
            validity=_nonempty_text(value["validity"], "row.validity").upper(),
            provenance=FeatureProvenance.from_dict(value["provenance"]),
            ranking=None if ranking_raw is None else RankingEvidence.from_dict(ranking_raw),
        )
        item.validate()
        return item

    def validate(self) -> None:
        _nonempty_text(self.symbol, "row.symbol")
        _nonempty_text(self.feature_id, "row.feature_id")
        value_type = _nonempty_text(self.value_type, "row.value_type").upper()
        validity = _nonempty_text(self.validity, "row.validity").upper()
        if value_type not in VALUE_TYPES:
            raise ExactAsOfSnapshotError(
                f"unsupported row.value_type: {self.value_type}", "BAD_VALUE_TYPE"
            )
        if validity not in VALIDITY_STATES:
            raise ExactAsOfSnapshotError(
                f"unsupported row.validity: {self.validity}", "BAD_VALIDITY"
            )
        if not isinstance(self.provenance, FeatureProvenance):
            raise ExactAsOfSnapshotError(
                "row.provenance must be FeatureProvenance", "BAD_PROVENANCE"
            )
        self.provenance.validate()
        if self.ranking is not None and not isinstance(self.ranking, RankingEvidence):
            raise ExactAsOfSnapshotError(
                "row.ranking must be RankingEvidence", "BAD_RANKING"
            )

        if validity != "VALID":
            if self.value is not None:
                raise ExactAsOfSnapshotError(
                    "non-VALID row value must remain None; default synthesis is forbidden",
                    "INVALID_ROW_HAS_VALUE",
                )
            if self.ranking is not None:
                raise ExactAsOfSnapshotError(
                    "non-VALID row cannot carry ranking evidence", "INVALID_ROW_HAS_RANK"
                )
            return

        if self.value is None:
            raise ExactAsOfSnapshotError(
                "VALID row requires an explicit value", "VALID_ROW_MISSING_VALUE"
            )
        if value_type == "NUMBER":
            _finite_number(self.value, "row.value")
        elif value_type == "BOOLEAN":
            if not isinstance(self.value, bool):
                raise ExactAsOfSnapshotError(
                    "BOOLEAN row.value must be bool", "BAD_BOOLEAN_VALUE"
                )
        elif value_type == "STRING":
            if not isinstance(self.value, str):
                raise ExactAsOfSnapshotError(
                    "STRING row.value must be str", "BAD_STRING_VALUE"
                )
        if self.ranking is not None:
            self.ranking.validate()

    @property
    def identity(self) -> tuple[str, str, str]:
        peer_group = "" if self.ranking is None else self.ranking.peer_group_id
        return (self.symbol, self.feature_id, peer_group)

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "symbol": self.symbol,
            "feature_id": self.feature_id,
            "value_type": self.value_type,
            "value": float(self.value) if self.value_type == "NUMBER" and self.value is not None else self.value,
            "validity": self.validity,
            "provenance": self.provenance.public_dict(),
            "ranking": None if self.ranking is None else self.ranking.public_dict(),
        }


@dataclass(frozen=True)
class PointInTimeSnapshot:
    snapshot_id: str
    as_of: str
    knowledge_cutoff: str
    universe_id: str
    feature_version: str
    source_refs: tuple[str, ...]
    rows: tuple[SnapshotRow, ...]
    schema_version: str = AXIS2_SNAPSHOT_SCHEMA

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PointInTimeSnapshot":
        _strict_keys(
            value,
            required=frozenset(
                {
                    "schema_version",
                    "snapshot_id",
                    "as_of",
                    "knowledge_cutoff",
                    "universe_id",
                    "feature_version",
                    "source_refs",
                    "rows",
                }
            ),
            optional=frozenset({"snapshot_hash"}),
            label="snapshot",
        )
        if value["schema_version"] != AXIS2_SNAPSHOT_SCHEMA:
            raise ExactAsOfSnapshotError(
                f"unsupported snapshot schema: {value['schema_version']}", "BAD_SCHEMA"
            )
        if not isinstance(value["source_refs"], list):
            raise ExactAsOfSnapshotError("snapshot.source_refs must be a list", "BAD_SOURCE_REFS")
        if not isinstance(value["rows"], list):
            raise ExactAsOfSnapshotError("snapshot.rows must be a list", "BAD_ROWS")
        item = cls(
            snapshot_id=_nonempty_text(value["snapshot_id"], "snapshot.snapshot_id"),
            as_of=_timestamp(value["as_of"], "snapshot.as_of"),
            knowledge_cutoff=_timestamp(
                value["knowledge_cutoff"], "snapshot.knowledge_cutoff"
            ),
            universe_id=_nonempty_text(value["universe_id"], "snapshot.universe_id"),
            feature_version=_nonempty_text(
                value["feature_version"], "snapshot.feature_version"
            ),
            source_refs=tuple(
                _nonempty_text(item, "snapshot.source_refs[]") for item in value["source_refs"]
            ),
            rows=tuple(SnapshotRow.from_dict(row) for row in value["rows"]),
            schema_version=AXIS2_SNAPSHOT_SCHEMA,
        )
        item.validate()
        supplied_hash = value.get("snapshot_hash")
        if supplied_hash is not None and supplied_hash != item.snapshot_hash:
            raise ExactAsOfSnapshotError(
                "snapshot_hash does not match canonical snapshot", "SNAPSHOT_HASH_MISMATCH"
            )
        return item

    def validate(self) -> None:
        if self.schema_version != AXIS2_SNAPSHOT_SCHEMA:
            raise ExactAsOfSnapshotError(
                f"unsupported snapshot schema: {self.schema_version}", "BAD_SCHEMA"
            )
        _nonempty_text(self.snapshot_id, "snapshot.snapshot_id")
        as_of = _timestamp(self.as_of, "snapshot.as_of")
        cutoff = _timestamp(self.knowledge_cutoff, "snapshot.knowledge_cutoff")
        _nonempty_text(self.universe_id, "snapshot.universe_id")
        _nonempty_text(self.feature_version, "snapshot.feature_version")
        if cutoff > as_of:
            raise ExactAsOfSnapshotError(
                "knowledge_cutoff cannot be after snapshot as_of", "FUTURE_KNOWLEDGE_CUTOFF"
            )
        if not isinstance(self.source_refs, tuple) or not self.source_refs:
            raise ExactAsOfSnapshotError(
                "snapshot.source_refs must be a non-empty immutable tuple", "BAD_SOURCE_REFS"
            )
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ExactAsOfSnapshotError("duplicate source_refs", "DUPLICATE_SOURCE_REF")
        for source_ref in self.source_refs:
            _nonempty_text(source_ref, "snapshot.source_refs[]")
        if not isinstance(self.rows, tuple):
            raise ExactAsOfSnapshotError(
                "snapshot.rows must be an immutable tuple", "BAD_ROWS"
            )

        identities: set[tuple[str, str, str]] = set()
        rank_group_contracts: dict[tuple[str, str], tuple[str, int]] = {}
        for row in self.rows:
            if not isinstance(row, SnapshotRow):
                raise ExactAsOfSnapshotError("snapshot.rows must contain SnapshotRow", "BAD_ROW")
            row.validate()
            if row.identity in identities:
                raise ExactAsOfSnapshotError(
                    f"duplicate snapshot row identity: {row.identity}", "DUPLICATE_ROW"
                )
            identities.add(row.identity)
            if row.provenance.source_ref not in self.source_refs:
                raise ExactAsOfSnapshotError(
                    f"row source_ref not declared by snapshot: {row.provenance.source_ref}",
                    "UNDECLARED_SOURCE_REF",
                )
            if row.provenance.knowledge_cutoff != cutoff:
                raise ExactAsOfSnapshotError(
                    "mixed knowledge_cutoff values are forbidden", "MIXED_KNOWLEDGE_CUTOFF"
                )
            if row.provenance.formula_version != self.feature_version:
                raise ExactAsOfSnapshotError(
                    "mixed formula versions are forbidden", "MIXED_FORMULA_VERSION"
                )
            if row.provenance.observed_as_of > cutoff:
                raise ExactAsOfSnapshotError(
                    "future observation relative to snapshot cutoff", "FUTURE_OBSERVATION"
                )
            if row.ranking is not None:
                key = (row.feature_id, row.ranking.peer_group_id)
                contract = (row.ranking.ranking_method, row.ranking.eligible_count)
                existing = rank_group_contracts.setdefault(key, contract)
                if existing != contract:
                    raise ExactAsOfSnapshotError(
                        f"mixed ranking contract within peer group: {key}",
                        "MIXED_RANKING_CONTRACT",
                    )

    def canonical_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "knowledge_cutoff": self.knowledge_cutoff,
            "universe_id": self.universe_id,
            "feature_version": self.feature_version,
            "source_refs": list(self.source_refs),
            "rows": [row.public_dict() for row in self.rows],
        }

    @property
    def snapshot_hash(self) -> str:
        canonical = json.dumps(
            self.canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "snapshot_hash": self.snapshot_hash}

    def require_exact(
        self,
        *,
        as_of: str,
        knowledge_cutoff: str | None = None,
    ) -> "PointInTimeSnapshot":
        """Return this snapshot only for an exact timestamp match.

        This method intentionally has no nearest/previous/fill-forward mode.
        """
        requested_as_of = _timestamp(as_of, "request.as_of")
        if requested_as_of != self.as_of:
            raise ExactAsOfSnapshotError(
                f"exact as_of snapshot not available: {requested_as_of}", "AS_OF_NOT_EXACT"
            )
        if knowledge_cutoff is not None:
            requested_cutoff = _timestamp(knowledge_cutoff, "request.knowledge_cutoff")
            if requested_cutoff != self.knowledge_cutoff:
                raise ExactAsOfSnapshotError(
                    f"exact knowledge_cutoff snapshot not available: {requested_cutoff}",
                    "CUTOFF_NOT_EXACT",
                )
        return self

    def row(
        self,
        symbol: str,
        feature_id: str,
        *,
        peer_group_id: str | None = None,
        require_valid: bool = True,
    ) -> SnapshotRow:
        symbol_name = _nonempty_text(symbol, "row lookup symbol")
        feature_name = _nonempty_text(feature_id, "row lookup feature_id")
        matches = [
            item
            for item in self.rows
            if item.symbol == symbol_name
            and item.feature_id == feature_name
            and (
                peer_group_id is None
                or (item.ranking is not None and item.ranking.peer_group_id == peer_group_id)
            )
        ]
        if not matches:
            raise ExactAsOfSnapshotError(
                f"snapshot row not found: {symbol_name}/{feature_name}", "ROW_NOT_FOUND"
            )
        if len(matches) != 1:
            raise ExactAsOfSnapshotError(
                f"snapshot row lookup is ambiguous: {symbol_name}/{feature_name}",
                "AMBIGUOUS_ROW",
            )
        item = matches[0]
        if require_valid and item.validity != "VALID":
            raise ExactAsOfSnapshotError(
                f"snapshot row is not valid: {symbol_name}/{feature_name} ({item.validity})",
                "ROW_NOT_VALID",
            )
        return item
