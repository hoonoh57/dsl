"""Bounded observation-only leader/follower/breadth evidence over MSA1 snapshots.

MSA2 consumes only exact immutable InstrumentSignalSnapshot points.  It does not
run DSL, Backtest, Broker, providers, universe discovery, allocation or entry
gating.  Leader/follower labels are descriptive cross-sectional evidence only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import mean
from typing import Any, Mapping, Sequence

from core.multi_symbol_snapshot import (
    InstrumentSignalSnapshot,
    MultiSymbolSnapshotAnalyzer,
    SnapshotAnalysisPolicy,
    SnapshotComparisonAxis,
    SnapshotUniverse,
)


SCHEMA_VERSION = "multi_symbol_group_evidence/v1"
POLICY_SCHEMA_VERSION = "multi_symbol_group_evidence_policy/v1"
ANALYSIS_POLICY = (
    "OBSERVATION_ONLY_BOUNDED_STATIC_UNIVERSE_LEADER_FOLLOWER_BREADTH_"
    "NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY"
)
TOPOLOGY_POLICY = "STATIC_EXPLICIT_UNIVERSE_EXACT_CHRONOLOGICAL_POINTS"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"MSA2 time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("MSA2 evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


@dataclass(frozen=True)
class GroupEvidencePolicy:
    """Explicit bounded policy for descriptive group evidence."""

    policy_id: str
    policy_version: str
    metric_id: str
    direction: str = "MAX"
    favorable_threshold: float = 0.0
    leader_count: int = 1
    lookback_points: int = 3
    max_symbols: int = 64
    max_points: int = 256
    require_tactic_trigger: bool = True
    require_hard_guards: bool = True
    require_local_admissibility: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.policy_id, "MSA2 policy_id")
        _text(self.policy_version, "MSA2 policy_version")
        _text(self.metric_id, "MSA2 metric_id")
        if str(self.direction).strip().upper() not in {"MAX", "MIN"}:
            raise ValueError("MSA2 direction은 MAX 또는 MIN이어야 합니다.")
        _finite(self.favorable_threshold, "MSA2 favorable_threshold")
        for name in ("leader_count", "lookback_points", "max_symbols", "max_points"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"MSA2 {name}는 1 이상의 int여야 합니다.")
        if self.lookback_points < 2:
            raise ValueError("MSA2 lookback_points는 2 이상이어야 합니다.")
        if self.max_points < self.lookback_points:
            raise ValueError("MSA2 max_points는 lookback_points 이상이어야 합니다.")
        if self.leader_count > self.max_symbols:
            raise ValueError("MSA2 leader_count는 max_symbols 이하여야 합니다.")
        for name in ("require_tactic_trigger", "require_hard_guards", "require_local_admissibility"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"MSA2 {name}는 bool이어야 합니다.")
        _json_safe(dict(self.metadata))

    @property
    def policy_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": POLICY_SCHEMA_VERSION,
                "analysis_policy": ANALYSIS_POLICY,
                "topology_policy": TOPOLOGY_POLICY,
                "policy_id": str(self.policy_id).strip(),
                "policy_version": str(self.policy_version).strip(),
                "metric_id": str(self.metric_id).strip(),
                "direction": str(self.direction).strip().upper(),
                "favorable_threshold": _finite(self.favorable_threshold, "MSA2 favorable_threshold"),
                "leader_count": int(self.leader_count),
                "lookback_points": int(self.lookback_points),
                "max_symbols": int(self.max_symbols),
                "max_points": int(self.max_points),
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
            "topology_policy": TOPOLOGY_POLICY,
            "policy_id": str(self.policy_id).strip(),
            "policy_version": str(self.policy_version).strip(),
            "metric_id": str(self.metric_id).strip(),
            "direction": str(self.direction).strip().upper(),
            "favorable_threshold": _finite(self.favorable_threshold, "MSA2 favorable_threshold"),
            "leader_count": int(self.leader_count),
            "lookback_points": int(self.lookback_points),
            "max_symbols": int(self.max_symbols),
            "max_points": int(self.max_points),
            "require_tactic_trigger": bool(self.require_tactic_trigger),
            "require_hard_guards": bool(self.require_hard_guards),
            "require_local_admissibility": bool(self.require_local_admissibility),
            "metadata": dict(self.metadata),
            "policy_hash": self.policy_hash,
        }


@dataclass(frozen=True)
class GroupSnapshotPoint:
    """One exact explicit universe and its immutable MSA1 snapshots."""

    universe: SnapshotUniverse
    snapshots: tuple[InstrumentSignalSnapshot, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.universe, SnapshotUniverse):
            raise ValueError("MSA2 point universe는 SnapshotUniverse여야 합니다.")
        self.universe.validate()
        if not self.snapshots:
            raise ValueError("MSA2 point snapshots가 비어 있습니다.")
        target = _time_key(self.universe.as_of)
        by_symbol: dict[str, InstrumentSignalSnapshot] = {}
        for snapshot in self.snapshots:
            if not isinstance(snapshot, InstrumentSignalSnapshot):
                raise ValueError("MSA2 point item은 InstrumentSignalSnapshot이어야 합니다.")
            snapshot.validate()
            symbol = str(snapshot.symbol).strip()
            if symbol in by_symbol:
                raise ValueError(f"MSA2 point snapshot symbol이 중복됩니다: {symbol}")
            if _time_key(snapshot.as_of) != target or _time_key(snapshot.knowledge_cutoff) != target:
                raise ValueError(f"MSA2 point snapshot이 exact universe time과 다릅니다: {symbol}")
            by_symbol[symbol] = snapshot
        expected = tuple(str(symbol).strip() for symbol in self.universe.symbols)
        if set(by_symbol) != set(expected):
            missing = sorted(set(expected) - set(by_symbol))
            extra = sorted(set(by_symbol) - set(expected))
            raise ValueError(f"MSA2 point universe membership 불일치: missing={missing}, extra={extra}")
        _json_safe(dict(self.metadata))

    @property
    def point_hash(self) -> str:
        self.validate()
        by_symbol = {str(item.symbol).strip(): item for item in self.snapshots}
        ordered_hashes = tuple(by_symbol[str(symbol).strip()].snapshot_hash for symbol in self.universe.symbols)
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "universe_hash": self.universe.universe_hash,
                "input_snapshot_hashes": ordered_hashes,
                "metadata": dict(self.metadata),
            }
        )


class MultiSymbolGroupEvidenceAnalyzer:
    """Derive bounded descriptive group evidence from exact MSA1 points."""

    @staticmethod
    def _msa1_policy(policy: GroupEvidencePolicy) -> SnapshotAnalysisPolicy:
        return SnapshotAnalysisPolicy(
            policy_id=f"{str(policy.policy_id).strip()}::MSA1_AXIS",
            policy_version=str(policy.policy_version).strip(),
            axes=(SnapshotComparisonAxis(str(policy.metric_id).strip(), str(policy.direction).strip().upper()),),
            require_tactic_trigger=bool(policy.require_tactic_trigger),
            require_hard_guards=bool(policy.require_hard_guards),
            require_local_admissibility=bool(policy.require_local_admissibility),
            metadata={"consumer": "MSA2", "msa2_policy_hash": policy.policy_hash},
        )

    @staticmethod
    def _favorable(value: float, policy: GroupEvidencePolicy) -> bool:
        threshold = _finite(policy.favorable_threshold, "MSA2 favorable_threshold")
        if str(policy.direction).strip().upper() == "MAX":
            return value >= threshold
        return value <= threshold

    @classmethod
    def analyze(
        cls,
        *,
        points: Sequence[GroupSnapshotPoint],
        policy: GroupEvidencePolicy,
    ) -> dict[str, Any]:
        policy.validate()
        frozen = tuple(points)
        if len(frozen) < 2:
            raise ValueError("MSA2는 최소 2개 exact snapshot point가 필요합니다.")
        if len(frozen) > policy.max_points:
            raise ValueError("MSA2 snapshot point 수가 policy max_points를 초과합니다.")

        for point in frozen:
            if not isinstance(point, GroupSnapshotPoint):
                raise ValueError("MSA2 points는 GroupSnapshotPoint여야 합니다.")
            point.validate()

        times = tuple(_time_key(point.universe.as_of) for point in frozen)
        if len(set(times)) != len(times) or any(times[index] >= times[index + 1] for index in range(len(times) - 1)):
            raise ValueError("MSA2 point timestamp는 중복 없는 엄격 오름차순이어야 합니다.")

        first_universe = frozen[0].universe
        universe_id = str(first_universe.universe_id).strip()
        symbols = tuple(str(symbol).strip() for symbol in first_universe.symbols)
        source_authority = str(first_universe.source_authority).strip()
        if len(symbols) > policy.max_symbols:
            raise ValueError("MSA2 universe symbol 수가 policy max_symbols를 초과합니다.")
        if policy.leader_count >= len(symbols):
            raise ValueError("MSA2 leader_count는 universe symbol 수보다 작아야 follower evidence가 정의됩니다.")

        baseline_identity: dict[str, tuple[str, str, str]] = {}
        point_analyses = []
        msa1_policy = cls._msa1_policy(policy)
        metric_id = str(policy.metric_id).strip()

        for point in frozen:
            current_symbols = tuple(str(symbol).strip() for symbol in point.universe.symbols)
            if str(point.universe.universe_id).strip() != universe_id:
                raise ValueError("MSA2 frame 중 universe_id 변경은 허용되지 않습니다.")
            if current_symbols != symbols:
                raise ValueError("MSA2 frame 중 universe symbol topology 변경은 허용되지 않습니다.")
            if str(point.universe.source_authority).strip() != source_authority:
                raise ValueError("MSA2 frame 중 universe source_authority 변경은 허용되지 않습니다.")

            by_symbol = {str(snapshot.symbol).strip(): snapshot for snapshot in point.snapshots}
            for symbol in symbols:
                snapshot = by_symbol[symbol]
                identity = (
                    str(snapshot.candidate_hash).strip(),
                    str(snapshot.family_id).strip(),
                    str(snapshot.generation_hash).strip(),
                )
                previous = baseline_identity.get(symbol)
                if previous is None:
                    baseline_identity[symbol] = identity
                elif previous != identity:
                    raise ValueError(f"MSA2 frame 중 tactic identity drift가 발생했습니다: {symbol}")
                if metric_id not in snapshot.comparison_metrics:
                    raise ValueError(f"MSA2 metric이 snapshot에 없습니다: {symbol} {metric_id}")

            analysis = MultiSymbolSnapshotAnalyzer.analyze(
                universe=point.universe,
                snapshots=point.snapshots,
                policy=msa1_policy,
            )
            leaderboard = tuple(analysis["leaderboards"][metric_id])
            if len(leaderboard) < policy.leader_count:
                raise ValueError("MSA2 point에 leader_count를 충족할 comparison-eligible snapshot이 없습니다.")
            eligible_rows = tuple(row for row in analysis["rows"] if row["comparison_eligible"])
            favorable_count = sum(
                1
                for row in eligible_rows
                if cls._favorable(_finite(row["comparison_metrics"][metric_id], metric_id), policy)
            )
            point_analyses.append(
                {
                    "as_of": _time_key(point.universe.as_of),
                    "point_hash": point.point_hash,
                    "msa1_result_hash": analysis["result_hash"],
                    "comparison_eligible_count": len(eligible_rows),
                    "comparison_eligible_rate": len(eligible_rows) / len(symbols),
                    "favorable_count": favorable_count,
                    "favorable_breadth_rate": (favorable_count / len(eligible_rows)) if eligible_rows else 0.0,
                    "leader_symbols": tuple(row["symbol"] for row in leaderboard[: policy.leader_count]),
                    "leaderboard": leaderboard,
                }
            )

        latest = point_analyses[-1]
        latest_leaderboard = latest["leaderboard"]
        current_leaders = tuple(row["symbol"] for row in latest_leaderboard[: policy.leader_count])
        current_followers = tuple(row["symbol"] for row in latest_leaderboard[policy.leader_count :])
        leader_values = tuple(_finite(row["value"], metric_id) for row in latest_leaderboard[: policy.leader_count])
        follower_values = tuple(_finite(row["value"], metric_id) for row in latest_leaderboard[policy.leader_count :])
        leader_mean = float(mean(leader_values))
        follower_mean = float(mean(follower_values)) if follower_values else None
        if follower_mean is None:
            spread = None
        elif str(policy.direction).strip().upper() == "MAX":
            spread = leader_mean - follower_mean
        else:
            spread = follower_mean - leader_mean

        follower_favorable_count = sum(1 for value in follower_values if cls._favorable(value, policy))
        follower_favorable_rate = (
            follower_favorable_count / len(follower_values) if follower_values else None
        )

        lookback = tuple(point_analyses[-min(policy.lookback_points, len(point_analyses)) :])
        persistence = []
        for symbol in current_leaders:
            appearances = sum(1 for point in lookback if symbol in point["leader_symbols"])
            persistence.append(
                {
                    "symbol": symbol,
                    "leader_appearances": appearances,
                    "lookback_points": len(lookback),
                    "leader_persistence_rate": appearances / len(lookback),
                }
            )

        latest_summary = {
            "as_of": latest["as_of"],
            "metric_id": metric_id,
            "direction": str(policy.direction).strip().upper(),
            "favorable_threshold": _finite(policy.favorable_threshold, "MSA2 favorable_threshold"),
            "universe_symbols": len(symbols),
            "comparison_eligible_count": latest["comparison_eligible_count"],
            "comparison_eligible_rate": latest["comparison_eligible_rate"],
            "favorable_count": latest["favorable_count"],
            "favorable_breadth_rate": latest["favorable_breadth_rate"],
            "leader_symbols": current_leaders,
            "follower_symbols": current_followers,
            "leader_metric_mean": leader_mean,
            "follower_metric_mean": follower_mean,
            "leader_follower_spread": spread,
            "follower_favorable_rate": follower_favorable_rate,
            "leader_persistence": tuple(persistence),
        }

        identity = {
            "schema": SCHEMA_VERSION,
            "analysis_policy": ANALYSIS_POLICY,
            "topology_policy": TOPOLOGY_POLICY,
            "policy_hash": policy.policy_hash,
            "universe_id": universe_id,
            "symbols": symbols,
            "source_authority": source_authority,
            "point_hashes": tuple(point.point_hash for point in frozen),
            "point_evidence": tuple(point_analyses),
            "latest": latest_summary,
        }
        return {
            "schema": SCHEMA_VERSION,
            "mode": "OBSERVATION_ONLY",
            "analysis_policy": ANALYSIS_POLICY,
            "topology_policy": TOPOLOGY_POLICY,
            "operational_authority": False,
            "policy": policy.public_dict(),
            "universe_id": universe_id,
            "symbols": symbols,
            "source_authority": source_authority,
            "start_as_of": times[0],
            "end_as_of": times[-1],
            "point_count": len(frozen),
            "point_hashes": tuple(point.point_hash for point in frozen),
            "points": tuple(point_analyses),
            "latest": latest_summary,
            "result_hash": _stable_hash(identity),
        }
