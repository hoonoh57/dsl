"""Failure analysis for evolving micro tactics.

The analyzer consumes immutable ``tactical_discovery/v1`` profiles and identifies
repeatable failure patterns.  It is deliberately evidence-only: it does not
rewrite DSL, alter historical results, or treat NO_TRADE as a failure by default.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping


SCHEMA_VERSION = "tactical_failure/v1"


def _safe_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _safe_json(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str, allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FailureAnalysisPolicy:
    """Declared thresholds for deterministic failure classification."""

    loss_return_pct: float = -0.000001
    severe_loss_return_pct: float = -2.0
    drawdown_threshold_pct: float = -3.0
    adverse_mae_threshold_pct: float = -2.0
    whipsaw_min_closed_trades: int = 3
    giveback_threshold_pct: float = 1.0

    def validate(self) -> None:
        if self.loss_return_pct > 0:
            raise ValueError("loss_return_pct는 0 이하여야 합니다.")
        if self.severe_loss_return_pct > self.loss_return_pct:
            raise ValueError("severe_loss_return_pct는 loss_return_pct 이하여야 합니다.")
        if self.drawdown_threshold_pct > 0 or self.adverse_mae_threshold_pct > 0:
            raise ValueError("drawdown/MAE threshold는 0 이하여야 합니다.")
        if self.whipsaw_min_closed_trades < 2:
            raise ValueError("whipsaw_min_closed_trades는 2 이상이어야 합니다.")
        if self.giveback_threshold_pct < 0:
            raise ValueError("giveback_threshold_pct는 0 이상이어야 합니다.")


CAPABILITY_HINTS = {
    "LOSS": ("ENTRY_QUALITY", "ENGAGEMENT_DISCIPLINE"),
    "SEVERE_LOSS": ("SURVIVAL_RISK", "ENGAGEMENT_DISCIPLINE"),
    "DRAWDOWN": ("SURVIVAL_RISK",),
    "ADVERSE_EXCURSION": ("ENTRY_QUALITY", "SURVIVAL_RISK"),
    "WHIPSAW": ("RANGE_DEFENSE", "ENGAGEMENT_DISCIPLINE"),
    "MFE_GIVEBACK": ("PROFIT_PROTECTION", "EXIT_QUALITY"),
}


class TacticalFailureAnalyzer:
    """Classify case-level failures and aggregate capability gaps."""

    @staticmethod
    def _case_tags(row: Mapping[str, Any], policy: FailureAnalysisPolicy) -> list[str]:
        tags: list[str] = []
        closed = int(row.get("closed_trade_count") or 0)
        if closed <= 0:
            return tags
        ret = float(row.get("return_pct") or 0.0)
        mdd = float(row.get("mdd_pct") or 0.0)
        mae = float(row.get("average_mae_pct") or 0.0)
        mfe = float(row.get("average_mfe_pct") or 0.0)
        giveback = float(row.get("mfe_giveback_pct") or 0.0)

        if ret <= policy.loss_return_pct:
            tags.append("LOSS")
        if ret <= policy.severe_loss_return_pct:
            tags.append("SEVERE_LOSS")
        if mdd <= policy.drawdown_threshold_pct:
            tags.append("DRAWDOWN")
        if mae <= policy.adverse_mae_threshold_pct:
            tags.append("ADVERSE_EXCURSION")
        if ret <= policy.loss_return_pct and closed >= policy.whipsaw_min_closed_trades:
            tags.append("WHIPSAW")
        if mfe > 0 and giveback >= policy.giveback_threshold_pct:
            tags.append("MFE_GIVEBACK")
        return tags

    @classmethod
    def analyze(
        cls,
        profile: Mapping[str, Any],
        policy: FailureAnalysisPolicy = FailureAnalysisPolicy(),
    ) -> dict:
        policy.validate()
        if str(profile.get("schema") or "") != "tactical_discovery/v1":
            raise ValueError("failure analyzer profile은 tactical_discovery/v1이어야 합니다.")
        results = list(profile.get("results") or [])
        if not results:
            raise ValueError("failure analyzer profile results가 비어 있습니다.")

        clusters: dict[str, dict[str, Any]] = {}
        no_trade_cases: list[str] = []
        active_cases = 0
        for row in results:
            case_id = str(row.get("case_id") or "").strip()
            if not case_id:
                raise ValueError("failure analyzer case_id가 비어 있습니다.")
            closed = int(row.get("closed_trade_count") or 0)
            if closed <= 0:
                no_trade_cases.append(case_id)
                continue
            active_cases += 1
            ret = float(row.get("return_pct") or 0.0)
            for tag in cls._case_tags(row, policy):
                bucket = clusters.setdefault(
                    tag,
                    {
                        "failure_tag": tag,
                        "case_ids": [],
                        "count": 0,
                        "return_impact_pct": 0.0,
                        "suggested_capabilities": list(CAPABILITY_HINTS.get(tag, ())),
                    },
                )
                bucket["case_ids"].append(case_id)
                bucket["count"] += 1
                bucket["return_impact_pct"] += min(0.0, ret)

        total_cases = len(results)
        ordered = []
        for tag, bucket in clusters.items():
            item = dict(bucket)
            item["case_rate"] = item["count"] / total_cases
            item["active_case_rate"] = item["count"] / active_cases if active_cases else 0.0
            item["case_ids"] = tuple(item["case_ids"])
            ordered.append(item)
        ordered.sort(key=lambda item: (item["return_impact_pct"], -item["count"], item["failure_tag"]))

        capability_scores: dict[str, dict[str, Any]] = {}
        for cluster in ordered:
            for capability in cluster["suggested_capabilities"]:
                score = capability_scores.setdefault(
                    capability,
                    {"capability": capability, "failure_tags": [], "case_count_sum": 0, "return_impact_pct": 0.0},
                )
                score["failure_tags"].append(cluster["failure_tag"])
                score["case_count_sum"] += int(cluster["count"])
                score["return_impact_pct"] += float(cluster["return_impact_pct"])
        gaps = list(capability_scores.values())
        for item in gaps:
            item["failure_tags"] = tuple(sorted(set(item["failure_tags"])))
        gaps.sort(key=lambda item: (item["return_impact_pct"], -item["case_count_sum"], item["capability"]))

        identity = {
            "schema": SCHEMA_VERSION,
            "profile_run_hash": str(profile.get("run_hash") or ""),
            "case_set_hash": str(profile.get("case_set_hash") or ""),
            "policy": policy.__dict__,
            "clusters": ordered,
            "no_trade_cases": no_trade_cases,
        }
        return {
            "schema": SCHEMA_VERSION,
            "profile_run_hash": str(profile.get("run_hash") or ""),
            "case_set_hash": str(profile.get("case_set_hash") or ""),
            "policy": dict(policy.__dict__),
            "total_cases": total_cases,
            "active_cases": active_cases,
            "no_trade_cases": tuple(no_trade_cases),
            "clusters": ordered,
            "capability_gaps": gaps,
            "failure_hash": _stable_hash(identity),
            "no_trade_policy": "ABSTENTION_IS_NOT_FAILURE_BY_DEFAULT",
        }
