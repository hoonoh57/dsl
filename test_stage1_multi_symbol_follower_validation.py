import unittest

from core.multi_symbol_follower_validation import (
    FollowerValidationContract,
    FollowerValidationPartition,
    MultiSymbolFollowerValidationArena,
    SCHEMA_VERSION,
)


def row(tag, *, qualified=True, setup=True, guard=True, relation=True, active=False, intent=None):
    if intent is None:
        if active:
            invalid = not (qualified and setup and guard and relation)
            intent = "CANCEL_PENDING" if invalid else "HOLD_PENDING"
        else:
            intent = "ARM_PENDING" if (qualified and setup and guard and relation) else "HOLD"
    return {
        "schema": "multi_symbol_follower_pending_orchestration/v1",
        "mode": "OBSERVATION_ONLY",
        "operational_authority": False,
        "execution_authority": False,
        "as_of": f"20260828{tag:06d}",
        "relation_result_hash": f"relation-{tag}",
        "policy_hash": "lf2-policy-stable",
        "leader_symbol": "A",
        "selected_follower_symbol": "B",
        "follower_symbol": "B",
        "selection_qualified": qualified,
        "local_setup_pass": setup,
        "hard_guard_pass": guard,
        "relation_still_valid": relation,
        "pending_order_active": active,
        "intent": intent,
        "client_order_id": f"lf2:B:{tag}" if (active or intent == "ARM_PENDING") else None,
        "reasons": ("fixture",),
        "evidence_hash": f"evidence-{tag}",
    }


def partition(pid, role, rows, **metadata):
    return FollowerValidationPartition(pid, role, tuple(rows), metadata=metadata)


def passing_partitions():
    return (
        partition("train", "TRAIN", (row(90000), row(90500), row(91000, relation=False, active=True))),
        partition("validation", "VALIDATION", (row(91500), row(92000), row(92500, guard=False, active=True))),
        partition("oos", "OOS", (row(93000), row(93500), row(94000, setup=False, active=True))),
        partition(
            "harsh-relation-loss",
            "HARSH",
            (row(94500), row(95000, relation=False), row(95500, relation=False, active=True)),
            adverse_reason="relation weakens under adverse fixture",
        ),
    )


class MultiSymbolFollowerValidationTests(unittest.TestCase):
    def test_partitioned_evidence_passes_without_operational_authority(self):
        result = MultiSymbolFollowerValidationArena.run(partitions=passing_partitions())
        self.assertEqual(result["schema"], SCHEMA_VERSION)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_status"], "VALIDATED")
        self.assertFalse(result["operational_authority"])
        self.assertFalse(result["execution_authority"])
        self.assertFalse(result["deployment_authority"])
        self.assertEqual(result["selection_policy"], "ALL_DECLARED_PARTITIONS_PASS_NO_HIDDEN_SCORE")
        self.assertNotIn("score", result)
        self.assertNotIn("broker_order", result)
        self.assertEqual([p["role"] for p in result["partitions"]], ["TRAIN", "VALIDATION", "OOS", "HARSH"])

    def test_holdout_regression_is_rejected_by_declared_axis(self):
        parts = list(passing_partitions())
        parts[2] = partition(
            "oos",
            "OOS",
            (
                row(93000, qualified=False, setup=False, guard=False, relation=False),
                row(93500, qualified=False, setup=False, guard=False, relation=False),
                row(94000, qualified=False, setup=False, guard=False, relation=False),
            ),
        )
        result = MultiSymbolFollowerValidationArena.run(
            partitions=parts,
            contract=FollowerValidationContract(
                max_selection_qualified_rate_regression=0.20,
                max_arm_rate_regression=0.20,
                max_hard_guard_pass_rate_regression=0.20,
                max_relation_valid_rate_regression=0.20,
            ),
        )
        self.assertEqual(result["status"], "FAIL")
        oos = next(p for p in result["partitions"] if p["role"] == "OOS")
        self.assertIn("selection_qualified_rate_regression", oos["violations"])
        self.assertIn("arm_rate_regression", oos["violations"])

    def test_active_invalid_pending_must_cancel_fail_closed(self):
        broken = row(90000, relation=False, active=True, intent="HOLD_PENDING")
        with self.assertRaisesRegex(ValueError, "CANCEL_PENDING"):
            MultiSymbolFollowerValidationArena.run(
                partitions=(
                    partition("train", "TRAIN", (broken, row(90500))),
                    partition("validation", "VALIDATION", (row(91000), row(91500))),
                    partition("oos", "OOS", (row(92000), row(92500))),
                    partition("harsh", "HARSH", (row(93000), row(93500)), adverse_reason="fixture"),
                )
            )

    def test_unsafe_arm_is_rejected_fail_closed(self):
        broken = row(90000, guard=False, intent="ARM_PENDING")
        with self.assertRaisesRegex(ValueError, "unsafe ARM"):
            MultiSymbolFollowerValidationArena.run(
                partitions=(
                    partition("train", "TRAIN", (broken, row(90500))),
                    partition("validation", "VALIDATION", (row(91000), row(91500))),
                    partition("oos", "OOS", (row(92000), row(92500))),
                    partition("harsh", "HARSH", (row(93000), row(93500)), adverse_reason="fixture"),
                )
            )

    def test_partition_contract_requires_train_validation_oos_and_harsh_reason(self):
        with self.assertRaisesRegex(ValueError, "OOS"):
            MultiSymbolFollowerValidationArena.run(partitions=passing_partitions()[:2] + passing_partitions()[3:])
        no_reason = partition("harsh", "HARSH", (row(96000), row(96500)))
        with self.assertRaisesRegex(ValueError, "adverse_reason"):
            MultiSymbolFollowerValidationArena.run(partitions=passing_partitions()[:3] + (no_reason,))

    def test_partition_order_does_not_change_validation_identity(self):
        one = MultiSymbolFollowerValidationArena.run(partitions=passing_partitions())
        two = MultiSymbolFollowerValidationArena.run(partitions=tuple(reversed(passing_partitions())))
        self.assertEqual(one["validation_evidence_hash"], two["validation_evidence_hash"])
        self.assertEqual(one["partitions"], two["partitions"])

    def test_policy_mismatch_across_partitions_fails_closed(self):
        parts = list(passing_partitions())
        mutated = dict(parts[1].rows[0])
        mutated["policy_hash"] = "different-policy"
        mutated["evidence_hash"] = "evidence-mutated"
        parts[1] = partition("validation", "VALIDATION", (mutated, *parts[1].rows[1:]))
        with self.assertRaisesRegex(ValueError, "동일 LF2 policy_hash"):
            MultiSymbolFollowerValidationArena.run(partitions=parts)


if __name__ == "__main__":
    unittest.main()
