"""Step 11 versioned AXIS2 -> AXIS3 -> AXIS1 E2E Bridge routing.

The Bridge is the only layer allowed to compose the three axes.  Each axis keeps
its own authority: AXIS 2 selects from a frozen point-in-time snapshot, AXIS 3
binds promoted immutable artifacts and produces a run plan, and AXIS 1 executes
one deterministic instrument request at a time through its existing Bridge.
"""
from __future__ import annotations

from typing import Any, Mapping

from bridges.contracts.common import BridgeContractError, BridgeResponseMeta
from bridges.contracts.axis1_execution import (
    AXIS1_EXECUTION_REQUEST_SCHEMA,
    AXIS1_OPERATION,
    Axis1ExecutionRequest,
)
from bridges.contracts.three_axis_e2e import (
    THREE_AXIS_E2E_OPERATION,
    ThreeAxisE2ERequest,
    ThreeAxisE2EResponse,
)
from bridges.axis1_execution_bridge import execute_axis1_request
from axes.axis2_selection.snapshots.exact_asof import (
    ExactAsOfSnapshotError,
    PointInTimeSnapshot,
)
from axes.axis2_selection.engine.selection import (
    Axis2SelectionEngine,
    SelectionError,
    SelectionSpec,
)
from axes.axis3_monetization.crud.versioned_store import (
    Axis3StoreError,
    VersionedArtifactStore,
)
from axes.axis3_monetization.orchestration.run_plan import (
    Axis3OrchestrationError,
    build_strategy_run_plan,
)


