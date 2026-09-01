from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from authoring.continuous_improvement.analyzer import (
    ImprovementAnalysisError,
    analyze_validation_events,
    validate_validation_event,
)
from authoring.external_llm.validator import (
    StageResult,
    ValidationReport,
    build_validation_event,
)


def stable_hash(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_event(
    request_id,
    iteration,
    *,
    stage="ACCEPTANCE",
    status="PASS",
    error_code=None,
    cause="UNKNOWN",
    final_status="ACCEPTED_DRAFT",
    capability_id=None,
    feature_id=None,
    data_source_id=None,
    prompt_version=None,
    user_request_hash=None,
):
    result = StageResult(
        stage=stage,
        status=status,
        error_code=error_code,
        error_message=None if status == "PASS" else f"{error_code} detail",
        root_cause_class=cause,
        capability_id=capability_id,
        feature_id=feature_id,
        data_source_id=data_source_id,
    )
    report = ValidationReport(
        request_id=request_id,
        draft_id=f"{request_id}-draft-{iteration}",
        final_status=final_status,
        stages=(result,),
        draft={},
        manifest_hash="manifest-hash",
    )
    event = build_validation_event(
        report,
        iteration=iteration,
        occurred_at=f"2026090109{iteration:02d}00",
        previous_draft_id=None if iteration == 0 else f"{request_id}-draft-{iteration - 1}",
        user_request_hash=user_request_hash or f"intent-{request_id}",
    )
    if prompt_version is not None:
        event["versions"]["prompt_template_version"] = prompt_version
        body = {key: value for key, value in event.items() if key != "event_id"}
        event["event_id"] = stable_hash(body)
    return event


class AuthoringContinuousImprovementTests(unittest.TestCase):
    def test_report_is_deterministic_order_independent_and_exposes_core_metrics(self):
        events = [
            make_event(
                "r1",
                0,
                stage="SCHEMA",
                status="FAIL",
                error_code="UNKNOWN_FIELD",
                cause="PROMPT_DEFECT",
                final_status="REQUIRES_CORRECTION",
            ),
            make_event("r1", 1),
            make_event("r2", 0),
            make_event(
                "r3",
                0,
                stage="CAPABILITY",
                status="BLOCKED",
                error_code="BLOCKED_NEEDS_CAPABILITY",
                cause="DSL_CAPABILITY_GAP",
                final_status="BLOCKED_NEEDS_CAPABILITY",
                capability_id="dsl.future_generic_feature",
            ),
            make_event(
                "r4",
                0,
                stage="CAPABILITY",
                status="BLOCKED",
                error_code="BLOCKED_NEEDS_CAPABILITY",
                cause="DSL_CAPABILITY_GAP",
                final_status="BLOCKED_NEEDS_CAPABILITY",
                capability_id="dsl.future_generic_feature",
            ),
        ]
        first = analyze_validation_events(events, review_id="review-1")
        second = analyze_validation_events(list(reversed(events)), review_id="review-1")

        self.assertEqual(first.public_dict(), second.public_dict())
        self.assertEqual(first.event_count, 5)
        self.assertEqual(first.request_count, 4)
        self.assertEqual(first.metrics["first_pass_acceptance_rate"], 0.25)
        self.assertEqual(first.metrics["mean_correction_iterations"], 0.25)
        self.assertEqual(first.metrics["capability_block_rate"], 0.4)
        json.dumps(first.public_dict(), allow_nan=False)
        self.assertEqual(first.report_hash, second.report_hash)

        generic = [
            item
            for item in first.recommendations
            if item["root_cause_class"] == "DSL_CAPABILITY_GAP"
        ]
        self.assertEqual(len(generic), 1)
        self.assertEqual(generic[0]["action_class"], "DSL_CAPABILITY_TRANCHE")
        self.assertEqual(generic[0]["independent_intent_count"], 2)
        self.assertTrue(generic[0]["requires_human_approval"])
        self.assertFalse(generic[0]["automatic_mutation"])

    def test_single_intent_repetition_cannot_promote_generic_dsl_change(self):
        events = [
            make_event(
                "same-request",
                0,
                stage="CAPABILITY",
                status="BLOCKED",
                error_code="BLOCKED_NEEDS_CAPABILITY",
                cause="DSL_CAPABILITY_GAP",
                final_status="BLOCKED_NEEDS_CAPABILITY",
                capability_id="dsl.generic_gap",
                user_request_hash="same-intent",
            ),
            make_event(
                "same-request",
                1,
                stage="CAPABILITY",
                status="BLOCKED",
                error_code="BLOCKED_NEEDS_CAPABILITY",
                cause="DSL_CAPABILITY_GAP",
                final_status="BLOCKED_NEEDS_CAPABILITY",
                capability_id="dsl.generic_gap",
                user_request_hash="same-intent",
            ),
        ]
        report = analyze_validation_events(events, review_id="review-single-intent")
        self.assertFalse(any(item["action_class"] == "DSL_CAPABILITY_TRANCHE" for item in report.recommendations))
        deferred = report.deferred_candidates[0]
        self.assertEqual(
            deferred["defer_reason"],
            "INSUFFICIENT_INDEPENDENT_INTENTS_FOR_DSL_CHANGE",
        )
        self.assertEqual(report.metrics["repeat_error_rate"], 0.5)

    def test_repeated_prompt_problem_recommends_narrow_prompt_boundary_first(self):
        events = [
            make_event(
                "p1",
                0,
                stage="SCHEMA",
                status="FAIL",
                error_code="MISSING_FIELD",
                cause="PROMPT_DEFECT",
                final_status="REQUIRES_CORRECTION",
            ),
            make_event(
                "p2",
                0,
                stage="SCHEMA",
                status="FAIL",
                error_code="MISSING_FIELD",
                cause="PROMPT_DEFECT",
                final_status="REQUIRES_CORRECTION",
            ),
        ]
        report = analyze_validation_events(events, review_id="review-prompt")
        self.assertEqual(report.recommendations[0]["action_class"], "PROMPT_WORDING")
        self.assertEqual(report.recommendations[0]["target"], "Prompt wording/examples")
        self.assertFalse(any("DSL" in item["action_class"] for item in report.recommendations))

    def test_version_breakdowns_allow_before_after_failure_comparison(self):
        events = [
            make_event(
                "v1-a",
                0,
                stage="SCHEMA",
                status="FAIL",
                error_code="UNKNOWN_FIELD",
                cause="PROMPT_DEFECT",
                final_status="REQUIRES_CORRECTION",
                prompt_version="prompt-v1",
            ),
            make_event("v1-b", 0, prompt_version="prompt-v1"),
            make_event("v2-a", 0, prompt_version="prompt-v2"),
            make_event("v2-b", 0, prompt_version="prompt-v2"),
        ]
        report = analyze_validation_events(events, review_id="review-version")
        rows = {item["version"]: item for item in report.breakdowns["prompt_template_versions"]}
        self.assertEqual(rows["prompt-v1"]["non_pass_rate"], 0.5)
        self.assertEqual(rows["prompt-v2"]["non_pass_rate"], 0.0)
        self.assertEqual(rows["prompt-v2"]["accepted_count"], 2)

    def test_ambiguous_intent_is_not_misclassified_as_dsl_gap(self):
        events = [
            make_event(
                "a1",
                0,
                stage="ACCEPTANCE",
                status="BLOCKED",
                error_code="UNRESOLVED_QUESTION",
                cause="USER_INTENT_AMBIGUITY",
                final_status="BLOCKED_USER_CLARIFICATION",
            ),
            make_event(
                "a2",
                0,
                stage="ACCEPTANCE",
                status="BLOCKED",
                error_code="MATERIAL_ASSUMPTION_NOT_ACCEPTED",
                cause="USER_INTENT_AMBIGUITY",
                final_status="BLOCKED_USER_CLARIFICATION",
            ),
        ]
        report = analyze_validation_events(events, review_id="review-ambiguity")
        self.assertEqual(report.metrics["ambiguous_intent_rate"], 1.0)
        self.assertEqual(report.recommendations[0]["action_class"], "USER_CLARIFICATION")

    def test_event_tamper_unknown_fields_and_duplicates_fail_closed(self):
        event = make_event("t1", 0)
        validate_validation_event(event)

        tampered = json.loads(json.dumps(event))
        tampered["validation"]["root_cause_class"] = "PROMPT_DEFECT"
        with self.assertRaises(ImprovementAnalysisError) as ctx:
            validate_validation_event(tampered)
        self.assertEqual(ctx.exception.code, "EVENT_HASH_MISMATCH")

        unknown = json.loads(json.dumps(event))
        unknown["raw_user_request"] = "must not be carried into aggregate event contract"
        body = {key: value for key, value in unknown.items() if key != "event_id"}
        unknown["event_id"] = stable_hash(body)
        with self.assertRaises(ImprovementAnalysisError) as ctx:
            validate_validation_event(unknown)
        self.assertEqual(ctx.exception.code, "EVENT_UNKNOWN_FIELD")

        with self.assertRaises(ImprovementAnalysisError) as ctx:
            analyze_validation_events([event, event], review_id="duplicate")
        self.assertEqual(ctx.exception.code, "DUPLICATE_EVENT")

    def test_analysis_layer_is_data_only_and_report_schema_forbids_auto_mutation(self):
        import authoring.continuous_improvement.analyzer as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        forbidden = (
            "axes.axis1_dsl",
            "axes.axis2_selection",
            "axes.axis3_monetization",
            "from core",
            "import core",
            "subprocess",
            "requests.",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

        schema_path = Path(module.__file__).with_name("authoring_improvement_report.v1.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "authoring_improvement_report/v1")
        self.assertFalse(schema["additionalProperties"])
        policy = schema["properties"]["analysis_policy"]["properties"]
        self.assertFalse(policy["automatic_mutation"]["const"])
        self.assertTrue(policy["human_approval_required"]["const"])


if __name__ == "__main__":
    unittest.main()
