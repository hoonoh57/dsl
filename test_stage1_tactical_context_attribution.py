from copy import deepcopy
import unittest

from core.battlefield_context import BattlefieldContext, ContextLayerSnapshot
from core.tactical_context_attribution import (
    ContextDeploymentPolicy,
    ContextSliceRule,
    TacticalContextAttributor,
)


def profile():
    rows = [
        {
            "case_id": "C1",
            "knowledge_cutoff": "20260824093000",
            "return_pct": -1.0,
            "mdd_pct": -2.0,
            "closed_trade_count": 2,
            "total_cost": 20.0,
            "mfe_giveback_pct": 1.4,
        },
        {
            "case_id": "C2",
            "knowledge_cutoff": "20260825093000",
            "return_pct": 2.0,
            "mdd_pct": -0.5,
            "closed_trade_count": 2,
            "total_cost": 10.0,
            "mfe_giveback_pct": 0.4,
        },
        {
            "case_id": "C3",
            "knowledge_cutoff": "20260826093000",
            "return_pct": -0.5,
            "mdd_pct": -1.2,
            "closed_trade_count": 1,
            "total_cost": 15.0,
            "mfe_giveback_pct": 1.0,
        },
        {
            "case_id": "C4",
            "knowledge_cutoff": "20260827093000",
            "return_pct": 1.5,
            "mdd_pct": -0.4,
            "closed_trade_count": 1,
            "total_cost": 8.0,
            "mfe_giveback_pct": 0.3,
        },
    ]
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {"candidate_hash": "candidate-jma-g3"},
        "case_set_hash": "neutral-frozen-cases",
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "results": rows,
        "run_hash": "trusted-neutral-run",
    }


def observed_context(date, state, strength):
    timestamp = f"{date}092959"
    return BattlefieldContext(
        as_of=timestamp,
        mode="OBSERVED",
        layers=(
            ContextLayerSnapshot(
                layer="MARKET",
                context_id="KOSPI_REGIME",
                as_of=timestamp,
                source="fixture://kospi",
                features={"state": state, "strength": strength},
            ),
        ),
    )


def deployment_context(date, state, strength):
    timestamp = f"{date}092959"
    return BattlefieldContext(
        as_of=timestamp,
        mode="DEPLOYMENT",
        layers=(
            ContextLayerSnapshot(
                layer="MARKET",
                context_id="KOSPI_REGIME",
                as_of=timestamp,
                source="fixture://kospi",
                features={"state": state, "strength": strength},
            ),
        ),
    )


def contexts():
    return {
        "C1": observed_context("20260824", "RISK_OFF", -0.4),
        "C2": observed_context("20260825", "RISK_ON", 0.8),
        "C3": observed_context("20260826", "RISK_OFF", -0.1),
        "C4": observed_context("20260827", "RISK_ON", 0.6),
    }


