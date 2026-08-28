"""Signal-time causal validated-context integration for next-open MARKET entries.

CTXINT3 extends the trusted blocking-only context gate to `signal_mode=next_open`
without changing BacktestEngine. A decision made from bar t evidence is shifted
forward and applied only when a MARKET entry generated at t can fill at the
next bar open. The fill bar's not-yet-completed context is never consulted.

Deferred LIMIT/STOP/STOP_LIMIT entry orders are intentionally rejected because
their original signal time and later fill time require a separate authority
contract.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from core.backtest import BacktestEngine
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import ParentFeatureRegistry
from core.tactical_context_deployment_evidence import ValidatedContextDeploymentPolicyEvidence
from core.tactical_context_gate_preview import ValidatedContextGatePreviewBuilder
from core.tactical_context_integration_scope import require_market_entry_orders_only
from core.tactical_discovery import TacticCandidate


SCHEMA_VERSION = "validated_context_next_open_entry_gate/v1"
INTEGRATION_POLICY = "PRIOR_COMPLETED_BAR_VALIDATED_CONTEXT_TO_NEXT_OPEN_MARKET_ENTRY_ONLY"
GATE_AUTHORITY = "ENTRY_SUPPRESSION_ONLY"
EXECUTION_AUTHORITY = "BrokerEmulator"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"CTXINT3 market time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


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
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("CTXINT3 evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


def _market_identity(market: Mapping[str, Any]) -> tuple[str, tuple[str, ...], str]:
    if not isinstance(market, Mapping):
        raise ValueError("CTXINT3 market은 Mapping이어야 합니다.")
    raw_times = market.get("time")
    if raw_times is None:
        raise ValueError("CTXINT3 market time이 필요합니다.")
    times = tuple(_time_key(item) for item in tuple(raw_times))
    if len(times) < 2:
        raise ValueError("CTXINT3 next_open 검증에는 최소 2개 bar가 필요합니다.")
    if len(set(times)) != len(times) or any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        raise ValueError("CTXINT3 market time은 중복 없이 엄격 오름차순이어야 합니다.")
    metadata = market.get("_meta")
    if not isinstance(metadata, Mapping):
        raise ValueError("CTXINT3 market _meta가 필요합니다.")
    symbol = _text(metadata.get("instrument"), "CTXINT3 market instrument")
    timeframe = _text(metadata.get("timeframe"), "CTXINT3 market timeframe")
    return symbol, times, timeframe


def _settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    frozen = dict(settings or {})
    signal_mode = str(frozen.get("signal_mode", "next_open")).strip()
    if signal_mode != "next_open":
        raise ValueError("CTXINT3은 signal_mode=next_open만 허용합니다.")
    frozen["signal_mode"] = "next_open"
    return frozen


class ValidatedContextNextOpenIntegration:
    """Apply prior completed-bar context permission to the next MARKET open only."""

    @classmethod
    def run(
        cls,
        *,
        candidate: TacticCandidate,
        policy_evidence: ValidatedContextDeploymentPolicyEvidence,
        frame: ParentContextFrame,
        registry: ParentFeatureRegistry,
        market: Mapping[str, Any],
        tactic_trigger: Sequence[bool],
        local_hard_guard_pass: Sequence[bool],
        settings: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(candidate, TacticCandidate):
            raise ValueError("CTXINT3 candidate는 TacticCandidate여야 합니다.")
        candidate.validate()
        require_market_entry_orders_only(candidate.dsl_code, label="CTXINT3")
        policy_evidence.validate()
        frame.validate()
        registry.validate()

        candidate_hash = candidate.candidate_hash
        if candidate_hash != str(policy_evidence.policy.tactic_id).strip():
            raise ValueError("CTXINT3 candidate_hash가 validated policy tactic과 다릅니다.")

        symbol, target_times, timeframe = _market_identity(market)
        if symbol != str(frame.target_symbol).strip():
            raise ValueError("CTXINT3 market instrument가 DEPLOYMENT frame target_symbol과 다릅니다.")
        frame_times = tuple(_time_key(point.target_time) for point in frame.points)
        if target_times != frame_times:
            raise ValueError("CTXINT3 market timeline이 DEPLOYMENT frame과 exact 일치해야 합니다.")

        config = _settings(settings)
        preview = ValidatedContextGatePreviewBuilder.build(
            policy_evidence=policy_evidence,
            frame=frame,
            registry=registry,
            tactic_id=candidate_hash,
            target_times=target_times,
            tactic_trigger=tactic_trigger,
            local_hard_guard_pass=local_hard_guard_pass,
        )

        signal_eligibility = tuple(bool(point.effective_entry_eligible) for point in preview.points)
        entry_gate = (False,) + signal_eligibility[:-1]
        gate_source_times = (None,) + target_times[:-1]

        backtest = BacktestEngine.run(
            candidate.dsl_code,
            settings=config,
            market=dict(market),
            data_timeframe=timeframe,
            entry_gate=entry_gate,
        )
        diagnostics = dict(backtest.get("diagnostics") or {})
        if diagnostics.get("execution_authority") != EXECUTION_AUTHORITY:
            raise ValueError("CTXINT3 실행 권한은 BrokerEmulator에 남아 있어야 합니다.")
        entry_policy = dict(diagnostics.get("entry_policy") or {})
        if entry_policy.get("higher_layer_gate_supplied") is not True:
            raise ValueError("CTXINT3 shifted validated gate가 Backtest entry policy에 전달되지 않았습니다.")

        gate_identity = {
            "schema": SCHEMA_VERSION,
            "integration_policy": INTEGRATION_POLICY,
            "candidate_hash": candidate_hash,
            "target_symbol": symbol,
            "target_times": target_times,
            "preview_hash": preview.preview_hash,
            "signal_eligibility": signal_eligibility,
            "entry_gate": entry_gate,
            "gate_source_times": gate_source_times,
        }
        gate_hash = _stable_hash(gate_identity)
        return {
            "schema": SCHEMA_VERSION,
            "integration_policy": INTEGRATION_POLICY,
            "candidate_hash": candidate_hash,
            "target_symbol": symbol,
            "target_times": target_times,
            "preview_hash": preview.preview_hash,
            "policy_hash": preview.policy_hash,
            "policy_evidence_hash": preview.policy_evidence_hash,
            "signal_eligibility": signal_eligibility,
            "entry_gate": entry_gate,
            "gate_source_times": gate_source_times,
            "gate_hash": gate_hash,
            "gate_authority": GATE_AUTHORITY,
            "context_timing": "PRIOR_COMPLETED_BAR_ONLY",
            "entry_order_scope": "MARKET_ONLY_DEFERRED_FAIL_CLOSED",
            "can_use_fill_bar_context_for_next_open": False,
            "can_create_entry": False,
            "can_bypass_local_hard_guard": False,
            "can_block_exit": False,
            "broker_order_authority": False,
            "execution_authority": EXECUTION_AUTHORITY,
            "backtest": backtest,
        }
