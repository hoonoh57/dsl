"""Non-operational preview of validated parent-context admission composition.

CTXINT1 verifies the seam between a trusted CTXDEP1 policy-evidence bundle and
an exact DEPLOYMENT ParentContextFrame without installing anything into
BacktestEngine or BrokerEmulator.  It proves composition semantics only:

    tactic trigger
    AND local hard-guard pass
    AND validated parent-context permission
    -> effective entry eligibility preview

The preview can only remove local entry opportunities.  It can never create an
entry when the tactic trigger or a local hard guard is false.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from core.parent_context_frame import ParentContextBinder, ParentContextFrame
from core.parent_feature_provider import ParentFeatureRegistry
from core.tactical_context_deployment_evidence import ValidatedContextDeploymentPolicyEvidence


SCHEMA_VERSION = "validated_context_entry_gate_preview/v1"
COMPOSITION_POLICY = (
    "TACTIC_TRIGGER_AND_LOCAL_HARD_GUARD_AND_VALIDATED_CONTEXT_PERMISSION_"
    "NO_ENTRY_CREATION"
)
EXECUTION_INTEGRATION = "PREVIEW_ONLY_NOT_INSTALLED_AS_BACKTEST_ENTRY_GATE_OR_BROKER"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"context gate preview time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


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
        raise ValueError("context gate preview에 NaN/Infinity를 사용할 수 없습니다.")
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


def _bool_series(values: Sequence[bool], *, label: str, size: int) -> tuple[bool, ...]:
    frozen = tuple(values)
    if len(frozen) != size:
        raise ValueError(f"{label} 길이는 target_times와 같아야 합니다: {len(frozen)} != {size}")
    if any(type(item) is not bool for item in frozen):
        raise ValueError(f"{label}는 명시적 bool 시퀀스여야 합니다.")
    return frozen


@dataclass(frozen=True)
class ContextGatePreviewPoint:
    target_time: str
    tactic_trigger: bool
    local_hard_guard_pass: bool
    context_allowed: bool
    effective_entry_eligible: bool
    context_hash: str
    binding_hash: str
    decision_hash: str

    def validate(self) -> None:
        _time_key(self.target_time)
        for name in (
            "tactic_trigger",
            "local_hard_guard_pass",
            "context_allowed",
            "effective_entry_eligible",
        ):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"context gate preview {name}는 bool이어야 합니다.")
        _text(self.context_hash, "context gate preview context_hash")
        _text(self.binding_hash, "context gate preview binding_hash")
        _text(self.decision_hash, "context gate preview decision_hash")
        expected = bool(self.tactic_trigger and self.local_hard_guard_pass and self.context_allowed)
        if self.effective_entry_eligible is not expected:
            raise ValueError("context gate preview effective entry composition이 올바르지 않습니다.")
        if self.effective_entry_eligible and (not self.tactic_trigger or not self.local_hard_guard_pass):
            raise ValueError("parent context는 local entry opportunity를 새로 만들 수 없습니다.")

    @property
    def point_hash(self) -> str:
        self.validate()
        return _stable_hash(self.public_dict(include_hash=False))

    def public_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "target_time": _time_key(self.target_time),
            "tactic_trigger": bool(self.tactic_trigger),
            "local_hard_guard_pass": bool(self.local_hard_guard_pass),
            "context_allowed": bool(self.context_allowed),
            "effective_entry_eligible": bool(self.effective_entry_eligible),
            "context_hash": str(self.context_hash).strip(),
            "binding_hash": str(self.binding_hash).strip(),
            "decision_hash": str(self.decision_hash).strip(),
        }
        if include_hash:
            payload["point_hash"] = self.point_hash
        return payload


@dataclass(frozen=True)
class ValidatedContextGatePreview:
    tactic_id: str
    target_symbol: str
    frame_hash: str
    registry_hash: str
    policy_hash: str
    policy_evidence_hash: str
    feature_id: str
    required_manifest_hash: str
    points: tuple[ContextGatePreviewPoint, ...]

    def validate(self) -> None:
        _text(self.tactic_id, "context gate preview tactic_id")
        _text(self.target_symbol, "context gate preview target_symbol")
        _text(self.frame_hash, "context gate preview frame_hash")
        _text(self.registry_hash, "context gate preview registry_hash")
        _text(self.policy_hash, "context gate preview policy_hash")
        _text(self.policy_evidence_hash, "context gate preview policy_evidence_hash")
        _text(self.feature_id, "context gate preview feature_id")
        _text(self.required_manifest_hash, "context gate preview required_manifest_hash")
        if not self.points:
            raise ValueError("context gate preview points가 비어 있습니다.")
        previous = None
        for point in self.points:
            if not isinstance(point, ContextGatePreviewPoint):
                raise ValueError("context gate preview point 타입이 올바르지 않습니다.")
            point.validate()
            current = _time_key(point.target_time)
            if previous is not None and current <= previous:
                raise ValueError("context gate preview points는 엄격 오름차순이어야 합니다.")
            previous = current

    @property
    def preview_hash(self) -> str:
        self.validate()
        return _stable_hash(self.public_dict(include_hash=False))

    def public_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        self.validate()
        effective_count = sum(1 for point in self.points if point.effective_entry_eligible)
        local_opportunity_count = sum(
            1 for point in self.points if point.tactic_trigger and point.local_hard_guard_pass
        )
        context_blocked_local_count = sum(
            1
            for point in self.points
            if point.tactic_trigger and point.local_hard_guard_pass and not point.context_allowed
        )
        payload = {
            "schema": SCHEMA_VERSION,
            "composition_policy": COMPOSITION_POLICY,
            "tactic_id": str(self.tactic_id).strip(),
            "target_symbol": str(self.target_symbol).strip(),
            "frame_hash": str(self.frame_hash).strip(),
            "registry_hash": str(self.registry_hash).strip(),
            "policy_hash": str(self.policy_hash).strip(),
            "policy_evidence_hash": str(self.policy_evidence_hash).strip(),
            "feature_id": str(self.feature_id).strip(),
            "required_manifest_hash": str(self.required_manifest_hash).strip(),
            "points": tuple(point.public_dict() for point in self.points),
            "local_entry_opportunity_count": local_opportunity_count,
            "context_blocked_local_count": context_blocked_local_count,
            "effective_entry_eligible_count": effective_count,
            "can_create_entry_without_local_opportunity": False,
            "operational_authority": False,
            "execution_integration": EXECUTION_INTEGRATION,
        }
        if include_hash:
            payload["preview_hash"] = self.preview_hash
        return payload


class ValidatedContextGatePreviewBuilder:
    """Build exact-time non-operational gate composition evidence."""

    @classmethod
    def build(
        cls,
        *,
        policy_evidence: ValidatedContextDeploymentPolicyEvidence,
        frame: ParentContextFrame,
        registry: ParentFeatureRegistry,
        tactic_id: str,
        target_times: Sequence[str],
        tactic_trigger: Sequence[bool],
        local_hard_guard_pass: Sequence[bool],
    ) -> ValidatedContextGatePreview:
        if not isinstance(policy_evidence, ValidatedContextDeploymentPolicyEvidence):
            raise ValueError("CTXINT1은 CTXDEP1 policy evidence만 허용합니다.")
        policy_evidence.validate()
        if not isinstance(frame, ParentContextFrame):
            raise ValueError("CTXINT1 frame은 ParentContextFrame이어야 합니다.")
        if not isinstance(registry, ParentFeatureRegistry):
            raise ValueError("CTXINT1 registry는 ParentFeatureRegistry여야 합니다.")
        frame.validate()
        registry.validate()
        if str(frame.mode).strip().upper() != "DEPLOYMENT":
            raise ValueError("CTXINT1은 DEPLOYMENT ParentContextFrame만 허용합니다.")
        if frame.registry_hash != registry.registry_hash:
            raise ValueError("CTXINT1 registry_hash가 frame과 다릅니다.")

        wanted_tactic = _text(tactic_id, "CTXINT1 tactic_id")
        policy_tactic = str(policy_evidence.policy.tactic_id).strip()
        if wanted_tactic != policy_tactic:
            raise ValueError("CTXINT1 tactic_id가 validated policy tactic과 다릅니다.")

        feature_id = _text(policy_evidence.feature_id, "CTXINT1 feature_id")
        required_manifest_hash = _text(
            policy_evidence.required_manifest_hash, "CTXINT1 required_manifest_hash"
        )
        if required_manifest_hash not in frame.manifest_hashes:
            raise ValueError("CTXINT1 required manifest가 DEPLOYMENT frame에 없습니다.")
        try:
            resolved = registry.resolve(feature_id)
        except KeyError as exc:
            raise ValueError("CTXINT1 feature_id가 registry에 등록되어 있지 않습니다.") from exc
        manifest = dict(resolved["manifest"])
        feature = dict(resolved["feature"])
        if str(manifest["manifest_hash"]) != required_manifest_hash:
            raise ValueError("CTXINT1 feature manifest가 validated policy evidence와 다릅니다.")
        rule = policy_evidence.policy.rule
        if str(manifest["layer"]).strip().upper() != str(rule.layer).strip().upper():
            raise ValueError("CTXINT1 feature layer가 validated policy rule과 다릅니다.")
        if str(manifest["context_id"]).strip() != str(rule.context_id).strip():
            raise ValueError("CTXINT1 feature context_id가 validated policy rule과 다릅니다.")
        if str(feature["feature_key"]).strip() != str(rule.feature_key).strip():
            raise ValueError("CTXINT1 feature_key가 validated policy rule과 다릅니다.")

        times = tuple(_time_key(item) for item in target_times)
        if not times:
            raise ValueError("CTXINT1 target_times가 비어 있습니다.")
        if len(set(times)) != len(times) or any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
            raise ValueError("CTXINT1 target_times는 중복 없이 엄격 오름차순이어야 합니다.")
        frame_times = tuple(_time_key(point.target_time) for point in frame.points)
        if times != frame_times:
            raise ValueError("CTXINT1 target_times는 DEPLOYMENT frame 전체 timeline과 exact 일치해야 합니다.")
        triggers = _bool_series(tactic_trigger, label="CTXINT1 tactic_trigger", size=len(times))
        guards = _bool_series(
            local_hard_guard_pass,
            label="CTXINT1 local_hard_guard_pass",
            size=len(times),
        )

        points: list[ContextGatePreviewPoint] = []
        for index, target_time in enumerate(times):
            binding = ParentContextBinder.bind(
                frame=frame,
                registry=registry,
                target_time=target_time,
                feature_ids=(feature_id,),
            )
            bound = binding.values[0]
            if not bound.present:
                raise ValueError("CTXINT1 validated policy feature가 exact DEPLOYMENT point에 없습니다.")
            context = frame.resolve_exact(target_time)
            decision = policy_evidence.policy.decide(context)
            if decision.get("operational_authority") is not False:
                raise ValueError("CTXINT1 source deployment decision은 non-operational이어야 합니다.")
            if str(decision.get("policy_hash") or "") != policy_evidence.policy.policy_hash:
                raise ValueError("CTXINT1 deployment decision policy identity가 evidence와 다릅니다.")
            public_decision = dict(decision.get("decision") or {})
            allowed = public_decision.get("allowed")
            if type(allowed) is not bool:
                raise ValueError("CTXINT1 deployment decision allowed가 bool이 아닙니다.")
            if allowed:
                if wanted_tactic not in tuple(public_decision.get("eligible_tactics") or ()):
                    raise ValueError("CTXINT1 allow decision에 validated tactic이 없습니다.")
                if wanted_tactic in tuple(public_decision.get("blocked_tactics") or ()):
                    raise ValueError("CTXINT1 allow decision이 validated tactic을 동시에 block합니다.")
            else:
                if wanted_tactic not in tuple(public_decision.get("blocked_tactics") or ()):
                    raise ValueError("CTXINT1 block decision에 validated tactic이 없습니다.")

            effective = bool(triggers[index] and guards[index] and allowed)
            point = ContextGatePreviewPoint(
                target_time=target_time,
                tactic_trigger=triggers[index],
                local_hard_guard_pass=guards[index],
                context_allowed=allowed,
                effective_entry_eligible=effective,
                context_hash=context.context_hash,
                binding_hash=binding.binding_hash,
                decision_hash=_text(decision.get("decision_hash"), "CTXINT1 decision_hash"),
            )
            point.validate()
            points.append(point)

        preview = ValidatedContextGatePreview(
            tactic_id=wanted_tactic,
            target_symbol=str(frame.target_symbol).strip(),
            frame_hash=frame.frame_hash,
            registry_hash=registry.registry_hash,
            policy_hash=policy_evidence.policy.policy_hash,
            policy_evidence_hash=policy_evidence.evidence_hash,
            feature_id=feature_id,
            required_manifest_hash=required_manifest_hash,
            points=tuple(points),
        )
        preview.validate()
        return preview
