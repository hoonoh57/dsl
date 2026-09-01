from __future__ import annotations

from pathlib import Path
import unittest

from authoring.external_llm.manifest import build_authoring_manifest
from authoring.external_llm.prompt_builder import build_correction_prompt, build_initial_prompt
from authoring.external_llm.validator import (
    build_validation_event,
    validate_external_draft,
    validation_errors,
)
from authoring.external_llm.workflow import AuthoringWorkflowError, HumanMediatedAuthoringSession


VALID_DSL = '''strategy "Authoring" {
    timeframe = "15m"
    basis = ta.ema(close, 5)
    enter = ta.crossover(close, basis)
    exit = ta.crossunder(close, basis)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''


def manifest():
    return build_authoring_manifest(
        feature_ids=(
            "selection.high_beta",
            "selection.hist_normalized",
            "market.regime_id",
        ),
        data_source_ids=("pit:market:v1", "pit:selection:v1"),
        context_feature_types={"selection.reference_hist": "NUMBER"},
    )


def draft(**changes):
    value = {
        "schema_version": "external_strategy_draft/v1",
        "request_id": "req-1",
        "intent_summary": "Use deterministic selection evidence and a 15m EMA crossover strategy.",
        "assumptions": [],
        "unresolved_questions": [],
        "needs_capability": [],
        "selection_plan": {
            "as_of_policy": "point_in_time",
            "lookback": {},
            "universe": {"feature_id": "selection.high_beta", "required": True},
            "filters": [
                {
                    "feature_id": "selection.hist_normalized",
                    "operator": "GTE",
                    "value": 1.0,
                    "data_source_id": "pit:selection:v1",
                }
            ],
            "rankings": [],
            "candidate_output": {},
            "evidence_required": [],
        },
        "strategy_plan": {
            "timeframe": "15m",
            "inputs": {},
            "entry": ["EMA crossover"],
            "exit": ["EMA crossunder"],
            "risk": [],
            "state": [],
            "context_dependencies": [],
        },
        "dsl_code": VALID_DSL,
        "projection_requests": ["basis", "enter", "exit"],
        "data_dependencies": ["pit:selection:v1"],
        "rationale": [],
    }
    value.update(changes)
    return value


class ExternalLLMAuthoringLaneTests(unittest.TestCase):
    def test_prompt_is_generated_from_current_machine_registry_and_exact_data_manifest(self):
        current = manifest()
        self.assertIn("dsl.user_functions", current.supported_capability_ids)
        self.assertIn("dsl.bounded_loops", current.supported_capability_ids)
        self.assertIn("dsl.multi_output", current.supported_capability_ids)
        self.assertIn("runtime.intrabar_state", current.supported_capability_ids)
        self.assertIn("execution.partial_fills", current.supported_capability_ids)
        self.assertIn("execution.pyramiding", current.supported_capability_ids)
        self.assertIn("execution.hedging", current.unavailable_capability_ids)
        self.assertIn("ta.sma", current.supported_function_names)

        text = build_initial_prompt(
            request_id="req-1",
            user_request="고베타 후보에서 15분 전략을 작성",
            manifest=current,
        )
        self.assertIn("고베타 후보에서 15분 전략을 작성", text)
        self.assertIn(current.capability_registry_hash, text)
        self.assertIn(current.manifest_hash, text)
        self.assertIn("selection.hist_normalized", text)
        self.assertIn("pit:selection:v1", text)
        self.assertIn("selection.reference_hist", text)
        self.assertIn('"$id": "external_strategy_draft/v1"', text)

    def test_valid_draft_passes_full_deterministic_pipeline_without_execution_or_persistence(self):
        report = validate_external_draft(draft(), request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_status, "ACCEPTED_DRAFT")
        self.assertTrue(report.accepted)
        self.assertEqual(
            [item.stage for item in report.stages],
            [
                "SCHEMA",
                "CAPABILITY",
                "DATA_SOURCE",
                "AXIS_BOUNDARY",
                "TIMEFRAME_CAUSALITY",
                "DSL_PARSER",
                "DSL_SEMANTIC",
                "COMPILE_DRY_RUN",
                "PERSISTENCE",
                "ACCEPTANCE",
            ],
        )
        self.assertTrue(all(item.status == "PASS" for item in report.stages))

    def test_unavailable_capability_is_explicitly_blocked_and_unknown_capability_is_corrected(self):
        blocked = draft(
            needs_capability=[
                {
                    "capability_id": "execution.hedging",
                    "reason": "Simultaneous long and short exposure requested.",
                }
            ]
        )
        report = validate_external_draft(blocked, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_status, "BLOCKED_NEEDS_CAPABILITY")
        self.assertEqual(report.final_stage.error_code, "BLOCKED_NEEDS_CAPABILITY")

        invented = draft(
            needs_capability=[
                {"capability_id": "dsl.magic_future_reader", "reason": "invented"}
            ]
        )
        report = validate_external_draft(invented, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_status, "REQUIRES_CORRECTION")
        self.assertEqual(report.final_stage.error_code, "UNKNOWN_CAPABILITY")

    def test_unknown_feature_data_context_and_noncausal_lookup_fail_closed(self):
        unknown_feature = draft()
        unknown_feature["selection_plan"]["filters"][0]["feature_id"] = "selection.invented"
        report = validate_external_draft(unknown_feature, request_id="req-1", manifest=manifest())
        self.assertEqual((report.final_stage.stage, report.final_stage.error_code), ("DATA_SOURCE", "UNKNOWN_FEATURE_ID"))

        unknown_source = draft(data_dependencies=["pit:invented:v9"])
        report = validate_external_draft(unknown_source, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_stage.error_code, "UNKNOWN_DATA_DEPENDENCY")

        unknown_context = draft()
        unknown_context["strategy_plan"]["context_dependencies"] = ["selection.unknown"]
        report = validate_external_draft(unknown_context, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_stage.error_code, "UNKNOWN_CONTEXT_ID")

        noncausal = draft()
        noncausal["selection_plan"]["lookback"] = {"lookup_mode": "nearest_time"}
        report = validate_external_draft(noncausal, request_id="req-1", manifest=manifest())
        self.assertEqual((report.final_stage.stage, report.final_stage.error_code), ("TIMEFRAME_CAUSALITY", "NON_CAUSAL_LOOKUP_MODE"))

    def test_axis_boundary_timeframe_parser_and_semantic_failures_are_classified(self):
        mixed = draft()
        mixed["selection_plan"]["filters"] = [{"entry": "order.buy"}]
        report = validate_external_draft(mixed, request_id="req-1", manifest=manifest())
        self.assertEqual((report.final_stage.stage, report.final_stage.error_code), ("AXIS_BOUNDARY", "BAD_SELECTION_AXIS"))

        mismatch = draft()
        mismatch["strategy_plan"]["timeframe"] = "5m"
        report = validate_external_draft(mismatch, request_id="req-1", manifest=manifest())
        self.assertEqual((report.final_stage.stage, report.final_stage.error_code), ("TIMEFRAME_CAUSALITY", "BAD_STRATEGY_TIMEFRAME"))

        parse_bad = draft(dsl_code='strategy "Bad" { timeframe = "15m" ??? }')
        report = validate_external_draft(parse_bad, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_stage.stage, "DSL_PARSER")

        semantic_bad = draft(
            dsl_code='''strategy "BadSemantic" {
    timeframe = "15m"
    x = unknown_symbol + 1
}'''
        )
        report = validate_external_draft(semantic_bad, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_stage.stage, "DSL_SEMANTIC")
        self.assertEqual(report.final_stage.error_code, "UNDEFINED_SYMBOL")

    def test_material_assumptions_require_explicit_human_acceptance(self):
        value = draft(
            assumptions=[{"id": "A1", "text": "Use the latest qualifying reference event.", "material": True}]
        )
        blocked = validate_external_draft(value, request_id="req-1", manifest=manifest())
        self.assertEqual(blocked.final_status, "BLOCKED_USER_CLARIFICATION")
        self.assertEqual(blocked.final_stage.error_code, "MATERIAL_ASSUMPTION_NOT_ACCEPTED")

        accepted = validate_external_draft(
            value,
            request_id="req-1",
            manifest=manifest(),
            accepted_assumption_ids=("A1",),
        )
        self.assertEqual(accepted.final_status, "ACCEPTED_DRAFT")

    def test_correction_prompt_preserves_request_and_exact_validator_error(self):
        value = draft()
        value["selection_plan"]["filters"][0]["feature_id"] = "selection.invented"
        report = validate_external_draft(value, request_id="req-1", manifest=manifest())
        prompt = build_correction_prompt(
            request_id="req-1",
            user_request="원래 사용자 요청",
            previous_draft=report.draft,
            errors=validation_errors(report),
            manifest=manifest(),
        )
        self.assertIn("원래 사용자 요청", prompt)
        self.assertIn('"request_id": "req-1"', prompt)
        self.assertIn("UNKNOWN_FEATURE_ID", prompt)
        self.assertIn("selection.invented", prompt)
        self.assertIn("change only", prompt.lower())

    def test_validation_event_and_bounded_human_loop_are_deterministic(self):
        current = manifest()
        session = HumanMediatedAuthoringSession(
            request_id="req-1",
            user_request="15분 전략 작성",
            manifest=current,
            max_iterations=1,
        )
        value = draft()
        value["selection_plan"]["filters"][0]["feature_id"] = "selection.invented"
        report, correction = session.submit(value)
        self.assertEqual(report.final_status, "REQUIRES_CORRECTION")
        self.assertIsNotNone(correction)
        with self.assertRaises(AuthoringWorkflowError) as ctx:
            session.submit(draft())
        self.assertEqual(ctx.exception.code, "ITERATION_LIMIT")

        event1 = build_validation_event(
            report,
            iteration=0,
            occurred_at="20260901090000",
            user_request_hash=session.user_request_hash,
        )
        event2 = build_validation_event(
            report,
            iteration=0,
            occurred_at="20260901090000",
            user_request_hash=session.user_request_hash,
        )
        self.assertEqual(event1, event2)
        self.assertEqual(event1["schema_version"], "authoring_validation_event/v1")
        self.assertEqual(event1["validation"]["error_code"], "UNKNOWN_FEATURE_ID")
        self.assertEqual(event1["resolution"]["resolution_class"], "PROMPT_CORRECTION")

    def test_schema_and_import_boundaries_reject_untrusted_or_cross_axis_authority(self):
        bad = draft(extra=True)
        report = validate_external_draft(bad, request_id="req-1", manifest=manifest())
        self.assertEqual((report.final_stage.stage, report.final_stage.error_code), ("SCHEMA", "UNKNOWN_FIELD"))

        nonfinite = draft()
        nonfinite["strategy_plan"]["inputs"] = {"x": float("inf")}
        report = validate_external_draft(nonfinite, request_id="req-1", manifest=manifest())
        self.assertEqual(report.final_stage.error_code, "NONFINITE_VALUE")

        import authoring.external_llm.validator as validator_module
        import authoring.external_llm.workflow as workflow_module

        source = Path(validator_module.__file__).read_text(encoding="utf-8") + Path(workflow_module.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "axes.axis2_selection",
            "axes.axis3_monetization",
            "from core",
            "import core",
            "execute_axis1_request",
            "three_axis_e2e_bridge",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
