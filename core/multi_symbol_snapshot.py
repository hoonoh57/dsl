"""Immutable point-in-time snapshots for observation-only multi-symbol analysis.

MSA1 is the policy-aligned Add-on seam between already-evaluated single-
instrument tactics and later cross-sectional research.  It never calls DSL,
Backtest, Broker, providers, network or database code.  It consumes only
explicit immutable snapshots and returns descriptive multi-axis evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


SNAPSHOT_SCHEMA_VERSION = "instrument_signal_snapshot/v1"
UNIVERSE_SCHEMA_VERSION = "multi_symbol_snapshot_universe/v1"
POLICY_SCHEMA_VERSION = "multi_symbol_snapshot_policy/v1"
ANALYSIS_SCHEMA_VERSION = "multi_symbol_snapshot_analysis/v1"
ANALYSIS_POLICY = "OBSERVATION_ONLY_PER_AXIS_LEADERBOARDS_AND_PARETO_NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY"
CAUSALITY_POLICY = "POINT_IN_TIME_ONLY"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"multi-symbol snapshot time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("multi-symbol evidence에 NaN/Infinity를 사용할 수 없습니다.")
        return value
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return number


@dataclass(frozen=True)
class InstrumentSignalSnapshot:
    """One causal, immutable single-instrument export at one exact timestamp."""

    symbol: str
    as_of: str
    knowledge_cutoff: str
    candidate_hash: str
    family_id: str
    generation_hash: str
    tactic_trigger: bool
    hard_guards_pass: bool
    locally_admissible: bool
    comparison_metrics: Mapping[str, float]
    source: str
    evidence_hash: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.symbol, "snapshot symbol")
        as_of = _time_key(self.as_of)
        cutoff = _time_key(self.knowledge_cutoff)
        if as_of != cutoff:
            raise ValueError("MSA1 snapshot은 exact as_of == knowledge_cutoff를 요구합니다.")
        _text(self.candidate_hash, "snapshot candidate_hash")
        _text(self.family_id, "snapshot family_id")
        _text(self.generation_hash, "snapshot generation_hash")
        _text(self.source, "snapshot source")
        _text(self.evidence_hash, "snapshot evidence_hash")
        if type(self.tactic_trigger) is not bool:
            raise ValueError("snapshot tactic_trigger는 bool이어야 합니다.")
        if type(self.hard_guards_pass) is not bool:
            raise ValueError("snapshot hard_guards_pass는 bool이어야 합니다.")
        if type(self.locally_admissible) is not bool:
            raise ValueError("snapshot locally_admissible는 bool이어야 합니다.")
        if not isinstance(self.comparison_metrics, Mapping):
            raise ValueError("snapshot comparison_metrics는 Mapping이어야 합니다.")
        if not self.comparison_metrics:
            raise ValueError("snapshot comparison_metrics가 비어 있습니다.")
        normalized = {}
        for raw_key, raw_value in self.comparison_metrics.items():
            key = _text(raw_key, "snapshot comparison metric key")
            if key in normalized:
                raise ValueError(f"snapshot comparison metric이 중복됩니다: {key}")
            normalized[key] = _finite_number(raw_value, f"snapshot metric {key}")
        _json_safe(dict(self.metadata))

    @property
    def snapshot_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": SNAPSHOT_SCHEMA_VERSION,
                "causality_policy": CAUSALITY_POLICY,
                "symbol": str(self.symbol).strip(),
                "as_of": _time_key(self.as_of),
                "knowledge_cutoff": _time_key(self.knowledge_cutoff),
                "candidate_hash": str(self.candidate_hash).strip(),
                "family_id": str(self.family_id).strip(),
                "generation_hash": str(self.generation_hash).strip(),
                "tactic_trigger": bool(self.tactic_trigger),
                "hard_guards_pass": bool(self.hard_guards_pass),
                "locally_admissible": bool(self.locally_admissible),
                "comparison_metrics": {
                    str(key): _finite_number(value, f"snapshot metric {key}")
                    for key, value in sorted(self.comparison_metrics.items(), key=lambda item: str(item[0]))
                },
                "source": str(self.source).strip(),
                "evidence_hash": str(self.evidence_hash).strip(),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": SNAPSHOT_SCHEMA_VERSION,
            "causality_policy": CAUSALITY_POLICY,
            "symbol": str(self.symbol).strip(),
            "as_of": _time_key(self.as_of),
            "knowledge_cutoff": _time_key(self.knowledge_cutoff),
            "candidate_hash": str(self.candidate_hash).strip(),
            "family_id": str(self.family_id).strip(),
            "generation_hash": str(self.generation_hash).strip(),
            "tactic_trigger": bool(self.tactic_trigger),
            "hard_guards_pass": bool(self.hard_guards_pass),
            "locally_admissible": bool(self.locally_admissible),
            "comparison_metrics": {
                str(key): _finite_number(value, f"snapshot metric {key}")
                for key, value in sorted(self.comparison_metrics.items(), key=lambda item: str(item[0]))
            },
            "source": str(self.source).strip(),
            "evidence_hash": str(self.evidence_hash).strip(),
            "metadata": dict(self.metadata),
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass(frozen=True)
class SnapshotUniverse:
    """Explicit opportunity set; the analyzer never discovers symbols."""

    universe_id: str
    symbols: tuple[str, ...]
    as_of: str
    knowledge_cutoff: str
    source_authority: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.universe_id, "snapshot universe_id")
        if not self.symbols:
            raise ValueError("snapshot universe symbols가 비어 있습니다.")
        normalized = tuple(_text(symbol, "snapshot universe symbol") for symbol in self.symbols)
        if len(set(normalized)) != len(normalized):
            raise ValueError("snapshot universe symbols에 중복이 있습니다.")
        if _time_key(self.as_of) != _time_key(self.knowledge_cutoff):
            raise ValueError("MSA1 universe는 exact as_of == knowledge_cutoff를 요구합니다.")
        _text(self.source_authority, "snapshot universe source_authority")
        _json_safe(dict(self.metadata))

    @property
    def universe_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": UNIVERSE_SCHEMA_VERSION,
                "universe_id": str(self.universe_id).strip(),
                "symbols": tuple(str(item).strip() for item in self.symbols),
                "as_of": _time_key(self.as_of),
                "knowledge_cutoff": _time_key(self.knowledge_cutoff),
                "source_authority": str(self.source_authority).strip(),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": UNIVERSE_SCHEMA_VERSION,
            "universe_id": str(self.universe_id).strip(),
            "symbols": tuple(str(item).strip() for item in self.symbols),
            "as_of": _time_key(self.as_of),
            "knowledge_cutoff": _time_key(self.knowledge_cutoff),
            "source_authority": str(self.source_authority).strip(),
            "metadata": dict(self.metadata),
            "universe_hash": self.universe_hash,
        }


@dataclass(frozen=True)
class SnapshotComparisonAxis:
    metric_id: str
    direction: str = "MAX"

    DIRECTIONS = {"MAX", "MIN"}

    def validate(self) -> None:
        _text(self.metric_id, "snapshot comparison metric_id")
        if str(self.direction).strip().upper() not in self.DIRECTIONS:
            raise ValueError("snapshot comparison direction은 MAX 또는 MIN이어야 합니다.")

    def public_dict(self) -> dict[str, str]:
        self.validate()
        return {
            "metric_id": str(self.metric_id).strip(),
            "direction": str(self.direction).strip().upper(),
        }


@dataclass(frozen=True)
class SnapshotAnalysisPolicy:
    """Explicit multi-axis observation policy; it has no slot/allocation authority."""

    policy_id: str
    policy_version: str
    axes: tuple[SnapshotComparisonAxis, ...]
    require_tactic_trigger: bool = True
    require_hard_guards: bool = True
    require_local_admissibility: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.policy_id, "snapshot analysis policy_id")
        _text(self.policy_version, "snapshot analysis policy_version")
        if not self.axes:
            raise ValueError("snapshot analysis axes가 비어 있습니다.")
        metric_ids = []
        for axis in self.axes:
            if not isinstance(axis, SnapshotComparisonAxis):
                raise ValueError("snapshot analysis axis는 SnapshotComparisonAxis여야 합니다.")
            axis.validate()
            metric_ids.append(str(axis.metric_id).strip())
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("snapshot analysis metric axis에 중복이 있습니다.")
        for name in ("require_tactic_trigger", "require_hard_guards", "require_local_admissibility"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name}는 bool이어야 합니다.")
        _json_safe(dict(self.metadata))

    @property
    def policy_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": POLICY_SCHEMA_VERSION,
                "analysis_policy": ANALYSIS_POLICY,
                "policy_id": str(self.policy_id).strip(),
                "policy_version": str(self.policy_version).strip(),
                "axes": tuple(axis.public_dict() for axis in self.axes),
                "require_tactic_trigger": bool(self.require_tactic_trigger),
                "require_hard_guards": bool(self.require_hard_guards),
                "require_local_admissibility": bool(self.require_local_admissibility),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": POLICY_SCHEMA_VERSION,
            "analysis_policy": ANALYSIS_POLICY,
            "policy_id": str(self.policy_id).strip(),
            "policy_version": str(self.policy_version).strip(),
            "axes": tuple(axis.public_dict() for axis in self.axes),
            "require_tactic_trigger": bool(self.require_tactic_trigger),
            "require_hard_guards": bool(self.require_hard_guards),
            "require_local_admissibility": bool(self.require_local_admissibility),
            "metadata": dict(self.metadata),
            "policy_hash": self.policy_hash,
        }


class MultiSymbolSnapshotAnalyzer:
    """Read-only cross-sectional evidence over an explicit snapshot universe."""

    @staticmethod
    def _comparison_reasons(snapshot: InstrumentSignalSnapshot, policy: SnapshotAnalysisPolicy) -> tuple[str, ...]:
        reasons = []
        if policy.require_tactic_trigger and not snapshot.tactic_trigger:
            reasons.append("TACTIC_NOT_TRIGGERED")
        if policy.require_hard_guards and not snapshot.hard_guards_pass:
            reasons.append("HARD_GUARD_FAILED")
        if policy.require_local_admissibility and not snapshot.locally_admissible:
            reasons.append("LOCAL_NOT_ADMISSIBLE")
        return tuple(reasons)

    @staticmethod
    def _dominates(left: InstrumentSignalSnapshot, right: InstrumentSignalSnapshot, policy: SnapshotAnalysisPolicy) -> bool:
        at_least_as_good = True
        strictly_better = False
        for axis in policy.axes:
            metric = str(axis.metric_id).strip()
            lvalue = _finite_number(left.comparison_metrics[metric], metric)
            rvalue = _finite_number(right.comparison_metrics[metric], metric)
            if str(axis.direction).strip().upper() == "MAX":
                if lvalue < rvalue:
                    at_least_as_good = False
                    break
                if lvalue > rvalue:
                    strictly_better = True
            else:
                if lvalue > rvalue:
                    at_least_as_good = False
                    break
                if lvalue < rvalue:
                    strictly_better = True
        return at_least_as_good and strictly_better

    @classmethod
    def analyze(
        cls,
        *,
        universe: SnapshotUniverse,
        snapshots: Sequence[InstrumentSignalSnapshot],
        policy: SnapshotAnalysisPolicy,
    ) -> dict[str, Any]:
        universe.validate()
        policy.validate()
        items = tuple(snapshots)
        if not items:
            raise ValueError("multi-symbol snapshots가 비어 있습니다.")
        by_symbol: dict[str, InstrumentSignalSnapshot] = {}
        target_time = _time_key(universe.as_of)
        required_metrics = tuple(str(axis.metric_id).strip() for axis in policy.axes)
        for snapshot in items:
            if not isinstance(snapshot, InstrumentSignalSnapshot):
                raise ValueError("multi-symbol snapshot item은 InstrumentSignalSnapshot이어야 합니다.")
            snapshot.validate()
            symbol = str(snapshot.symbol).strip()
            if symbol in by_symbol:
                raise ValueError(f"multi-symbol snapshot symbol이 중복됩니다: {symbol}")
            if _time_key(snapshot.as_of) != target_time or _time_key(snapshot.knowledge_cutoff) != target_time:
                raise ValueError(f"snapshot timestamp가 universe exact time과 다릅니다: {symbol}")
            missing_metrics = [metric for metric in required_metrics if metric not in snapshot.comparison_metrics]
            if missing_metrics:
                raise ValueError(f"snapshot comparison metric이 누락되었습니다: {symbol} {missing_metrics}")
            by_symbol[symbol] = snapshot

        universe_symbols = tuple(str(symbol).strip() for symbol in universe.symbols)
        if set(by_symbol) != set(universe_symbols):
            missing = sorted(set(universe_symbols) - set(by_symbol))
            extra = sorted(set(by_symbol) - set(universe_symbols))
            raise ValueError(f"snapshot universe membership 불일치: missing={missing}, extra={extra}")

        ordered = tuple(by_symbol[symbol] for symbol in universe_symbols)
        rows = []
        comparable = []
        for snapshot in ordered:
            reasons = cls._comparison_reasons(snapshot, policy)
            comparison_eligible = not reasons
            if comparison_eligible:
                comparable.append(snapshot)
            rows.append(
                {
                    "symbol": str(snapshot.symbol).strip(),
                    "snapshot_hash": snapshot.snapshot_hash,
                    "candidate_hash": str(snapshot.candidate_hash).strip(),
                    "family_id": str(snapshot.family_id).strip(),
                    "generation_hash": str(snapshot.generation_hash).strip(),
                    "tactic_trigger": bool(snapshot.tactic_trigger),
                    "hard_guards_pass": bool(snapshot.hard_guards_pass),
                    "locally_admissible": bool(snapshot.locally_admissible),
                    "comparison_eligible": comparison_eligible,
                    "comparison_reasons": reasons,
                    "comparison_metrics": {
                        metric: _finite_number(snapshot.comparison_metrics[metric], metric)
                        for metric in required_metrics
                    },
                }
            )

        leaderboards: dict[str, tuple[dict[str, Any], ...]] = {}
        for axis in policy.axes:
            metric = str(axis.metric_id).strip()
            reverse = str(axis.direction).strip().upper() == "MAX"
            if reverse:
                ranked = sorted(
                    comparable,
                    key=lambda item: (-_finite_number(item.comparison_metrics[metric], metric), str(item.symbol).strip()),
                )
            else:
                ranked = sorted(
                    comparable,
                    key=lambda item: (_finite_number(item.comparison_metrics[metric], metric), str(item.symbol).strip()),
                )
            leaderboards[metric] = tuple(
                {
                    "rank": index + 1,
                    "symbol": str(snapshot.symbol).strip(),
                    "value": _finite_number(snapshot.comparison_metrics[metric], metric),
                    "direction": str(axis.direction).strip().upper(),
                    "snapshot_hash": snapshot.snapshot_hash,
                }
                for index, snapshot in enumerate(ranked)
            )

        pareto = []
        for candidate in comparable:
            dominated = any(
                other is not candidate and cls._dominates(other, candidate, policy)
                for other in comparable
            )
            if not dominated:
                pareto.append(str(candidate.symbol).strip())
        pareto_symbols = tuple(sorted(pareto))

        identity = {
            "schema": ANALYSIS_SCHEMA_VERSION,
            "analysis_policy": ANALYSIS_POLICY,
            "universe_hash": universe.universe_hash,
            "policy_hash": policy.policy_hash,
            "input_snapshot_hashes": tuple(snapshot.snapshot_hash for snapshot in ordered),
            "rows": rows,
            "leaderboards": leaderboards,
            "pareto_symbols": pareto_symbols,
        }
        return {
            "schema": ANALYSIS_SCHEMA_VERSION,
            "mode": "OBSERVATION_ONLY",
            "analysis_policy": ANALYSIS_POLICY,
            "operational_authority": False,
            "universe": universe.public_dict(),
            "policy": policy.public_dict(),
            "input_snapshot_hashes": tuple(snapshot.snapshot_hash for snapshot in ordered),
            "rows": tuple(rows),
            "leaderboards": leaderboards,
            "pareto_symbols": pareto_symbols,
            "comparison_eligible_symbols": tuple(
                str(snapshot.symbol).strip() for snapshot in comparable
            ),
            "result_hash": _stable_hash(identity),
        }