class TacticalContextAttributionTests(unittest.TestCase):
    def test_observed_context_is_attributed_without_rewriting_micro_profile(self):
        original = profile()
        before = deepcopy(original)
        rule = ContextSliceRule(
            slice_id="KOSPI_RISK_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        result = TacticalContextAttributor.attribute(
            profile=original,
            contexts=contexts(),
            rules=(rule,),
        )

        self.assertEqual(original, before)
        self.assertEqual(result["schema"], "tactical_context_attribution/v1")
        self.assertEqual(result["mutation_policy"], "HISTORICAL_MICRO_PROFILE_READ_ONLY")
        self.assertEqual(result["deployment_policy"], "ATTRIBUTION_ONLY_NO_ENTRY_AUTHORITY")
        self.assertEqual(result["baseline"]["cases"], 4)
        self.assertAlmostEqual(result["baseline"]["average_return_pct"], 0.5)
        risk_on = result["slices"][0]
        self.assertEqual(risk_on["matched_case_ids"], ("C2", "C4"))
        self.assertEqual(risk_on["summary"]["cases"], 2)
        self.assertAlmostEqual(risk_on["summary"]["average_return_pct"], 1.75)
        self.assertAlmostEqual(risk_on["incremental_vs_all"]["average_return_pct"], 1.25)
        self.assertAlmostEqual(risk_on["retained_case_rate"], 0.5)
        self.assertNotIn("score", result)
        self.assertNotIn("best", result)

    def test_rule_and_context_input_order_do_not_change_attribution_identity(self):
        state_rule = ContextSliceRule(
            slice_id="STATE_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        strength_rule = ContextSliceRule(
            slice_id="STRENGTH_GT_HALF",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="strength",
            operator="GT",
            value=0.5,
        )
        normal = contexts()
        reverse = dict(reversed(list(normal.items())))
        first = TacticalContextAttributor.attribute(
            profile=profile(), contexts=normal, rules=(state_rule, strength_rule)
        )
        second = TacticalContextAttributor.attribute(
            profile=profile(), contexts=reverse, rules=(strength_rule, state_rule)
        )
        self.assertEqual(first["attribution_hash"], second["attribution_hash"])
        self.assertEqual(first["slices"], second["slices"])

    def test_context_coverage_and_causality_fail_closed(self):
        missing = contexts()
        missing.pop("C4")
        rule = ContextSliceRule(
            slice_id="RISK_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        with self.assertRaisesRegex(ValueError, "coverage"):
            TacticalContextAttributor.attribute(profile=profile(), contexts=missing, rules=(rule,))

        future = contexts()
        future["C1"] = BattlefieldContext(
            as_of="20260824093100",
            mode="OBSERVED",
            layers=(
                ContextLayerSnapshot(
                    layer="MARKET",
                    context_id="KOSPI_REGIME",
                    as_of="20260824093100",
                    source="fixture://future",
                    features={"state": "RISK_ON", "strength": 1.0},
                ),
            ),
        )
        with self.assertRaisesRegex(ValueError, "knowledge cutoff"):
            TacticalContextAttributor.attribute(profile=profile(), contexts=future, rules=(rule,))

    def test_attribution_requires_neutral_micro_baseline(self):
        non_neutral = profile()
        non_neutral["context_policy"]["require_neutral_context"] = False
        rule = ContextSliceRule(
            slice_id="RISK_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        with self.assertRaisesRegex(ValueError, "NEUTRAL"):
            TacticalContextAttributor.attribute(
                profile=non_neutral,
                contexts=contexts(),
                rules=(rule,),
            )

    def test_deployment_policy_is_explicit_evidence_and_not_execution_wiring(self):
        rule = ContextSliceRule(
            slice_id="RISK_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        policy = ContextDeploymentPolicy(
            policy_id="JMA_RISK_ON_ONLY",
            policy_version="v1",
            tactic_id="candidate-jma-g3",
            rule=rule,
            attribution_hash="attribution-evidence-hash",
            evidence_status="RESEARCH_ONLY",
            priority_if_allowed=1.0,
        )
        allowed = policy.decide(deployment_context("20260827", "RISK_ON", 0.7))
        self.assertTrue(allowed["decision"]["allowed"])
        self.assertEqual(allowed["decision"]["eligible_tactics"], ("candidate-jma-g3",))
        self.assertFalse(allowed["operational_authority"])
        self.assertEqual(
            allowed["execution_integration"],
            "NOT_WIRED_TO_DSL_ENTRY_GATE_OR_BROKER",
        )

        blocked = policy.decide(deployment_context("20260827", "RISK_OFF", -0.2))
        self.assertFalse(blocked["decision"]["allowed"])
        self.assertEqual(blocked["decision"]["blocked_tactics"], ("candidate-jma-g3",))

        with self.assertRaisesRegex(ValueError, "DEPLOYMENT"):
            policy.decide(observed_context("20260827", "RISK_ON", 0.7))

    def test_validated_deployment_status_requires_separate_validation_evidence(self):
        rule = ContextSliceRule(
            slice_id="RISK_ON",
            layer="MARKET",
            context_id="KOSPI_REGIME",
            feature_key="state",
            operator="EQ",
            value="RISK_ON",
        )
        with self.assertRaisesRegex(ValueError, "validation_evidence_hash"):
            ContextDeploymentPolicy(
                policy_id="VALIDATED_POLICY",
                policy_version="v1",
                tactic_id="candidate-jma-g3",
                rule=rule,
                attribution_hash="attr",
                evidence_status="VALIDATED",
            ).validate()


if __name__ == "__main__":
    unittest.main()
