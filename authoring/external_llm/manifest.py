"""Machine-derived contract snapshot for the external-LLM authoring lane.

AXIS 1 capability truth is read from the Step 6 registry. AXIS 2 feature/data
source identities are supplied explicitly by the caller until a dedicated
machine-readable AXIS 2 source registry exists; they are never inferred here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from axes.axis1_dsl.core.capability_diagnostic_registry import capability_records, registry_hash
from axes.axis1_dsl.core.dsl_parser import DSLParser


SUPPORTED_STATUSES = frozenset({"SUPPORTED", "SUPPORTED_WITH_BOUNDARY"})
CONTEXT_TYPES = frozenset({"NUMBER", "BOOLEAN", "STRING"})


class AuthoringManifestError(ValueError):
    def __init__(self, message: str, code: str = "AUTHORING_MANIFEST_ERROR"):
        self.code = str(code)
        super().__init__(message)


def _identity_list(values: Sequence[str], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AuthoringManifestError(f"{label} must be a sequence", "BAD_MANIFEST_LIST")
    result = tuple(sorted(str(value).strip() for value in values))
    if any(not value for value in result):
        raise AuthoringManifestError(f"{label} contains empty identity", "BAD_MANIFEST_ID")
    if len(result) != len(set(result)):
        raise AuthoringManifestError(f"{label} contains duplicate identity", "DUPLICATE_MANIFEST_ID")
    return result


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthoringManifest:
    capability_registry_hash: str
    capabilities: tuple[Mapping[str, Any], ...]
    feature_ids: tuple[str, ...]
    data_source_ids: tuple[str, ...]
    context_feature_types: tuple[tuple[str, str], ...]
    order_commands: tuple[str, ...]
    manifest_version: str = "external_authoring_manifest/v1"

    @property
    def context_types(self) -> dict[str, str]:
        return dict(self.context_feature_types)

    @property
    def capability_by_id(self) -> dict[str, Mapping[str, Any]]:
        return {str(item["capability_id"]): item for item in self.capabilities}

    @property
    def supported_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                capability_id
                for capability_id, item in self.capability_by_id.items()
                if item.get("status") in SUPPORTED_STATUSES
            )
        )

    @property
    def unavailable_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                capability_id
                for capability_id, item in self.capability_by_id.items()
                if item.get("status") not in SUPPORTED_STATUSES
            )
        )

    @property
    def supported_function_names(self) -> tuple[str, ...]:
        return tuple(sorted({item["name"] for item in self.function_contracts}))

    @property
    def function_contracts(self) -> tuple[dict[str, Any], ...]:
        result: list[dict[str, Any]] = []
        for item in self.capabilities:
            if item.get("kind") != "function" or item.get("status") not in SUPPORTED_STATUSES:
                continue
            details = item.get("details") or {}
            name = str(details.get("name") or "").strip()
            if not name:
                continue
            result.append(
                {
                    "capability_id": str(item["capability_id"]),
                    "name": name,
                    "mode": str(details.get("mode") or ""),
                    "signature": str(details.get("signature") or item.get("support_scope") or ""),
                    "output_names": list(details.get("output_names") or ()),
                    "output_types": list(details.get("output_types") or ()),
                    "lookback": details.get("lookback"),
                    "warmup": details.get("warmup"),
                    "nan_policy": details.get("nan_policy"),
                    "causality": details.get("causality"),
                    "limitations": list(item.get("limitations") or ()),
                }
            )
        return tuple(sorted(result, key=lambda value: (value["name"], value["mode"])))

    @property
    def feature_capability_contracts(self) -> tuple[dict[str, Any], ...]:
        result: list[dict[str, Any]] = []
        for item in self.capabilities:
            if item.get("kind") == "function":
                continue
            result.append(
                {
                    "capability_id": str(item["capability_id"]),
                    "kind": str(item.get("kind") or ""),
                    "status": str(item.get("status") or ""),
                    "summary": str(item.get("summary") or ""),
                    "support_scope": str(item.get("support_scope") or ""),
                    "limitations": list(item.get("limitations") or ()),
                }
            )
        return tuple(sorted(result, key=lambda value: value["capability_id"]))

    def public_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "capability_registry_hash": self.capability_registry_hash,
            "supported_capability_ids": list(self.supported_capability_ids),
            "unavailable_capability_ids": list(self.unavailable_capability_ids),
            "function_contracts": list(self.function_contracts),
            "feature_capability_contracts": list(self.feature_capability_contracts),
            "feature_ids": list(self.feature_ids),
            "data_source_ids": list(self.data_source_ids),
            "context_feature_types": dict(self.context_feature_types),
            "order_commands": list(self.order_commands),
        }

    @property
    def manifest_hash(self) -> str:
        return _canonical_hash(self.public_dict())


def build_authoring_manifest(
    *,
    feature_ids: Sequence[str] = (),
    data_source_ids: Sequence[str] = (),
    context_feature_types: Mapping[str, str] | None = None,
) -> AuthoringManifest:
    context = context_feature_types or {}
    if not isinstance(context, Mapping):
        raise AuthoringManifestError("context_feature_types must be a mapping", "BAD_CONTEXT_MANIFEST")
    normalized_context: list[tuple[str, str]] = []
    for feature_id, value_type in context.items():
        identity = str(feature_id).strip()
        kind = str(value_type).strip().upper()
        if not identity:
            raise AuthoringManifestError("context feature id is empty", "BAD_CONTEXT_ID")
        if kind not in CONTEXT_TYPES:
            raise AuthoringManifestError(f"unsupported context type: {kind}", "BAD_CONTEXT_TYPE")
        normalized_context.append((identity, kind))
    normalized_context.sort()
    if len(normalized_context) != len({item[0] for item in normalized_context}):
        raise AuthoringManifestError("duplicate context feature id", "DUPLICATE_CONTEXT_ID")

    records = tuple(capability_records())
    return AuthoringManifest(
        capability_registry_hash=registry_hash(),
        capabilities=records,
        feature_ids=_identity_list(feature_ids, "feature_ids"),
        data_source_ids=_identity_list(data_source_ids, "data_source_ids"),
        context_feature_types=tuple(normalized_context),
        order_commands=tuple(sorted(DSLParser.ORDER_COMMANDS)),
    )
