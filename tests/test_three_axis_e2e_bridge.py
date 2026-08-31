from __future__ import annotations

import json
from pathlib import Path
import unittest

from axes.axis2_selection.snapshots.exact_asof import PointInTimeSnapshot
from axes.axis2_selection.engine.selection import SelectionSpec
from axes.axis3_monetization.crud.versioned_store import VersionedArtifactStore
from bridges.contracts.common import BridgeContractError
from bridges.contracts.three_axis_e2e import (
    THREE_AXIS_E2E_REQUEST_SCHEMA,
    THREE_AXIS_E2E_RESPONSE_SCHEMA,
    ThreeAxisE2ERequest,
)
from bridges.three_axis_e2e_bridge import execute_three_axis_request


AS_OF = "20260901090000"
SOURCE = "prepared:e2e-0900"


def snapshot():
    rows = []
    values = (
        ("AAA", 2.4, 1, 100.0),
        ("BBB", 2.1, 2, 66.0),
        ("CCC", 1.7, 3, 33.0),
    )
    for symbol, value, rank, percentile in values:
        rows.append(
            {
                "symbol": symbol,
                "feature_id": "selection.hist_normalized",
                "value_type": "NUMBER",
                "value": value,
                "validity": "VALID",
                "provenance": {
                    "source_ref": SOURCE,
                    "observed_as_of": "20260901085900",
                    "knowledge_cutoff": AS_OF,
                    "formula_version": "features-v1",
                },
                "ranking": {
                    "ranking_method": "DESCENDING_DENSE_V1",
                    "eligible_count": 3,
                    "rank": rank,
                    "percentile": percentile,
                    "peer_group_id": "HIGH_BETA",
                },
            }
        )
    return PointInTimeSnapshot.from_dict(
        {
            "schema_version": "axis2_point_in_time_snapshot/v1",
            "snapshot_id": "e2e-snapshot-0900",
            "as_of": AS_OF,
            "knowledge_cutoff": AS_OF,
            "universe_id": "HIGH_BETA-v1",
            "feature_version": "features-v1",
            "source_refs": [SOURCE],
            "rows": rows,
        }
    )


def selection(snap):
    return SelectionSpec.from_dict(
        {
            "schema_version": "axis2_selection_spec/v1",
            "selection_id": "e2e-selection",
            "condition_version": "cond-v1",
            "snapshot_id": snap.snapshot_id,
            "snapshot_hash": snap.snapshot_hash,
            "as_of": AS_OF,
            "knowledge_cutoff": AS_OF,
            "filters": [
                {
                    "rule_id": "hist-percentile",
                    "feature_id": "selection.hist_normalized",
                    "metric": "PERCENTILE",
                    "operator": "GTE",
                    "operand": 50.0,
                    "peer_group_id": "HIGH_BETA",
                }
            ],
            "sort": {
                "feature_id": "selection.hist_normalized",
                "metric": "RANK",
                "direction": "ASC",
                "peer_group_id": "HIGH_BETA",
            },
            "top_n": 2,
            "symbol_scope": None,
        }
    )


