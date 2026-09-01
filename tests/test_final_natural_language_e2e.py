from __future__ import annotations

import copy
from pathlib import Path
import unittest

from acceptance.final_natural_language_scenario import (
    FINAL_USER_REQUEST,
    PROFIT_ASSUMPTION_ID,
    build_scenario,
)
from bridges.three_axis_e2e_bridge import execute_three_axis_request


class FinalNaturalLanguageE2EAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.scenario = build_scenario()

    def tearDown(self):
        self.scenario.close()

    def test_natural_language_is_preserved_and_material_profit_definition_requires_human_acceptance(self):
        self.assertIn(FINAL_USER_REQUEST, self.scenario.prompt)
        self.assertEqual(
            self.scenario.blocked_report.final_status,
            "BLOCKED_USER_CLARIFICATION",
        )
        self.assertEqual(
            self.scenario.blocked_report.final_stage.error_code,
            "MATERIAL_ASSUMPTION_NOT_ACCEPTED",
        )
        self.assertEqual(
            self.scenario.draft["assumptions"][0]["id"],
            PROFIT_ASSUMPTION_ID,
        )
        self.assertEqual(self.scenario.accepted_report.final_status, "ACCEPTED_DRAFT")
        self.assertTrue(all(item.status == "PASS" for item in self.scenario.accepted_report.stages))

    def test_representative_request_runs_through_selection_promoted_artifacts_and_axis1(self):
        response = self.scenario.execute()
        self.assertEqual(response["meta"]["status"], "OK")

        trace = response["trace"]
        candidate_set = trace["axis2_candidate_set"]
        run_plan = trace["axis3_run_plan"]
        executions = trace["axis1_executions"]

        self.assertEqual(
            [item["symbol"] for item in candidate_set["candidates"]],
            ["AAA", "BBB"],
        )
        self.assertEqual(
            [item["ordinal"] for item in candidate_set["candidates"]],
            [1, 2],
        )
        self.assertEqual(candidate_set["candidate_set_hash"], run_plan["candidate_set_hash"])
        self.assertEqual(run_plan["selection_hash"], self.scenario.selection_spec.selection_hash)
        self.assertEqual(run_plan["snapshot_hash"], self.scenario.snapshot.snapshot_hash)
        self.assertEqual(run_plan["intents"][0]["dsl_code"], self.scenario.draft["dsl_code"])
        self.assertEqual([item["candidate_ordinal"] for item in executions], [1, 2])

        for item in executions:
            axis1 = item["axis1_response"]
            self.assertEqual(axis1["meta"]["status"], "OK")
            execution = axis1["result"]["execution"]
            counts = execution["diagnostics"]["signal_counts"]
            self.assertGreaterEqual(counts["entry_now"], 1)
            self.assertGreaterEqual(counts["exit_blocked_now"], 1)
            self.assertGreaterEqual(counts["exit_now"], 1)
            self.assertEqual(execution["metrics_numeric"]["closed_trade_count"], 1)
            self.assertEqual(execution["metrics_numeric"]["open_position"], 0)
            self.assertGreater(execution["closed_trades"][0]["net_pnl"], 0.0)

            indicator_names = {entry["name"] for entry in execution["indicators"]}
            for expected in ("ema120", "hist_strength", "reference_hist", "jma"):
                self.assertIn(expected, indicator_names)

    def test_reference_hist_evidence_matches_exact_read_only_axis1_context_and_hash_trace(self):
        response = self.scenario.execute()
        candidate_set = response["trace"]["axis2_candidate_set"]
        executions = response["trace"]["axis1_executions"]
        by_symbol = {item["symbol"]: item for item in executions}

        for candidate in candidate_set["candidates"]:
            symbol = candidate["symbol"]
            evidence = next(
                item
                for item in candidate["evidence"]
                if item["feature_id"] == "selection.reference_hist"
            )
            prepared = self.scenario.request["execution_inputs"][symbol]["parent_context"]
            values = prepared["feature_values"]["selection.reference_hist"]
            self.assertTrue(values)
            self.assertTrue(all(float(value) == float(evidence["observed"]) for value in values))

            diagnostics = (
                by_symbol[symbol]["axis1_response"]["result"]["execution"]["diagnostics"]
                ["parent_context"]
            )
            self.assertTrue(diagnostics["supplied"])
            self.assertEqual(diagnostics["target_symbol"], symbol)
            self.assertEqual(diagnostics["binding_hash"], prepared["binding_hash"])
            self.assertEqual(diagnostics["registry_hash"], self.scenario.manifest.manifest_hash)
            self.assertEqual(diagnostics["feature_ids"], ["selection.reference_hist"])

    def test_same_inputs_are_deterministic_and_context_tamper_fails_before_any_axis1_execution(self):
        first = self.scenario.execute()
        second = self.scenario.execute()
        self.assertEqual(first["request_hash"], second["request_hash"])
        self.assertEqual(first["response_hash"], second["response_hash"])

        tampered = copy.deepcopy(self.scenario.request)
        values = tampered["execution_inputs"]["BBB"]["parent_context"]["feature_values"]
        values["selection.reference_hist"][0] = float(values["selection.reference_hist"][0]) + 0.001
        rejected = execute_three_axis_request(self.scenario.store, tampered)
        self.assertEqual(rejected["meta"]["status"], "REJECTED")
        self.assertEqual(
            rejected["error"]["code"],
            "BRIDGE_CONTEXT_BINDING_HASH_MISMATCH",
        )
        self.assertIsNotNone(rejected["trace"]["axis2_candidate_set"])
        self.assertIsNotNone(rejected["trace"]["axis3_run_plan"])
        self.assertEqual(rejected["trace"]["axis1_executions"], [])

    def test_final_acceptance_adds_no_strategy_shortcut_to_axis_cores_or_frozen_core(self):
        import acceptance.final_natural_language_scenario as scenario_module
        import bridges.three_axis_e2e_bridge as bridge_module

        scenario_source = Path(scenario_module.__file__).read_text(encoding="utf-8")
        bridge_source = Path(bridge_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", scenario_source)
        self.assertNotIn("import core", scenario_source)
        self.assertNotIn("axes.axis1_dsl", bridge_source)
        self.assertIn("preflight_axis1_request", bridge_source)

        # Historical event search is data evidence in the acceptance fixture,
        # never a single-instrument DSL/provider shortcut.
        dsl = self.scenario.draft["dsl_code"]
        for forbidden in ("universe", "provider", "nearest_time", "fill_forward"):
            self.assertNotIn(forbidden, dsl)
        self.assertIn("ctx.selection.reference_hist", dsl)


if __name__ == "__main__":
    unittest.main()
