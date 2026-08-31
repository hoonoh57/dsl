"""Bridge adapter that owns the only Step 7 call into AXIS 1 execution.

External axes pass versioned JSON-safe data.  The adapter validates the contract,
constructs AXIS 1-owned immutable inputs, calls the public AXIS 1 facade, and
returns a versioned JSON-safe response.  No AXIS 1 runtime object crosses back
through the Bridge.
"""
from __future__ import annotations

import math
from numbers import Integral, Real
from typing import Any, Mapping

from bridges.contracts.common import BridgeResponseMeta, json_safe
from bridges.contracts.axis1_execution import Axis1ExecutionRequest, Axis1ExecutionResponse, AXIS1_OPERATION
from axes.axis1_dsl.core.capability_diagnostic_registry import registry_hash
from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding


_NONFINITE_TAG = "$number"


def _result_json_safe(value: Any, *, path: str = "$.result") -> Any:
    """Serialize AXIS 1 output without losing explicit non-finite meaning.

    Input contracts reject NaN/Infinity.  Execution output may legitimately
    contain Infinity (for example profit factor with gains and no losses), so the
    Bridge encodes non-finite output as a tagged JSON object instead of silently
    defaulting it or rejecting an otherwise valid execution.
    """
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        number = float(value)
        if math.isnan(number):
            return {_NONFINITE_TAG: "NaN"}
        if math.isinf(number):
            return {_NONFINITE_TAG: "Infinity" if number > 0 else "-Infinity"}
        return number
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"AXIS 1 result mapping key is invalid at {path}")
            result[key] = _result_json_safe(item, path=f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [
            _result_json_safe(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"AXIS 1 returned an opaque value at {path}: {type(value).__name__}")


class Axis1ExecutionBridge:
    """Versioned BACKTEST Request -> Response boundary for AXIS 1."""

    @staticmethod
    def _context_binding(request: Axis1ExecutionRequest) -> DSLContextSeriesBinding | None:
        payload = request.parent_context
        if payload is None:
            return None
        binding = DSLContextSeriesBinding.from_prepared(
            target_symbol=str(payload["target_symbol"]),
            target_times=payload["target_times"],
            frame_hash=str(payload["frame_hash"]),
            registry_hash=str(payload["registry_hash"]),
            feature_types=payload["feature_types"],
            feature_values=payload["feature_values"],
        )
        supplied_hash = payload.get("binding_hash")
        if supplied_hash is not None and str(supplied_hash) != binding.binding_hash:
            raise ValueError("parent_context binding_hash does not match prepared binding")
        return binding

    @staticmethod
    def _market(request: Axis1ExecutionRequest) -> dict[str, Any]:
        market = {
            key: list(request.market[key])
            for key in ("time", "open", "high", "low", "close", "volume")
        }
        meta = dict(request.market.get("meta") or {})
        supplied_instrument = str(meta.get("instrument") or "").strip()
        supplied_timeframe = str(meta.get("timeframe") or "").strip()
        if supplied_instrument and supplied_instrument != request.symbol:
            raise ValueError("market.meta.instrument conflicts with request instrument.symbol")
        if supplied_timeframe and supplied_timeframe != request.timeframe:
            raise ValueError("market.meta.timeframe conflicts with request instrument.timeframe")
        meta["instrument"] = request.symbol
        meta["timeframe"] = request.timeframe
        market["_meta"] = meta
        return market

    @classmethod
    def execute(cls, raw_request: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and execute one AXIS 1 backtest request.

        Malformed Bridge envelopes fail closed by raising BridgeContractError from
        the contract parser.  Once a request is structurally valid, deterministic
        AXIS 1 validation/execution failures return a structured REJECTED response.
        """
        request = Axis1ExecutionRequest.from_dict(raw_request)
        capability_hash = registry_hash()
        response_meta = lambda status: BridgeResponseMeta(
            request_id=request.meta.request_id,
            source_axis="AXIS1",
            target_axis=request.meta.source_axis,
            operation=AXIS1_OPERATION,
            status=status,
        )
        try:
            result = Axis1BacktestEngine.run(
                request.dsl_code,
                market=cls._market(request),
                data_timeframe=request.timeframe,
                settings=dict(request.settings),
                entry_gate=None if request.entry_gate is None else list(request.entry_gate),
                parent_context_binding=cls._context_binding(request),
            )
            safe_result = _result_json_safe(
                {
                    "strategy_ref": {
                        "strategy_id": request.strategy_id,
                        "strategy_version": request.strategy_version,
                    },
                    "instrument": {
                        "symbol": request.symbol,
                        "timeframe": request.timeframe,
                    },
                    "execution": result,
                }
            )
            response = Axis1ExecutionResponse(
                meta=response_meta("OK"),
                request_hash=request.request_hash,
                capability_registry_hash=capability_hash,
                result=safe_result,
            )
        except (ValueError, TypeError, ArithmeticError) as exc:
            response = Axis1ExecutionResponse(
                meta=response_meta("REJECTED"),
                request_hash=request.request_hash,
                capability_registry_hash=capability_hash,
                error={
                    "code": "AXIS1_EXECUTION_REJECTED",
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            )
        return response.public_dict()


def execute_axis1_request(raw_request: Mapping[str, Any]) -> dict[str, Any]:
    return Axis1ExecutionBridge.execute(raw_request)
