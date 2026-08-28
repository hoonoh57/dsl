import unittest

from core.multi_symbol_follower_outcome_validation import (
    FollowerOutcomeContract,
    FollowerOutcomePartition,
    FrozenFollowerOutcome,
    MultiSymbolFollowerOutcomeValidationArena,
)


def evidence(tag, intent, *, policy_hash="p1"):
    return {
        "schema": "multi_symbol_follower_pending_orchestration/v1",
        "mode": "OBSERVATION_ONLY",
        "operational_authority": False,
        "execution_authority": False,
        "evidence_hash": f"e-{tag}",
        "relation_result_hash": f"r-{tag}",
        "policy_hash": policy_hash,
        "as_of": f"20260828{tag:0>6}",
        "follower_symbol": "005930",
        "intent": intent,
    }


def outcome(row, ret, mfe, mae):
    return FrozenFollowerOutcome(
        evidence_hash=row["evidence_hash"],
        forward_return_pct=ret,
        mfe_pct=mfe,
        mae_pct=mae,
    )


def partition(pid, role, base, *, degrade=0.0, policy_hash="p1"):
    rows = (
        evidence(base + 1, "ARM_PENDING", policy_hash=policy_hash),
        evidence(base + 2, "ARM_PENDING", policy_hash=policy_hash),
        evidence(base + 3, "HOLD", policy_hash=policy_hash),
        evidence(base + 4, "CANCEL_PENDING", policy_hash=policy_hash),
    )
    outcomes = (
        outcome(rows[0], 2.0 - degrade, 3.0 - degrade, -0.4),
        outcome(rows[1], 1.5 - degrade, 2.5 - degrade, -0.5),
        outcome(rows[2], 0.0, 0.8, -0.6),
        outcome(rows[3], -1.2, 0.2, -1.4),
    )
    metadata = {"fixture_only": True}
    if role == "HARSH":
        metadata["adverse_reason"] = "synthetic adverse partition"
    return FollowerOutcomePartition(pid, role, rows, outcomes, metadata)


class FollowerOutcomeValidationTests(unittest.TestCase):
    def parts(self, *, validation_degrade=0.0):
        return (
            partition("train", "TRAIN", 100),
            partition("validation", "VALIDATION", 200, degrade=validation_degrade),
            partition("oos", "OOS", 300, degrade=0.2),
            partition("harsh", "HARSH", 400, degrade=0.4),
        )

    def test_partitioned_pass_is_evidence_only(self):
        result = MultiSymbolFollowerOutcomeValidationArena.run(partitions=self.parts())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_status"], "VALIDATED")
        self.assertFalse(result["operational_authority"])
        self.assertFalse(result["execution_authority"])
        self.assertFalse(result["deployment_authority"])
        self.assertNotIn("score", result)

    def test_exact_outcome_coverage_required(self):
        p = partition("train", "TRAIN", 100)
        broken = FollowerOutcomePartition(p.partition_id, p.role, p.evidence_rows, p.outcomes[:-1], p.metadata)
        with self.assertRaisesRegex(ValueError, "exact outcome coverage"):
            broken.validate()

    def test_holdout_return_edge_regression_rejects(self):
        contract = FollowerOutcomeContract(max_holdout_edge_regression_pct=0.25)
        result = MultiSymbolFollowerOutcomeValidationArena.run(
            partitions=self.parts(validation_degrade=1.0),
            contract=contract,
        )
        val = next(row for row in result["partitions"] if row["role"] == "VALIDATION")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("holdout_return_edge_regression", val["violations"])

    def test_cancel_avoided_loss_axis_is_explicit(self):
        contract = FollowerOutcomeContract(min_cancel_avoided_loss_pct=1.0)
        result = MultiSymbolFollowerOutcomeValidationArena.run(partitions=self.parts(), contract=contract)
        self.assertEqual(result["status"], "PASS")
        for row in result["partitions"]:
            self.assertGreaterEqual(row["metrics"]["cancel_avoided_loss_pct"], 1.0)

    def test_partition_contract_requires_train_validation_oos_harsh(self):
        with self.assertRaisesRegex(ValueError, "HARSH"):
            MultiSymbolFollowerOutcomeValidationArena.run(partitions=self.parts()[:-1])
        harsh = partition("harsh", "HARSH", 500)
        broken_harsh = FollowerOutcomePartition(harsh.partition_id, harsh.role, harsh.evidence_rows, harsh.outcomes, {})
        with self.assertRaisesRegex(ValueError, "adverse_reason"):
            MultiSymbolFollowerOutcomeValidationArena.run(partitions=(*self.parts()[:-1], broken_harsh))

    def test_partition_order_does_not_change_identity(self):
        one = MultiSymbolFollowerOutcomeValidationArena.run(partitions=self.parts())
        two = MultiSymbolFollowerOutcomeValidationArena.run(partitions=tuple(reversed(self.parts())))
        self.assertEqual(one["outcome_evidence_hash"], two["outcome_evidence_hash"])
        self.assertEqual(
            [row["partition_id"] for row in one["partitions"]],
            ["train", "validation", "oos", "harsh"],
        )

    def test_lf2_policy_mismatch_fails_closed(self):
        parts = list(self.parts())
        parts[2] = partition("oos", "OOS", 700, policy_hash="other")
        with self.assertRaisesRegex(ValueError, "policy_hash"):
            MultiSymbolFollowerOutcomeValidationArena.run(partitions=tuple(parts))


if __name__ == "__main__":
    unittest.main()