class ThreeAxisE2EBridge:
    @staticmethod
    def _response_meta(request: ThreeAxisE2ERequest, status: str) -> BridgeResponseMeta:
        return BridgeResponseMeta(
            request_id=request.meta.request_id,
            source_axis="AXIS3",
            target_axis=request.meta.source_axis,
            operation=THREE_AXIS_E2E_OPERATION,
            status=status,
        )

    @staticmethod
    def _selection_spec(payload: Mapping[str, Any]) -> SelectionSpec:
        raw = dict(payload)
        supplied_hash = raw.pop("selection_hash", None)
        if supplied_hash is None:
            raise SelectionError("selection_hash is required", "SELECTION_HASH_REQUIRED")
        spec = SelectionSpec.from_dict(raw)
        if str(supplied_hash) != spec.selection_hash:
            raise SelectionError("selection_hash mismatch", "SELECTION_HASH_MISMATCH")
        return spec

    @staticmethod
    def _axis1_request(
        request: ThreeAxisE2ERequest,
        intent: Mapping[str, Any],
    ) -> Axis1ExecutionRequest:
        symbol = str(intent["symbol"])
        ordinal = int(intent["candidate_ordinal"])
        if symbol not in request.execution_inputs:
            raise BridgeContractError(
                f"execution input missing for selected candidate: {symbol}",
                "BRIDGE_E2E_EXECUTION_INPUT_MISSING",
            )
        execution_input = request.execution_inputs[symbol]
        raw = {
            "schema": AXIS1_EXECUTION_REQUEST_SCHEMA,
            "meta": {
                "request_id": f"{request.meta.request_id}:axis1:{ordinal}:{symbol}",
                "source_axis": "AXIS3",
                "target_axis": "AXIS1",
                "operation": AXIS1_OPERATION,
                "contract_version": "v1",
            },
            "instrument": {
                "symbol": symbol,
                "timeframe": str(intent["timeframe"]),
            },
            "strategy": {
                "strategy_id": str(intent["strategy_id"]),
                "strategy_version": str(intent["strategy_version"]),
                "dsl_code": str(intent["dsl_code"]),
            },
            "market": execution_input["market"],
            "settings": intent["settings"],
            "entry_gate": execution_input.get("entry_gate"),
            "parent_context": execution_input.get("parent_context"),
        }
        return Axis1ExecutionRequest.from_dict(raw)

    @classmethod
    def execute(
        cls,
        store: VersionedArtifactStore,
        raw_request: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Execute one fully versioned selection -> plan -> backtest pipeline.

        Malformed outer envelopes raise BridgeContractError before any axis is
        called.  Once structurally valid, axis/domain failures become a
        structured REJECTED response with the completed trace preserved.
        """
        request = ThreeAxisE2ERequest.from_dict(raw_request)
        trace: dict[str, Any] = {
            "axis2_candidate_set": None,
            "axis3_run_plan": None,
            "axis1_executions": [],
        }
        try:
            if not isinstance(store, VersionedArtifactStore):
                raise Axis3OrchestrationError(
                    "store must be VersionedArtifactStore", "BAD_STORE"
                )

            snapshot = PointInTimeSnapshot.from_dict(request.snapshot)
            selection_spec = cls._selection_spec(request.selection_spec)
            candidate_set = Axis2SelectionEngine.select(snapshot, selection_spec)
            candidate_payload = candidate_set.public_dict()
            trace["axis2_candidate_set"] = candidate_payload

            strategy_ref = request.strategy_ref
            condition_ref = request.condition_ref
            run_plan = build_strategy_run_plan(
                store,
                run_id=request.run_id,
                strategy_id=str(strategy_ref["strategy_id"]),
                strategy_version=int(strategy_ref["version"]),
                condition_id=str(condition_ref["condition_id"]),
                condition_version=int(condition_ref["version"]),
                candidate_set=candidate_payload,
            )
            if run_plan.strategy_hash != str(strategy_ref["artifact_hash"]):
                raise Axis3OrchestrationError(
                    "strategy artifact_hash does not match requested version",
                    "STRATEGY_HASH_MISMATCH",
                )
            if run_plan.condition_hash != str(condition_ref["artifact_hash"]):
                raise Axis3OrchestrationError(
                    "condition artifact_hash does not match requested version",
                    "CONDITION_HASH_MISMATCH",
                )
            plan_payload = run_plan.public_dict()
            trace["axis3_run_plan"] = plan_payload

            # Preflight every selected candidate before starting AXIS 1 calls so
            # a missing/bad later market input cannot create a partial pipeline.
            axis1_requests = [
                cls._axis1_request(request, intent.public_dict())
                for intent in run_plan.intents
            ]

            rejected_symbols: list[str] = []
            execution_trace: list[dict[str, Any]] = []
            for intent, axis1_request in zip(run_plan.intents, axis1_requests):
                response = execute_axis1_request(axis1_request.public_dict())
                status = str((response.get("meta") or {}).get("status") or "").upper()
                if status != "OK":
                    rejected_symbols.append(intent.symbol)
                execution_trace.append(
                    {
                        "symbol": intent.symbol,
                        "candidate_ordinal": intent.candidate_ordinal,
                        "axis1_request_hash": axis1_request.request_hash,
                        "axis1_response": response,
                    }
                )
            trace["axis1_executions"] = execution_trace

            if rejected_symbols:
                response = ThreeAxisE2EResponse(
                    meta=cls._response_meta(request, "REJECTED"),
                    request_hash=request.request_hash,
                    trace=trace,
                    error={
                        "code": "E2E_AXIS1_EXECUTION_REJECTED",
                        "message": "one or more AXIS 1 executions were rejected",
                        "symbols": rejected_symbols,
                    },
                )
            else:
                response = ThreeAxisE2EResponse(
                    meta=cls._response_meta(request, "OK"),
                    request_hash=request.request_hash,
                    trace=trace,
                )
            return response.public_dict()

        except (
            ExactAsOfSnapshotError,
            SelectionError,
            Axis3StoreError,
            Axis3OrchestrationError,
            BridgeContractError,
            ValueError,
            TypeError,
            ArithmeticError,
        ) as exc:
            code = str(getattr(exc, "code", "E2E_REJECTED"))
            return ThreeAxisE2EResponse(
                meta=cls._response_meta(request, "REJECTED"),
                request_hash=request.request_hash,
                trace=trace,
                error={
                    "code": code,
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            ).public_dict()


def execute_three_axis_request(
    store: VersionedArtifactStore,
    raw_request: Mapping[str, Any],
) -> dict[str, Any]:
    return ThreeAxisE2EBridge.execute(store, raw_request)
