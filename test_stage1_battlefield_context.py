import unittest

from core.battlefield_context import (
    BattlefieldContext,
    ContextLayerSnapshot,
    DeploymentDecision,
)


class BattlefieldContextTests(unittest.TestCase):
    def test_neutral_context_is_stable_and_contains_no_macro_layer(self):
        context = BattlefieldContext.neutral("20260825090500")
        context.validate_for("20260825090500")
        self.assertEqual(context.mode, "NEUTRAL")
        self.assertEqual(context.layers, ())
        self.assertEqual(context.context_hash, context.context_hash)

    def test_observed_context_allows_point_in_time_layers(self):
        market = ContextLayerSnapshot(
            layer="MARKET",
            context_id="KOSDAQ_REGIME",
            as_of="20260825090459",
            source="fixture://market",
            features={"state": "RISK_ON", "breadth": 0.61},
        )
        sector = ContextLayerSnapshot(
            layer="SECTOR",
            context_id="ROBOTICS",
            as_of="20260825090500",
            source="fixture://sector",
            features={"rank": 1, "relative_strength": 3.2},
        )
        context = BattlefieldContext(
            as_of="20260825090500",
            mode="OBSERVED",
            layers=(market, sector),
        )
        context.validate_for("20260825090500")
        public = context.public_dict()
        self.assertEqual(len(public["layers"]), 2)
        self.assertEqual(public["mode"], "OBSERVED")

    def test_future_context_fails_closed(self):
        layer = ContextLayerSnapshot(
            layer="MARKET",
            context_id="FUTURE",
            as_of="20260825090600",
            source="fixture://future",
            features={"state": "KNOWN_LATER"},
        )
        context = BattlefieldContext(
            as_of="20260825090600",
            mode="OBSERVED",
            layers=(layer,),
        )
        with self.assertRaisesRegex(ValueError, "knowledge cutoff"):
            context.validate_for("20260825090500")

    def test_neutral_context_rejects_hidden_layers(self):
        layer = ContextLayerSnapshot(
            layer="MARKET",
            context_id="HIDDEN_FILTER",
            as_of="20260825090500",
            source="fixture://market",
            features={"allow": True},
        )
        with self.assertRaisesRegex(ValueError, "NEUTRAL"):
            BattlefieldContext(
                as_of="20260825090500",
                mode="NEUTRAL",
                layers=(layer,),
            ).validate()

    def test_deployment_decision_cannot_both_allow_and_block_same_tactic(self):
        with self.assertRaisesRegex(ValueError, "동시에"):
            DeploymentDecision(
                context_hash="abc",
                eligible_tactics=("T1",),
                blocked_tactics=("T1",),
            ).validate()


if __name__ == "__main__":
    unittest.main()
