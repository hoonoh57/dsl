"""Bounded observation-only leader/follower relation evidence over MSA2 inputs.

LF1 turns exact chronological MSA1 snapshots into explicit leader persistence and
lagged follower-response evidence. It is deliberately analysis-only: it does not
publish parent context, rank for deployment, allocate capital, gate entries, or
submit/cancel Broker orders.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import mean
from typing import Any, Mapping, Sequence

from core.multi_symbol_group_evidence import (
    GroupEvidencePolicy,
    GroupSnapshotPoint,
    MultiSymbolGroupEvidenceAnalyzer,
)


SCHEMA_VERSION = "multi_symbol_leader_follower_relation/v1"
POLICY_SCHEMA_VERSION = "multi_symbol_leader_follower_relation_policy/v1"
ANALYSIS_POLICY = (
    "OBSERVATION_ONLY_EXPLICIT_LEADER_PERSISTENCE_LAGGED_FOLLOW_RATE_"
    "NO_HIDDEN_SCORE_NO_DEPLOYMENT_AUTHORITY"
)


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


def _rate(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{label}은 0~1 범위여야 합니다.")
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("LF1 evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


def _oriented_delta(previous: float, current: float, direction: str) -> float:
    if direction == "MAX":
        return current - previous
    return previous - current


def _snapshot_eligible(snapshot: Any, policy: GroupEvidencePolicy) -> bool:
    if policy.require_tactic_trigger and not bool(snapshot.tactic_trigger):
        return False
    if policy.require_hard_guards and not bool(snapshot.hard_guards_pass):
        return False
    if policy.require_local_admissibility and not bool(snapshot.locally_admissible):
        return False
    return True


@dataclass(frozen=True)
class LeaderFollowerRelationPolicy:
    policy_id: str
    policy_version: str
    leader_impulse_threshold: float
    follower_response_threshold: float
    max_lag_points: int = 2
    min_observable_impulses: int = 2
    min_follow_rate: float = 0.60
    min_leader_persistence_rate: float = 0.60
    min_leader_spread: float = 0.0
    max_symbols: int = 32
    max_points: int = 256
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.policy_id, "LF1 policy_id")
        _text(self.policy_version, "LF1 policy_version")
        if _finite(self.leader_impulse_threshold, "LF1 leader_impulse_threshold") <= 0.0:
            raise ValueError("LF1 leader_impulse_threshold는 0보다 커야 합니다.")
        if _finite(self.follower_response_threshold, "LF1 follower_response_threshold") <= 0.0:
            raise ValueError("LF1 follower_response_threshold는 0보다 커야 합니다.")
        if isinstance(self.max_lag_points, bool) or not isinstance(self.max_lag_points, int) or self.max_lag_points < 1:
            raise ValueError("LF1 max_lag_points는 1 이상의 int여야 합니다.")
        if isinstance(self.min_observable_impulses, bool) or not isinstance(self.min_observable_impulses, int) or self.min_observable_impulses < 1:
            raise ValueError("LF1 min_observable_impulses는 1 이상의 int여야 합니다.")
        _rate(self.min_follow_rate, "LF1 min_follow_rate")
        _rate(self.min_leader_persistence_rate, "LF1 min_leader_persistence_rate")
        if _finite(self.min_leader_spread, "LF1 min_leader_spread") < 0.0:
            raise ValueError("LF1 min_leader_spread는 0 이상이어야 합니다.")
        for name in ("max_symbols", "max_points"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise ValueError(f"LF1 {name}는 2 이상의 int여야 합니다.")
        if self.max_points < self.max_lag_points + 3:
            raise ValueError("LF1 max_points는 max_lag_points + 3 이상이어야 합니다.")
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
                "leader_impulse_threshold": _finite(self.leader_impulse_threshold, "LF1 leader_impulse_threshold"),
                "follower_response_threshold": _finite(self.follower_response_threshold, "LF1 follower_response_threshold"),
                "max_lag_points": int(self.max_lag_points),
                "min_observable_impulses": int(self.min_observable_impulses),
                "min_follow_rate": _rate(self.min_follow_rate, "LF1 min_follow_rate"),
                "min_leader_persistence_rate": _rate(self.min_leader_persistence_rate, "LF1 min_leader_persistence_rate"),
                "min_leader_spread": _finite(self.min_leader_spread, "LF1 min_leader_spread"),
                "max_symbols": int(self.max_symbols),
                "max_points": int(self.max_points),
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
            "leader_impulse_threshold": _finite(self.leader_impulse_threshold, "LF1 leader_impulse_threshold"),
            "follower_response_threshold": _finite(self.follower_response_threshold, "LF1 follower_response_threshold"),
            "max_lag_points": int(self.max_lag_points),
            "min_observable_impulses": int(self.min_observable_impulses),
            "min_follow_rate": _rate(self.min_follow_rate, "LF1 min_follow_rate"),
            "min_leader_persistence_rate": _rate(self.min_leader_persistence_rate, "LF1 min_leader_persistence_rate"),
            "min_leader_spread": _finite(self.min_leader_spread, "LF1 min_leader_spread"),
            "max_symbols": int(self.max_symbols),
            "max_points": int(self.max_points),
            "metadata": dict(self.metadata),
            "policy_hash": self.policy_hash,
        }


class MultiSymbolLeaderFollowerRelationAnalyzer:
    """Derive explicit one-leader / many-follower lag evidence with no hidden score."""

    @classmethod
    def analyze(
        cls,
        *,
        points: Sequence[GroupSnapshotPoint],
        group_policy: GroupEvidencePolicy,
        relation_policy: LeaderFollowerRelationPolicy,
    ) -> dict[str, Any]:
        group_policy.validate()
        relation_policy.validate()
        frozen = tuple(points)
        if len(frozen) < relation_policy.max_lag_points + 3:
            raise ValueError("LF1은 지연 추종을 관찰할 충분한 point가 필요합니다.")
        if len(frozen) > relation_policy.max_points:
            raise ValueError("LF1 point 수가 relation policy max_points를 초과합니다.")
        if group_policy.leader_count != 1:
            raise ValueError("LF1 v1은 명시적인 단일 대장주 leader_count=1만 허용합니다.")

        group = MultiSymbolGroupEvidenceAnalyzer.analyze(points=frozen, policy=group_policy)
        symbols = tuple(str(item).strip() for item in group["symbols"])
        if len(symbols) > relation_policy.max_symbols:
            raise ValueError("LF1 universe symbol 수가 relation policy max_symbols를 초과합니다.")

        metric_id = str(group_policy.metric_id).strip()
        direction = str(group_policy.direction).strip().upper()
        leader = str(group["latest"]["leader_symbols"][0]).strip()
        followers = tuple(str(item).strip() for item in group["latest"]["follower_symbols"])
        persistence_rows = {
            str(row["symbol"]).strip(): row for row in group["latest"]["leader_persistence"]
        }
        leader_persistence_rate = _rate(
            persistence_rows[leader]["leader_persistence_rate"],
            "LF1 leader_persistence_rate",
        )
        raw_spread = group["latest"]["leader_follower_spread"]
        leader_spread = None if raw_spread is None else _finite(raw_spread, "LF1 leader_spread")
        leader_role_qualified = (
            leader_persistence_rate >= relation_policy.min_leader_persistence_rate
            and leader_spread is not None
            and leader_spread >= relation_policy.min_leader_spread
        )

        by_point: list[dict[str, Any]] = []
        for point in frozen:
            point.validate()
            by_symbol = {str(item.symbol).strip(): item for item in point.snapshots}
            values = {}
            eligible = {}
            for symbol in symbols:
                snapshot = by_symbol[symbol]
                if metric_id not in snapshot.comparison_metrics:
                    raise ValueError(f"LF1 metric이 snapshot에 없습니다: {symbol} {metric_id}")
                values[symbol] = _finite(snapshot.comparison_metrics[metric_id], f"LF1 {symbol} {metric_id}")
                eligible[symbol] = _snapshot_eligible(snapshot, group_policy)
            by_point.append(
                {
                    "as_of": str(point.universe.as_of),
                    "point_hash": point.point_hash,
                    "values": values,
                    "eligible": eligible,
                }
            )

        leader_impulses: list[dict[str, Any]] = []
        censored_leader_impulse_count = 0
        for index in range(1, len(by_point)):
            previous = by_point[index - 1]
            current = by_point[index]
            if not (previous["eligible"][leader] and current["eligible"][leader]):
                continue
            delta = _oriented_delta(previous["values"][leader], current["values"][leader], direction)
            if delta < relation_policy.leader_impulse_threshold:
                continue
            if index + relation_policy.max_lag_points >= len(by_point):
                censored_leader_impulse_count += 1
                continue
            leader_impulses.append(
                {
                    "impulse_index": index,
                    "as_of": current["as_of"],
                    "oriented_delta": delta,
                }
            )

        pair_rows: list[dict[str, Any]] = []
        for follower in followers:
            observable = 0
            matches: list[dict[str, Any]] = []
            for impulse in leader_impulses:
                index = int(impulse["impulse_index"])
                candidate_transitions: list[tuple[int, float, str]] = []
                for lag in range(1, relation_policy.max_lag_points + 1):
                    response_index = index + lag
                    previous = by_point[response_index - 1]
                    current = by_point[response_index]
                    if not (previous["eligible"][follower] and current["eligible"][follower]):
                        continue
                    delta = _oriented_delta(
                        previous["values"][follower],
                        current["values"][follower],
                        direction,
                    )
                    candidate_transitions.append((lag, delta, current["as_of"]))
                if not candidate_transitions:
                    continue
                observable += 1
                matched = next(
                    (item for item in candidate_transitions if item[1] >= relation_policy.follower_response_threshold),
                    None,
                )
                if matched is not None:
                    matches.append(
                        {
                            "leader_impulse_as_of": impulse["as_of"],
                            "response_as_of": matched[2],
                            "lag_points": matched[0],
                            "oriented_delta": matched[1],
                        }
                    )

            follow_rate = (len(matches) / observable) if observable else None
            mean_lag_points = float(mean(item["lag_points"] for item in matches)) if matches else None
            mean_response_delta = float(mean(item["oriented_delta"] for item in matches)) if matches else None
            qualified = bool(
                leader_role_qualified
                and observable >= relation_policy.min_observable_impulses
                and follow_rate is not None
                and follow_rate >= relation_policy.min_follow_rate
            )
            pair_rows.append(
                {
                    "leader_symbol": leader,
                    "follower_symbol": follower,
                    "observable_impulse_count": observable,
                    "matched_response_count": len(matches),
                    "follow_rate": follow_rate,
                    "mean_lag_points": mean_lag_points,
                    "mean_response_oriented_delta": mean_response_delta,
                    "qualified": qualified,
                    "matches": tuple(matches),
                }
            )

        qualified_rows = tuple(row for row in pair_rows if row["qualified"])

        def follow_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
            return (-float(row["follow_rate"]), str(row["follower_symbol"]))

        def lag_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
            lag = row["mean_lag_points"]
            return (float("inf") if lag is None else float(lag), str(row["follower_symbol"]))

        latest_leaderboard = tuple(group["latest"].get("leader_symbols", ())) + tuple(group["latest"].get("follower_symbols", ()))
        latest_rank = {symbol: index for index, symbol in enumerate(latest_leaderboard)}
        by_symbol_latest = {str(row["symbol"]): row for row in group["points"][-1]["leaderboard"]}

        def current_metric_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
            symbol = str(row["follower_symbol"])
            value = _finite(by_symbol_latest[symbol]["value"], f"LF1 latest {metric_id}")
            oriented = value if direction == "MAX" else -value
            return (-oriented, latest_rank.get(symbol, 10**9), symbol)

        follow_rate_leaderboard = tuple(sorted(qualified_rows, key=follow_key))
        lag_leaderboard = tuple(sorted(qualified_rows, key=lag_key))
        current_metric_leaderboard = tuple(sorted(qualified_rows, key=current_metric_key))
        top_follow_rate_follower = (
            str(follow_rate_leaderboard[0]["follower_symbol"]) if follow_rate_leaderboard else None
        )

        public_pairs = tuple(pair_rows)
        identity = {
            "schema": SCHEMA_VERSION,
            "analysis_policy": ANALYSIS_POLICY,
            "group_result_hash": group["result_hash"],
            "group_policy_hash": group_policy.policy_hash,
            "relation_policy_hash": relation_policy.policy_hash,
            "universe_id": group["universe_id"],
            "symbols": symbols,
            "source_authority": group["source_authority"],
            "leader_symbol": leader,
            "leader_role_qualified": leader_role_qualified,
            "leader_persistence_rate": leader_persistence_rate,
            "leader_spread": leader_spread,
            "leader_impulses": tuple(leader_impulses),
            "censored_leader_impulse_count": censored_leader_impulse_count,
            "pairs": public_pairs,
            "follow_rate_order": tuple(row["follower_symbol"] for row in follow_rate_leaderboard),
            "lag_order": tuple(row["follower_symbol"] for row in lag_leaderboard),
            "current_metric_order": tuple(row["follower_symbol"] for row in current_metric_leaderboard),
        }
        return {
            "schema": SCHEMA_VERSION,
            "mode": "OBSERVATION_ONLY",
            "analysis_policy": ANALYSIS_POLICY,
            "operational_authority": False,
            "group_result_hash": group["result_hash"],
            "group_policy_hash": group_policy.policy_hash,
            "relation_policy": relation_policy.public_dict(),
            "universe_id": group["universe_id"],
            "symbols": symbols,
            "source_authority": group["source_authority"],
            "start_as_of": group["start_as_of"],
            "end_as_of": group["end_as_of"],
            "point_count": group["point_count"],
            "leader_symbol": leader,
            "leader_role_qualified": leader_role_qualified,
            "leader_persistence_rate": leader_persistence_rate,
            "leader_spread": leader_spread,
            "leader_impulse_count": len(leader_impulses),
            "censored_leader_impulse_count": censored_leader_impulse_count,
            "leader_impulses": tuple(leader_impulses),
            "pairs": public_pairs,
            "qualified_followers": tuple(row["follower_symbol"] for row in qualified_rows),
            "follow_rate_leaderboard": tuple(row["follower_symbol"] for row in follow_rate_leaderboard),
            "lag_leaderboard": tuple(row["follower_symbol"] for row in lag_leaderboard),
            "current_metric_leaderboard": tuple(row["follower_symbol"] for row in current_metric_leaderboard),
            "top_follow_rate_follower": top_follow_rate_follower,
            "selection_axis": "FOLLOW_RATE_ONLY_EXPLICIT_NO_HIDDEN_SCORE",
            "result_hash": _stable_hash(identity),
        }