def strategy_code(valid=True):
    if not valid:
        return 'strategy "Bad" { timeframe = "15m" broken = }'
    return '''strategy "E2E" {
    timeframe = "15m"
    fast = ta.sma(close, 2)
    slow = ta.sma(close, 3)
    enter = ta.crossover(fast, slow)
    exit = ta.crossunder(fast, slow)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''


def market(symbol):
    close = [100.0, 101.0, 103.0, 102.0, 104.0, 101.0]
    return {
        "time": [
            "20260901090000",
            "20260901091500",
            "20260901093000",
            "20260901094500",
            "20260901100000",
            "20260901101500",
        ],
        "open": [99.8, 100.8, 102.8, 102.2, 103.7, 101.5],
        "high": [100.5, 101.5, 103.5, 102.8, 104.5, 102.0],
        "low": [99.5, 100.4, 102.4, 101.6, 103.4, 100.6],
        "close": close,
        "volume": [1000, 1100, 1200, 1300, 1250, 1400],
        "meta": {"instrument": symbol, "timeframe": "15m", "source": "e2e-test"},
    }


def prepared(*, promote=True, valid_dsl=True):
    snap = snapshot()
    spec = selection(snap)
    store = VersionedArtifactStore()
    condition = store.create_condition(
        condition_id="cond-alpha",
        name="Histogram candidates",
        selection_spec=spec.public_dict(),
        created_at="20260901091000",
    )
    strategy = store.create_strategy(
        strategy_id="strategy-alpha",
        name="E2E strategy",
        timeframe="15m",
        dsl_code=strategy_code(valid_dsl),
        settings={"commission_pct": 0.0, "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        condition_refs=[{"condition_id": condition.condition_id, "version": condition.version}],
        created_at="20260901092000",
    )
    if promote:
        store.transition(
            "CONDITION",
            condition.condition_id,
            condition.version,
            to_status="PROMOTED",
            reason="validated",
            event_time="20260901093000",
        )
        store.transition(
            "STRATEGY",
            strategy.strategy_id,
            strategy.version,
            to_status="PROMOTED",
            reason="validated",
            event_time="20260901093001",
        )
    request = {
        "schema": THREE_AXIS_E2E_REQUEST_SCHEMA,
        "meta": {
            "request_id": "e2e-request-001",
            "source_axis": "EXTERNAL",
            "target_axis": "AXIS3",
            "operation": "SELECT_PLAN_BACKTEST",
            "contract_version": "v1",
        },
        "run_id": "run-e2e-001",
        "strategy_ref": {
            "strategy_id": strategy.strategy_id,
            "version": strategy.version,
            "artifact_hash": strategy.artifact_hash,
        },
        "condition_ref": {
            "condition_id": condition.condition_id,
            "version": condition.version,
            "artifact_hash": condition.artifact_hash,
        },
        "snapshot": snap.public_dict(),
        "selection_spec": spec.public_dict(),
        "execution_inputs": {
            symbol: {"market": market(symbol), "entry_gate": None, "parent_context": None}
            for symbol in ("AAA", "BBB", "CCC")
        },
    }
    return store, request


class ThreeAxisE2EBridgeTests(unittest.TestCase):
    def test_full_pipeline_preserves_axis_authority_order_and_hashes(self):
        store, request = prepared()
        first = execute_three_axis_request(store, request)
        second = execute_three_axis_request(store, request)
        self.assertEqual(first["schema"], THREE_AXIS_E2E_RESPONSE_SCHEMA)
        self.assertEqual(first["meta"]["status"], "OK")
        self.assertEqual(first["request_hash"], second["request_hash"])
        self.assertEqual(first["response_hash"], second["response_hash"])

        trace = first["trace"]
        candidates = trace["axis2_candidate_set"]["candidates"]
        intents = trace["axis3_run_plan"]["intents"]
        executions = trace["axis1_executions"]
        self.assertEqual([item["symbol"] for item in candidates], ["AAA", "BBB"])
        self.assertEqual([item["ordinal"] for item in candidates], [1, 2])
        self.assertEqual([item["symbol"] for item in intents], ["AAA", "BBB"])
        self.assertEqual([item["candidate_ordinal"] for item in executions], [1, 2])
        self.assertTrue(all(item["axis1_response"]["meta"]["status"] == "OK" for item in executions))
        self.assertEqual(
            trace["axis3_run_plan"]["candidate_set_hash"],
            trace["axis2_candidate_set"]["candidate_set_hash"],
        )
        store.close()

    def test_snapshot_or_selection_tamper_is_rejected_before_axis1(self):
        store, request = prepared()
        request["snapshot"]["rows"][0]["value"] = 999.0
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "SNAPSHOT_HASH_MISMATCH")
        self.assertEqual(response["trace"]["axis1_executions"], [])
        store.close()

        store, request = prepared()
        request["selection_spec"]["selection_hash"] = "tampered"
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "SELECTION_HASH_MISMATCH")
        self.assertEqual(response["trace"]["axis1_executions"], [])
        store.close()

    def test_promoted_exact_artifact_hashes_are_required(self):
        store, request = prepared(promote=False)
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "ARTIFACT_NOT_PROMOTED")
        store.close()

        store, request = prepared()
        request["strategy_ref"]["artifact_hash"] = "wrong-strategy-hash"
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "STRATEGY_HASH_MISMATCH")
        self.assertEqual(response["trace"]["axis1_executions"], [])
        store.close()

    def test_all_selected_markets_are_preflighted_before_execution(self):
        store, request = prepared()
        del request["execution_inputs"]["BBB"]
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "BRIDGE_E2E_EXECUTION_INPUT_MISSING")
        self.assertIsNotNone(response["trace"]["axis2_candidate_set"])
        self.assertIsNotNone(response["trace"]["axis3_run_plan"])
        self.assertEqual(response["trace"]["axis1_executions"], [])
        store.close()

    def test_axis1_rejection_is_visible_without_losing_selection_or_plan_trace(self):
        store, request = prepared(valid_dsl=False)
        response = execute_three_axis_request(store, request)
        self.assertEqual(response["meta"]["status"], "REJECTED")
        self.assertEqual(response["error"]["code"], "E2E_AXIS1_EXECUTION_REJECTED")
        self.assertEqual(response["error"]["symbols"], ["AAA", "BBB"])
        self.assertEqual(len(response["trace"]["axis1_executions"]), 2)
        self.assertTrue(
            all(
                item["axis1_response"]["meta"]["status"] == "REJECTED"
                for item in response["trace"]["axis1_executions"]
            )
        )
        self.assertEqual(
            [item["symbol"] for item in response["trace"]["axis2_candidate_set"]["candidates"]],
            ["AAA", "BBB"],
        )
        store.close()

    def test_outer_contract_is_versioned_json_safe_and_fail_closed(self):
        store, request = prepared()
        parsed = ThreeAxisE2ERequest.from_dict(request)
        self.assertEqual(parsed.public_dict(), ThreeAxisE2ERequest.from_dict(parsed.public_dict()).public_dict())
        self.assertEqual(parsed.request_hash, ThreeAxisE2ERequest.from_dict(request).request_hash)

        unknown = dict(request)
        unknown["nearest_time"] = True
        with self.assertRaises(BridgeContractError):
            ThreeAxisE2ERequest.from_dict(unknown)

        opaque = dict(request)
        opaque["execution_inputs"] = dict(request["execution_inputs"])
        opaque["execution_inputs"]["AAA"] = {"market": object()}
        with self.assertRaises(BridgeContractError):
            ThreeAxisE2ERequest.from_dict(opaque)

        nonfinite = dict(request)
        nonfinite["execution_inputs"] = dict(request["execution_inputs"])
        bad_market = dict(request["execution_inputs"]["AAA"]["market"])
        bad_market["close"] = list(bad_market["close"])
        bad_market["close"][0] = float("inf")
        nonfinite["execution_inputs"]["AAA"] = {"market": bad_market}
        with self.assertRaises(BridgeContractError):
            ThreeAxisE2ERequest.from_dict(nonfinite)
        store.close()

    def test_contract_is_data_only_and_bridge_has_no_frozen_or_axis1_internal_import(self):
        import bridges.contracts.three_axis_e2e as contract_module
        import bridges.three_axis_e2e_bridge as bridge_module

        contract_source = Path(contract_module.__file__).read_text(encoding="utf-8")
        bridge_source = Path(bridge_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("axes.", contract_source)
        for token in ("from core", "import core", "axes.axis1_dsl"):
            self.assertNotIn(token, bridge_source)

        contract_dir = Path(contract_module.__file__).parent
        request_schema = json.loads(
            (contract_dir / "three_axis_e2e_request.v1.schema.json").read_text(encoding="utf-8")
        )
        response_schema = json.loads(
            (contract_dir / "three_axis_e2e_response.v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(request_schema["$id"], THREE_AXIS_E2E_REQUEST_SCHEMA)
        self.assertEqual(response_schema["$id"], THREE_AXIS_E2E_RESPONSE_SCHEMA)
        self.assertFalse(request_schema["additionalProperties"])
        self.assertFalse(response_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
