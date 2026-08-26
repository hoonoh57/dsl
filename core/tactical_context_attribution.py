"""Read-only macro/parent-context attribution and deployment evidence.

E8 deliberately keeps macro intelligence outside the Instrument DSL and trusted
execution engine.  A previously frozen NEUTRAL tactical profile is joined to
separate point-in-time OBSERVED BattlefieldContext snapshots for attribution.
A separately declared policy may later turn a DEPLOYMENT context into a
DeploymentDecision, but this module never calls BrokerEmulator, mutates DSL
source, rewrites historical profiles, or installs an entry gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import mean, median
from typing import Any, Mapping, Sequence

from core.battlefield_context import BattlefieldContext, DeploymentDecision


ATTRIBUTION_SCHEMA_VERSION = "tactical_context_attribution/v1"
DEPLOYMENT_SCHEMA_VERSION = "tactical_context_deployment/v1"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("context attribution evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label}가 필요합니다.")
    return text


def _finite_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}는 숫자여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}는 유한해야 합니다.")
    return number


@dataclass(frozen=True)
class ContextSliceRule:
    """One explicit context slice used independently for attribution/gating."""

    slice_id: str
    layer: str
    context_id: str
    feature_key: str
    operator: str
    value: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)

    OPERATORS = {"EQ", "GT", "GTE", "LT", "LTE"}

    def normalized_operator(self) -> str:
        return str(self.operator or "").strip().upper()

    def validate(self) -> None:
        _require_text(self.slice_id, "slice_id")
        _require_text(self.layer, "slice.layer")
        _require_text(self.context_id, "slice.context_id")
        _require_text(self.feature_key, "slice.feature_key")
        operator = self.normalized_operator()
        if operator not in self.OPERATORS:
            raise ValueError(f"지원하지 않는 context slice operator: {self.operator!r}")
        if operator != "EQ":
            _finite_number(self.value, "slice.value")
        _json_safe(dict(self.metadata))

    def public_dict(self) -> dict:
        self.validate()
        return {
            "slice_id": str(self.slice_id).strip(),
            "layer": str(self.layer).strip().upper(),
            "context_id": str(self.context_id).strip(),
            "feature_key": str(self.feature_key).strip(),
            "operator": self.normalized_operator(),
            "value": _json_safe(self.value),
            "metadata": dict(self.metadata),
        }

    def _feature_value(self, context: BattlefieldContext) -> Any:
        context.validate()
        wanted_layer = str(self.layer).strip().upper()
        wanted_context = str(self.context_id).strip()
        matches = [
            layer
            for layer in context.layers
            if str(layer.layer).strip().upper() == wanted_layer
            and str(layer.context_id).strip() == wanted_context
        ]
        if len(matches) != 1:
            raise ValueError(
                f"context slice가 요구하는 layer/context를 정확히 하나 찾을 수 없습니다: "
                f"{wanted_layer}/{wanted_context}"
            )
        feature_key = str(self.feature_key).strip()
        if feature_key not in matches[0].features:
            raise ValueError(
                f"context slice feature가 없습니다: {wanted_layer}/{wanted_context}/{feature_key}"
            )
        return matches[0].features[feature_key]

    def matches(self, context: BattlefieldContext) -> bool:
        self.validate()
        actual = self._feature_value(context)
        operator = self.normalized_operator()
        if operator == "EQ":
            return actual == self.value
        left = _finite_number(actual, "context feature")
        right = _finite_number(self.value, "slice.value")
        if operator == "GT":
            return left > right
        if operator == "GTE":
            return left >= right
        if operator == "LT":
            return left < right
        if operator == "LTE":
            return left <= right
        raise AssertionError(operator)


class TacticalContextAttributor:
    """Join a frozen neutral tactical profile to external observed context."""

    @staticmethod
    def _validate_profile(profile: Mapping[str, Any]) -> tuple[dict, ...]:
        if str(profile.get("schema") or "") != "tactical_discovery/v1":
            raise ValueError("context attribution profile은 tactical_discovery/v1이어야 합니다.")
        _require_text(profile.get("run_hash"), "profile.run_hash")
        _require_text(profile.get("case_set_hash"), "profile.case_set_hash")
        candidate_hash = (profile.get("candidate") or {}).get("candidate_hash")
        _require_text(candidate_hash, "profile.candidate_hash")
        policy = dict(profile.get("context_policy") or {})
        if policy.get("require_neutral_context") is not True:
            raise ValueError("E8 attribution은 NEUTRAL micro baseline profile만 허용합니다.")
        rows = tuple(dict(row) for row in (profile.get("results") or ()))
        if not rows:
            raise ValueError("context attribution profile results가 비어 있습니다.")
        case_ids = []
        for row in rows:
            case_ids.append(_require_text(row.get("case_id"), "profile result.case_id"))
            _require_text(row.get("knowledge_cutoff"), "profile result.knowledge_cutoff")
            for key in ("return_pct", "mdd_pct", "total_cost", "mfe_giveback_pct"):
                _finite_number(row.get(key, 0.0), f"profile result.{key}")
            try:
                closed = int(row.get("closed_trade_count") or 0)
            except (TypeError, ValueError) as exc:
                raise ValueError("profile result.closed_trade_count가 올바르지 않습니다.") from exc
            if closed < 0:
                raise ValueError("profile result.closed_trade_count는 음수일 수 없습니다.")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("context attribution profile case_id에 중복이 있습니다.")
        return rows

    @staticmethod
    def _summary(rows: Sequence[Mapping[str, Any]]) -> dict:
        items = tuple(rows)
        if not items:
            return {
                "cases": 0,
                "active_cases": 0,
                "no_trade_cases": 0,
                "profitable_case_rate": None,
                "average_return_pct": None,
                "median_return_pct": None,
                "worst_case_return_pct": None,
                "worst_mdd_pct": None,
                "cost_per_case": None,
                "average_mfe_giveback_pct": None,
            }
        returns = [_finite_number(row.get("return_pct", 0.0), "return_pct") for row in items]
        mdds = [_finite_number(row.get("mdd_pct", 0.0), "mdd_pct") for row in items]
        costs = [_finite_number(row.get("total_cost", 0.0), "total_cost") for row in items]
        giveback = [_finite_number(row.get("mfe_giveback_pct", 0.0), "mfe_giveback_pct") for row in items]
        active = sum(1 for row in items if int(row.get("closed_trade_count") or 0) > 0)
        return {
            "cases": len(items),
            "active_cases": active,
            "no_trade_cases": len(items) - active,
            "profitable_case_rate": sum(1 for value in returns if value > 0.0) / len(items),
            "average_return_pct": float(mean(returns)),
            "median_return_pct": float(median(returns)),
            "worst_case_return_pct": float(min(returns)),
            "worst_mdd_pct": float(min(mdds)),
            "cost_per_case": float(mean(costs)),
            "average_mfe_giveback_pct": float(mean(giveback)),
        }

    @staticmethod
    def _delta(slice_summary: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict:
        result = {}
        for key in (
            "profitable_case_rate",
            "average_return_pct",
            "median_return_pct",
            "worst_case_return_pct",
            "worst_mdd_pct",
            "cost_per_case",
            "average_mfe_giveback_pct",
        ):
            left = slice_summary.get(key)
            right = baseline.get(key)
            result[key] = None if left is None or right is None else float(left) - float(right)
        return result

    @classmethod
    def attribute(
        cls,
        *,
        profile: Mapping[str, Any],
        contexts: Mapping[str, BattlefieldContext],
        rules: Sequence[ContextSliceRule],
    ) -> dict:
        rows = cls._validate_profile(profile)
        ordered_rules = tuple(sorted(tuple(rules), key=lambda item: str(item.slice_id)))
        if not ordered_rules:
            raise ValueError("context attribution rules가 비어 있습니다.")
        for rule in ordered_rules:
            rule.validate()
        if len({rule.slice_id for rule in ordered_rules}) != len(ordered_rules):
            raise ValueError("context attribution slice_id에 중복이 있습니다.")

        row_by_case = {str(row["case_id"]): row for row in rows}
        supplied = {str(case_id): context for case_id, context in contexts.items()}
        if set(supplied) != set(row_by_case):
            missing = sorted(set(row_by_case) - set(supplied))
            extra = sorted(set(supplied) - set(row_by_case))
            raise ValueError(f"context attribution case coverage가 정확히 일치해야 합니다: missing={missing}, extra={extra}")

        context_identity = []
        for case_id in sorted(row_by_case):
            context = supplied[case_id]
            if not isinstance(context, BattlefieldContext):
                raise ValueError(f"context attribution context 타입이 올바르지 않습니다: {case_id}")
            context.validate_for(str(row_by_case[case_id]["knowledge_cutoff"]))
            if str(context.mode).strip().upper() != "OBSERVED":
                raise ValueError(f"E8 attribution context는 OBSERVED mode여야 합니다: {case_id}")
            context_identity.append({"case_id": case_id, "context_hash": context.context_hash})

        baseline = cls._summary(rows)
        rule_results = []
        for rule in ordered_rules:
            matched = []
            matched_ids = []
            for row in rows:
                case_id = str(row["case_id"])
                if rule.matches(supplied[case_id]):
                    matched.append(row)
                    matched_ids.append(case_id)
            summary = cls._summary(matched)
            rule_results.append(
                {
                    "slice": rule.public_dict(),
                    "matched_case_ids": tuple(matched_ids),
                    "summary": summary,
                    "incremental_vs_all": cls._delta(summary, baseline),
                    "retained_case_rate": len(matched) / len(rows),
                    "retained_active_case_rate": (
                        summary["active_cases"] / baseline["active_cases"]
                        if baseline["active_cases"] > 0
                        else None
                    ),
                }
            )

        identity = {
            "schema": ATTRIBUTION_SCHEMA_VERSION,
            "profile_run_hash": profile["run_hash"],
            "case_set_hash": profile["case_set_hash"],
            "candidate_hash": profile["candidate"]["candidate_hash"],
            "contexts": context_identity,
            "rules": rule_results,
        }
        return {
            "schema": ATTRIBUTION_SCHEMA_VERSION,
            "profile_run_hash": profile["run_hash"],
            "case_set_hash": profile["case_set_hash"],
            "candidate_hash": profile["candidate"]["candidate_hash"],
            "baseline": baseline,
            "context_case_hashes": tuple(context_identity),
            "slices": tuple(rule_results),
            "selection_policy": "INDEPENDENT_DECLARED_CONTEXT_SLICES_NO_HIDDEN_SCORE",
            "mutation_policy": "HISTORICAL_MICRO_PROFILE_READ_ONLY",
            "deployment_policy": "ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY",
            "attribution_hash": _stable_hash(identity),
        }


@dataclass(frozen=True)
class ContextDeploymentPolicy:
    """Explicit command policy producing evidence, never direct execution."""

    policy_id: str
    policy_version: str
    tactic_id: str
    rule: ContextSliceRule
    attribution_hash: str
    evidence_status: str = "RESEARCH_ONLY"
    validation_evidence_hash: str = ""
    priority_if_allowed: float = 0.0

    EVIDENCE_STATUSES = {"RESEARCH_ONLY", "VALIDATED"}

    def validate(self) -> None:
        _require_text(self.policy_id, "deployment policy_id")
        _require_text(self.policy_version, "deployment policy_version")
        _require_text(self.tactic_id, "deployment tactic_id")
        self.rule.validate()
        _require_text(self.attribution_hash, "deployment attribution_hash")
        status = str(self.evidence_status or "").strip().upper()
        if status not in self.EVIDENCE_STATUSES:
            raise ValueError(f"deployment evidence_status가 올바르지 않습니다: {self.evidence_status!r}")
        if status == "VALIDATED":
            _require_text(self.validation_evidence_hash, "VALIDATED deployment validation_evidence_hash")
        _finite_number(self.priority_if_allowed, "deployment priority_if_allowed")

    def public_dict(self) -> dict:
        self.validate()
        return {
            "policy_id": str(self.policy_id).strip(),
            "policy_version": str(self.policy_version).strip(),
            "tactic_id": str(self.tactic_id).strip(),
            "rule": self.rule.public_dict(),
            "attribution_hash": str(self.attribution_hash).strip(),
            "evidence_status": str(self.evidence_status).strip().upper(),
            "validation_evidence_hash": str(self.validation_evidence_hash or "").strip(),
            "priority_if_allowed": float(self.priority_if_allowed),
        }

    @property
    def policy_hash(self) -> str:
        return _stable_hash({"schema": DEPLOYMENT_SCHEMA_VERSION, **self.public_dict()})

    def decide(self, context: BattlefieldContext) -> dict:
        self.validate()
        context.validate()
        if str(context.mode).strip().upper() != "DEPLOYMENT":
            raise ValueError("deployment policy는 DEPLOYMENT BattlefieldContext만 허용합니다.")
        matched = self.rule.matches(context)
        tactic = str(self.tactic_id).strip()
        status = str(self.evidence_status).strip().upper()
        if matched:
            decision = DeploymentDecision(
                context_hash=context.context_hash,
                allowed=True,
                priority=float(self.priority_if_allowed),
                eligible_tactics=(tactic,),
                blocked_tactics=(),
                reasons=(
                    f"context_slice_match:{self.rule.slice_id}",
                    f"attribution:{self.attribution_hash}",
                    f"evidence_status:{status}",
                ),
            )
        else:
            decision = DeploymentDecision(
                context_hash=context.context_hash,
                allowed=False,
                priority=0.0,
                eligible_tactics=(),
                blocked_tactics=(tactic,),
                reasons=(
                    f"context_slice_miss:{self.rule.slice_id}",
                    f"attribution:{self.attribution_hash}",
                    f"evidence_status:{status}",
                ),
            )
        public_decision = decision.public_dict()
        identity = {
            "schema": DEPLOYMENT_SCHEMA_VERSION,
            "policy_hash": self.policy_hash,
            "context_hash": context.context_hash,
            "matched": matched,
            "decision": public_decision,
        }
        return {
            "schema": DEPLOYMENT_SCHEMA_VERSION,
            "policy": self.public_dict(),
            "policy_hash": self.policy_hash,
            "context_hash": context.context_hash,
            "matched": matched,
            "decision": public_decision,
            "operational_authority": status == "VALIDATED",
            "execution_integration": "NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER",
            "decision_hash": _stable_hash(identity),
        }
