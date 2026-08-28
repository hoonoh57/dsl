"""Observation-only pending-intent orchestration over trusted LF1 evidence.

This module is an optional multi-symbol Add-on seam. It composes already-frozen
leader/follower relation evidence with one follower-local deterministic setup,
local hard-guard state and an explicit relation-validity flag. It emits intent
evidence only; it never calls DSLRuntime, BacktestEngine, BrokerEmulator,
providers, network or persistence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = "multi_symbol_follower_pending_orchestration/v1"
POLICY_SCHEMA_VERSION = "multi_symbol_follower_pending_orchestration_policy/v1"
ORCHESTRATION_POLICY = (
    "OBSERVATION_ONLY_LF1_SELECTED_FOLLOWER_LOCAL_SETUP_HARD_GUARD_"
    "EXPLICIT_INVALIDATION_NO_EXECUTION_AUTHORITY"
)


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
class FollowerPendingIntentPolicy:
    policy_id: str
    policy_version: str
    client_id_prefix: str = "lf2-pending"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.policy_id, "LF2 policy_id")
        _text(self.policy_version, "LF2 policy_version")
        prefix = _text(self.client_id_prefix, "LF2 client_id_prefix")
        if any(ch.isspace() for ch in prefix):
            raise ValueError("LF2 client_id_prefix에는 공백을 사용할 수 없습니다.")
        _json_safe(dict(self.metadata))

    @property
    def policy_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": POLICY_SCHEMA_VERSION,
                "orchestration_policy": ORCHESTRATION_POLICY,
                "policy_id": str(self.policy_id).strip(),
                "policy_version": str(self.policy_version).strip(),
                "client_id_prefix": str(self.client_id_prefix).strip(),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": POLICY_SCHEMA_VERSION,
            "orchestration_policy": ORCHESTRATION_POLICY,
            "policy_id": str(self.policy_id).strip(),
            "policy_version": str(self.policy_version).strip(),
            "client_id_prefix": str(self.client_id_prefix).strip(),
            "metadata": dict(self.metadata),
            "policy_hash": self.policy_hash,
        }


class MultiSymbolFollowerPendingOrchestrator:
    """Compose LF1 relation evidence into non-executable ARM/CANCEL/HOLD evidence."""

    @classmethod
    def compose(
        cls,
        *,
        relation_result: Mapping[str, Any],
        policy: FollowerPendingIntentPolicy,
        as_of: str,
        follower_symbol: str,
        local_setup_pass: bool,
        hard_guard_pass: bool,
        relation_still_valid: bool,
        pending_order_active: bool = False,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        policy.validate()
        decision_time = _text(as_of, "LF2 as_of")
        local_symbol = _text(follower_symbol, "LF2 follower_symbol")
        if not isinstance(relation_result, Mapping):
            raise ValueError("LF2 relation_result는 mapping이어야 합니다.")
        if str(relation_result.get("mode", "")).strip() != "OBSERVATION_ONLY":
            raise ValueError("LF2는 OBSERVATION_ONLY LF1 evidence만 허용합니다.")
        if bool(relation_result.get("operational_authority", False)):
            raise ValueError("LF2 입력 evidence에 operational authority가 있으면 안 됩니다.")
        relation_hash = _text(relation_result.get("result_hash"), "LF2 relation result_hash")
        selected = relation_result.get("top_follow_rate_follower")
        selected = None if selected is None else str(selected).strip()
        pairs = tuple(relation_result.get("pairs") or ())
        pair_by_symbol = {
            str(row.get("follower_symbol", "")).strip(): row
            for row in pairs
            if isinstance(row, Mapping) and str(row.get("follower_symbol", "")).strip()
        }
        selected_pair = pair_by_symbol.get(selected) if selected else None
        selection_qualified = bool(
            selected
            and bool(relation_result.get("leader_role_qualified"))
            and isinstance(selected_pair, Mapping)
            and bool(selected_pair.get("qualified"))
        )

        if bool(pending_order_active):
            active_id = _text(client_order_id, "LF2 active client_order_id")
            invalid_reasons = []
            if not selection_qualified or local_symbol != selected:
                invalid_reasons.append("relation_selection_invalid")
            if not bool(local_setup_pass):
                invalid_reasons.append("local_setup_invalid")
            if not bool(hard_guard_pass):
                invalid_reasons.append("hard_guard_failed")
            if not bool(relation_still_valid):
                invalid_reasons.append("relation_invalidated")
            intent = "CANCEL_PENDING" if invalid_reasons else "HOLD_PENDING"
            resolved_client_id = active_id
            reasons = tuple(invalid_reasons) if invalid_reasons else ("pending_still_valid",)
        else:
            if client_order_id is not None and str(client_order_id).strip():
                raise ValueError("LF2 inactive pending state에는 기존 client_order_id를 지정할 수 없습니다.")
            can_arm = bool(
                selection_qualified
                and local_symbol == selected
                and bool(local_setup_pass)
                and bool(hard_guard_pass)
                and bool(relation_still_valid)
            )
            if can_arm:
                seed = _stable_hash(
                    {
                        "relation_result_hash": relation_hash,
                        "policy_hash": policy.policy_hash,
                        "as_of": decision_time,
                        "follower_symbol": local_symbol,
                    }
                )
                resolved_client_id = f"{policy.client_id_prefix}:{local_symbol}:{seed[:16]}"
                intent = "ARM_PENDING"
                reasons = ("qualified_relation_and_local_setup",)
            else:
                resolved_client_id = None
                intent = "HOLD"
                hold_reasons = []
                if not selection_qualified:
                    hold_reasons.append("no_qualified_relation")
                elif local_symbol != selected:
                    hold_reasons.append("not_selected_follower")
                if not bool(local_setup_pass):
                    hold_reasons.append("local_setup_invalid")
                if not bool(hard_guard_pass):
                    hold_reasons.append("hard_guard_failed")
                if not bool(relation_still_valid):
                    hold_reasons.append("relation_invalidated")
                reasons = tuple(hold_reasons) or ("not_armed",)

        payload = {
            "schema": SCHEMA_VERSION,
            "orchestration_policy": ORCHESTRATION_POLICY,
            "mode": "OBSERVATION_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "as_of": decision_time,
            "relation_result_hash": relation_hash,
            "policy_hash": policy.policy_hash,
            "leader_symbol": relation_result.get("leader_symbol"),
            "selected_follower_symbol": selected,
            "follower_symbol": local_symbol,
            "selection_qualified": selection_qualified,
            "local_setup_pass": bool(local_setup_pass),
            "hard_guard_pass": bool(hard_guard_pass),
            "relation_still_valid": bool(relation_still_valid),
            "pending_order_active": bool(pending_order_active),
            "intent": intent,
            "client_order_id": resolved_client_id,
            "reasons": reasons,
        }
        payload["evidence_hash"] = _stable_hash(payload)
        return payload
