"""Compare micro tactics on exactly the same frozen BattleCase set.

There is intentionally no hidden universal score.  The engine exposes metric
leaderboards and a Pareto frontier so a simpler/safer tactic can remain visible
instead of being buried by one arbitrary weighted objective.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "tactical_competition/v1"


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    number = float(value)
    if not math.isfinite(number):
        return default
    return number


def _candidate_row(profile: Mapping[str, Any]) -> dict:
    if str(profile.get("schema") or "") != "tactical_discovery/v1":
        raise ValueError("competition profile은 tactical_discovery/v1이어야 합니다.")
    candidate = dict(profile.get("candidate") or {})
    aggregate = dict(profile.get("aggregate") or {})
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    candidate_hash = str(candidate.get("candidate_hash") or "").strip()
    if not candidate_id or not candidate_hash:
        raise ValueError("competition profile candidate identity가 없습니다.")
    cases = int(aggregate.get("cases") or 0)
    if cases < 1:
        raise ValueError(f"{candidate_id}: aggregate cases가 비어 있습니다.")
    total_cost = _number(aggregate.get("total_cost"))
    return {
        "candidate_id": candidate_id,
        "candidate_hash": candidate_hash,
        "run_hash": str(profile.get("run_hash") or ""),
        "average_return_pct": _number(aggregate.get("average_return_pct")),
        "median_return_pct": _number(aggregate.get("median_return_pct")),
        "profitable_case_rate": _number(aggregate.get("profitable_case_rate")),
        "worst_mdd_pct": _number(aggregate.get("worst_mdd_pct")),
        "median_finite_profit_factor": _number(aggregate.get("median_finite_profit_factor")),
        "average_closed_trades_per_case": _number(aggregate.get("average_closed_trades_per_case")),
        "cost_per_case": total_cost / cases,
        "complexity_units": int(aggregate.get("complexity_units") or candidate.get("complexity_units") or 1),
        "top1_positive_return_concentration": (
            None
            if aggregate.get("top1_positive_return_concentration") is None
            else _number(aggregate.get("top1_positive_return_concentration"))
        ),
        "cases": cases,
    }


def _dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """Conservative Pareto dominance across the primary tactical axes."""

    maximize = ("average_return_pct", "profitable_case_rate")
    minimize = ("drawdown_risk", "cost_per_case", "complexity_units")
    l = dict(left)
    r = dict(right)
    l["drawdown_risk"] = abs(min(0.0, _number(l.get("worst_mdd_pct"))))
    r["drawdown_risk"] = abs(min(0.0, _number(r.get("worst_mdd_pct"))))

    no_worse = all(_number(l[key]) >= _number(r[key]) for key in maximize) and all(
        _number(l[key]) <= _number(r[key]) for key in minimize
    )
    strictly_better = any(_number(l[key]) > _number(r[key]) for key in maximize) or any(
        _number(l[key]) < _number(r[key]) for key in minimize
    )
    return bool(no_worse and strictly_better)


class TacticalCompetitionEngine:
    @classmethod
    def compare(cls, profiles: Sequence[Mapping[str, Any]]) -> dict:
        frozen = tuple(profiles)
        if len(frozen) < 2:
            raise ValueError("tactical competition에는 최소 2개 profile이 필요합니다.")
        case_sets = {str(profile.get("case_set_hash") or "") for profile in frozen}
        if "" in case_sets or len(case_sets) != 1:
            raise ValueError("모든 tactic은 동일한 frozen case_set_hash에서 비교되어야 합니다.")
        policies = {
            _stable_hash(dict(profile.get("context_policy") or {})) for profile in frozen
        }
        if len(policies) != 1:
            raise ValueError("모든 tactic은 동일한 context policy에서 비교되어야 합니다.")
        rows = [_candidate_row(profile) for profile in frozen]
        if len({row["candidate_hash"] for row in rows}) != len(rows):
            raise ValueError("동일 candidate가 competition에 중복되었습니다.")
        case_counts = {row["cases"] for row in rows}
        if len(case_counts) != 1:
            raise ValueError("동일 case_set_hash인데 aggregate case 수가 다릅니다.")

        dominated_by: dict[str, list[str]] = {row["candidate_hash"]: [] for row in rows}
        for left in rows:
            for right in rows:
                if left is right:
                    continue
                if _dominates(left, right):
                    dominated_by[right["candidate_hash"]].append(left["candidate_hash"])
        frontier = [
            row["candidate_hash"] for row in rows if not dominated_by[row["candidate_hash"]]
        ]

        leaderboard_specs = {
            "average_return_pct": True,
            "median_return_pct": True,
            "profitable_case_rate": True,
            "worst_mdd_pct": True,
            "median_finite_profit_factor": True,
            "cost_per_case": False,
            "average_closed_trades_per_case": False,
            "complexity_units": False,
        }
        leaderboards = {}
        for metric, descending in leaderboard_specs.items():
            ordered = sorted(
                rows,
                key=lambda row: (
                    -_number(row.get(metric)) if descending else _number(row.get(metric)),
                    row["candidate_id"],
                ),
            )
            leaderboards[metric] = [row["candidate_hash"] for row in ordered]

        comparison_identity = {
            "schema": SCHEMA_VERSION,
            "case_set_hash": next(iter(case_sets)),
            "profile_run_hashes": [str(profile.get("run_hash") or "") for profile in frozen],
            "candidate_hashes": [row["candidate_hash"] for row in rows],
            "frontier": frontier,
        }
        return {
            "schema": SCHEMA_VERSION,
            "case_set_hash": next(iter(case_sets)),
            "context_policy": dict(frozen[0].get("context_policy") or {}),
            "candidates": rows,
            "pareto_frontier": frontier,
            "dominated_by": dominated_by,
            "leaderboards": leaderboards,
            "comparison_hash": _stable_hash(comparison_identity),
            "selection_policy": "PARETO_NO_HIDDEN_UNIVERSAL_SCORE",
        }
