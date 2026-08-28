import unittest
from pathlib import Path

from core.multi_symbol_follower_pending_orchestration import (
    ORCHESTRATION_POLICY,
    FollowerPendingIntentPolicy,
    MultiSymbolFollowerPendingOrchestrator,
)


def policy():
    return FollowerPendingIntentPolicy(
        policy_id="LF2_FOLLOWER_PENDING",
        policy_version="v1",
        client_id_prefix="lf2-pending",
    )


def relation_result():
    return {
        "mode": "OBSERVATION_ONLY",
        "operational_authority": False,
        "result_hash": "lf1-result-hash",
        "leader_symbol": "A",
        "leader_role_qualified": True,
        "top_follow_rate_follower": "B",
        "pairs": (
            {
                "leader_symbol": "A",
                "follower_symbol": "B",
                "follow_rate": 1.0,
                "mean_lag_points": 1.0,
                "qualified": True,
            },
            {
                "leader_symbol": "A",
                "follower_symbol": "C",
                "follow_rate": 0.67,
                "mean_lag_points": 1.5,
                "qualified": True,
            },
        ),
    }


class MultiSymbolFollowerPendingOrchestrationTests(unittest.TestCase):
    def test_qualified_selected_follower_arms_one_stable_pending_identity(self):
        first = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828110000",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=True,
        )
        second = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828110000",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=True,
        )
        self.assertEqual(first["intent"], "ARM_PENDING")
        self.assertEqual(first["selected_follower_symbol"], "B")
        self.assertTrue(first["selection_qualified"])
        self.assertTrue(first["client_order_id"].startswith("lf2-pending:B:"))
        self.assertEqual(first["client_order_id"], second["client_order_id"])
        self.assertEqual(first["evidence_hash"], second["evidence_hash"])
        self.assertEqual(first["mode"], "OBSERVATION_ONLY")
        self.assertFalse(first["operational_authority"])
        self.assertFalse(first["execution_authority"])
        self.assertEqual(first["orchestration_policy"], ORCHESTRATION_POLICY)

    def test_relation_invalidation_cancels_existing_pending_identity(self):
        result = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828110500",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=False,
            pending_order_active=True,
            client_order_id="lf2-pending:B:existing",
        )
        self.assertEqual(result["intent"], "CANCEL_PENDING")
        self.assertEqual(result["client_order_id"], "lf2-pending:B:existing")
        self.assertIn("relation_invalidated", result["reasons"])

    def test_hard_guard_blocks_new_arm_and_cancels_existing_pending(self):
        blocked = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828111000",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=False,
            relation_still_valid=True,
        )
        self.assertEqual(blocked["intent"], "HOLD")
        self.assertIsNone(blocked["client_order_id"])
        self.assertIn("hard_guard_failed", blocked["reasons"])

        canceled = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828111000",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=False,
            relation_still_valid=True,
            pending_order_active=True,
            client_order_id="lf2-pending:B:existing",
        )
        self.assertEqual(canceled["intent"], "CANCEL_PENDING")
        self.assertIn("hard_guard_failed", canceled["reasons"])

    def test_unselected_or_unqualified_follower_cannot_arm(self):
        unselected = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828111500",
            follower_symbol="C",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=True,
        )
        self.assertEqual(unselected["intent"], "HOLD")
        self.assertIn("not_selected_follower", unselected["reasons"])

        weak = relation_result()
        weak["leader_role_qualified"] = False
        result = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=weak,
            policy=policy(),
            as_of="20260828111500",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=True,
        )
        self.assertEqual(result["intent"], "HOLD")
        self.assertIn("no_qualified_relation", result["reasons"])

    def test_fail_closed_on_authority_or_pending_identity_mismatch(self):
        authoritative = relation_result()
        authoritative["operational_authority"] = True
        with self.assertRaisesRegex(ValueError, "operational authority"):
            MultiSymbolFollowerPendingOrchestrator.compose(
                relation_result=authoritative,
                policy=policy(),
                as_of="20260828112000",
                follower_symbol="B",
                local_setup_pass=True,
                hard_guard_pass=True,
                relation_still_valid=True,
            )
        with self.assertRaisesRegex(ValueError, "active client_order_id"):
            MultiSymbolFollowerPendingOrchestrator.compose(
                relation_result=relation_result(),
                policy=policy(),
                as_of="20260828112000",
                follower_symbol="B",
                local_setup_pass=True,
                hard_guard_pass=True,
                relation_still_valid=False,
                pending_order_active=True,
            )

    def test_addon_module_has_no_execution_provider_network_or_persistence_authority(self):
        source = Path("core/multi_symbol_follower_pending_orchestration.py").read_text(encoding="utf-8")
        for forbidden in (
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "ParentFeatureProvider",
            "broker.submit(",
            "broker.cancel(",
            "provider.build(",
            "requests.",
            "sqlite3",
        ):
            self.assertNotIn(forbidden, source)

        result = MultiSymbolFollowerPendingOrchestrator.compose(
            relation_result=relation_result(),
            policy=policy(),
            as_of="20260828112500",
            follower_symbol="B",
            local_setup_pass=True,
            hard_guard_pass=True,
            relation_still_valid=True,
        )
        for forbidden_key in (
            "broker_order",
            "entry_gate",
            "allocation",
            "allowed_symbols",
            "blocked_symbols",
        ):
            self.assertNotIn(forbidden_key, result)


if __name__ == "__main__":
    unittest.main()
