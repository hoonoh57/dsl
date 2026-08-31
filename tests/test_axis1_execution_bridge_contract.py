from __future__ import annotations

from pathlib import Path
import unittest

from bridges.axis1_execution_bridge import _result_json_safe, execute_axis1_request
from bridges.contracts.axis1_execution import (
    AXIS1_EXECUTION_REQUEST_SCHEMA,
    AXIS1_EXECUTION_RESPONSE_SCHEMA,
    Axis1ExecutionRequest,
)
from bridges.contracts.common import BridgeContractError, stable_hash
from axes.axis1_dsl.core.capability_diagnostic_registry import registry_hash


def market_fixture():
    close = [100.0, 101.0, 102.0, 101.5, 103.0, 104.0]
    return {
        "time": [
            "20260901090000",
            "20260901090500",
            "20260901091000",
            "20260901091500",
            "20260901092000",
            "20260901092500",
        ],
        "open": close,
        "high": [value + 1.0 for value in close],
        "low": [value - 1.0 for value in close],
        "close": close,
        "volume": [1000.0, 1100.0, 1200.0, 1150.0, 1300.0, 1400.0],
        "meta": {"source": "bridge-contract-test"},
    }


def request_fixture(*, dsl_code=None, entry_gate=None, parent_context=None):
    code = dsl_code or '''strategy "BridgeContract" {
    timeframe = "5m"
    fast = ta.sma(close, 2)
    slow = ta.sma(close, 3)
    enter = ta.crossover(fast, slow)
    exit = ta.crossunder(fast, slow)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''
    return {
        "schema": AXIS1_EXECUTION_REQUEST_SCHEMA,
        "meta": {
            "request_id": "req-bridge-001",
            "source_axis": "AXIS3",
            "target_axis": "AXIS1",
            "operation": "BACKTEST",
            "contract_version": "v1",
        },
        "instrument": {"symbol": "TEST", "timeframe": "5m"},
        "strategy": {
            "strategy_id": "strategy-1",
            "strategy_version": "v3",
            "dsl_code": code,
        },
        "market": market_fixture(),
        "settings": {"commission_pct": 0.0, "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        "entry_gate": entry_gate,
        "parent_context": parent_context,
    }


class Axis1ExecutionBridgeContractTests(unittest.TestCase):
    def test_request_contract_is_versioned_deterministic_and_fail_closed(self):
        request = request_fixture(entry_gate=[True] * 6)
        parsed = Axis1ExecutionRequest.from_dict(request)
        self.assertEqual(parsed.public_dict()["schema"], AXIS1_EXECUTION_REQUEST_SCHEMA)
        self.assertEqual(parsed.meta.target_axis.upper(), "AXIS1")
        first_hash = parsed.request_hash

        reordered = dict(reversed(list(request.items())))
        self.assertEqual(Axis1ExecutionRequest.from_dict(reordered).request_hash, first_hash)

        bad = dict(request)
        bad["unknown_internal_state"] = {"object": "not allowed"}
        with self.assertRaises(BridgeContractError) as ctx:
            Axis1ExecutionRequest.from_dict(bad)
        self.assertEqual(ctx.exception.code, "BRIDGE_UNKNOWN_FIELD")

    def test_contract_rejects_opaque_and_nonfinite_input(self):
        request = request_fixture()
        request["settings"] = {"opaque": object()}
        with self.assertRaises(BridgeContractError) as ctx:
            Axis1ExecutionRequest.from_dict(request)
        self.assertEqual(ctx.exception.code, "BRIDGE_OPAQUE_VALUE")

        request = request_fixture()
        request["market"] = dict(request["market"])
        request["market"]["close"] = list(request["market"]["close"])
        request["market"]["close"][2] = float("nan")
        with self.assertRaises(BridgeContractError) as ctx:
            Axis1ExecutionRequest.from_dict(request)
        self.assertEqual(ctx.exception.code, "BRIDGE_BAD_MARKET_VALUE")

    def test_parent_context_must_match_symbol_and_market_times_exactly(self):
        market = market_fixture()
        context = {
            "schema": "dsl_parent_context_series/v1",
            "target_symbol": "TEST",
            "target_times": list(market["time"]),
            "frame_hash": "frame-1",
            "registry_hash": "selection-registry-1",
            "feature_types": {"selection.reference_strength": "NUMBER"},
            "feature_values": {"selection.reference_strength": [1.0] * 6},
        }
        parsed = Axis1ExecutionRequest.from_dict(request_fixture(parent_context=context))
        self.assertEqual(parsed.parent_context["target_times"], market["time"])

        wrong_time = dict(context)
        wrong_time["target_times"] = list(context["target_times"])
        wrong_time["target_times"][3] = "20260901091600"
        with self.assertRaises(BridgeContractError) as ctx:
            Axis1ExecutionRequest.from_dict(request_fixture(parent_context=wrong_time))
        self.assertEqual(ctx.exception.code, "BRIDGE_CONTEXT_TIME_MISMATCH")

        wrong_symbol = dict(context)
        wrong_symbol["target_symbol"] = "OTHER"
        with self.assertRaises(BridgeContractError) as ctx:
            Axis1ExecutionRequest.from_dict(request_fixture(parent_context=wrong_symbol))
        self.assertEqual(ctx.exception.code, "BRIDGE_CONTEXT_SYMBOL_MISMATCH")

    def test_bridge_executes_through_axis1_facade_and_returns_versioned_response(self):
        request = request_fixture(entry_gate=[False] * 6)
        parsed = Axis1ExecutionRequest.from_dict(request)
        response = execute_axis1_request(request)

        self.assertEqual(response["schema"], AXIS1_EXECUTION_RESPONSE_SCHEMA)
        self.assertEqual(response["meta"]["status"], "OK")
        self.assertEqual(response["meta"]["source_axis"], "AXIS1")
        self.assertEqual(response["meta"]["target_axis"], "AXIS3")
        self.assertEqual(response["request_hash"], parsed.request_hash)
        self.assertEqual(response["capability_registry_hash"], registry_hash())
        self.assertEqual(response["result"]["strategy_ref"]["strategy_id"], "strategy-1")
        execution = response["result"]["execution"]
        self.assertEqual(execution["diagnostics"]["entry_policy"]["higher_layer_gate_supplied"], True)
        self.assertEqual(execution["metrics_numeric"]["trade_count"], 0)
        self.assertEqual(response["response_hash"], stable_hash({key: value for key, value in response.items() if key != "response_hash"}))

    def test_valid_envelope_with_bad_axis1_dsl_returns_rejected_response(self):
        request = request_fixture(dsl_code='''strategy "Bad" {
    timeframe = "5m"
    value = ta.this_function_does_not_exist(close)
}''')
        response = execute_axis1_request(request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertIsNone(response["result"])
        self.assertEqual(response["error"]["code"], "AXIS1_EXECUTION_REJECTED")
        self.assertTrue(response["error"]["message"])

    def test_nonfinite_execution_output_is_explicitly_tagged_not_defaulted(self):
        self.assertEqual(_result_json_safe(float("inf")), {"$number": "Infinity"})
        self.assertEqual(_result_json_safe(float("-inf")), {"$number": "-Infinity"})
        self.assertEqual(_result_json_safe(float("nan")), {"$number": "NaN"})

    def test_bridge_contracts_are_data_only_and_no_cross_axis_internal_import_leaks(self):
        import bridges.contracts.common as common
        import bridges.contracts.axis1_execution as contract
        import bridges.axis1_execution_bridge as adapter

        for module in (common, contract):
            text = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from axes.", text)
            self.assertNotIn("import axes.", text)
            self.assertNotIn("from core", text)
            self.assertNotIn("import core", text)

        adapter_text = Path(adapter.__file__).read_text(encoding="utf-8")
        self.assertNotIn("axes.axis2", adapter_text)
        self.assertNotIn("axes.axis3", adapter_text)
        self.assertNotIn("from core", adapter_text)
        self.assertNotIn("import core", adapter_text)
        self.assertIn("axes.axis1_dsl.execution.axis1_backtest", adapter_text)


if __name__ == "__main__":
    unittest.main()
