import unittest

from core.multi_symbol_follower_outcome_validation import FollowerOutcomeContract, FrozenFollowerOutcome
from core.multi_symbol_follower_real_evidence import (
    FrozenEvidenceProvenance,
    MultiSymbolFollowerRealEvidenceStudy,
    RealEvidenceStudyPartition,
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
        "as_of": f"20260829{tag:06d}",
        "follower_symbol": "005930",
        "intent": intent,
    }


def provenance(row, *, source_kind="RECORDED_MARKET_DATA", fixture_only=False, cutoff=None):
    return FrozenEvidenceProvenance(
        evidence_hash=row["evidence_hash"],
        source_id="recorded-feed-A",
        source_hash=f"sha256:{row['evidence_hash']}",
        source_kind=source_kind,
        observation_cutoff=cutoff or row["as_of"],
        fixture_only=fixture_only,
    )


def outcome(row, ret, mfe, mae, *, source_kind="RECORDED_MARKET_DATA", fixture_only=False, start="20260829130000"):
    return FrozenFollowerOutcome(
        evidence_hash=row["evidence_hash"],
        forward_return_pct=ret,
        mfe_pct=mfe,
        mae_pct=mae,
        metadata={
            "source_id": "recorded-feed-A",
            "source_hash": f"sha256:outcome:{row['evidence_hash']}",
            "source_kind": source_kind,
            "fixture_only": fixture_only,
            "horizon_id": "NEXT_30M",
            "outcome_start": start,
            "outcome_end": "20260829133000",
        },
    )


def partition(pid, role, base, *, degrade=0.0):
    rows = (
        evidence(base + 1, "ARM_PENDING"),
        evidence(base + 2, "ARM_PENDING"),
        evidence(base + 3, "HOLD"),
        evidence(base + 4, "CANCEL_PENDING"),
    )
    provenances = tuple(provenance(row) for row in rows)
    outcomes = (
        outcome(rows[0], 2.0 - degrade, 3.0 - degrade, -0.4),
        outcome(rows[1], 1.5 - degrade, 2.5 - degrade, -0.5),
        outcome(rows[2], 0.0, 0.8, -0.6),
        outcome(rows[3], -1.2, 0.2, -1.4),
    )
    metadata = {"contract_test_only": True}
    if role == "HARSH":
        metadata["adverse_reason"] = "contract adverse partition"
    return RealEvidenceStudyPartition(pid, role, rows, provenances, outcomes, metadata)


class FollowerRealEvidenceAdmissionTests(unittest.TestCase):
    def parts(self, *, validation_degrade=0.0):
        return (
            partition("train", "TRAIN", 100),
            partition("validation", "VALIDATION", 200, degrade=validation_degrade),
            partition("oos", "OOS", 300, degrade=0.2),
            partition("harsh", "HARSH", 400, degrade=0.4),
        )

    def test_admissible_contract_stays_research_only(self):
        result = MultiSymbolFollowerRealEvidenceStudy.run(partitions=self.parts())
        self.assertEqual(result["evidence_status"], "ADMISSIBLE")
        self.assertEqual(result["provenance_contract_status"], "PASS")
        self.assertFalse(result["operational_authority"])
        self.assertFalse(result["execution_authority"])
        self.assertFalse(result["deployment_authority"])
        self.assertFalse(result["source_content_verified"])
        self.assertFalse(result["real_data_claim"])
        self.assertNotIn("score", result)

    def test_fixture_provenance_rejected(self):
        p = partition("train", "TRAIN", 500)
        prov = list(p.provenances)
        prov[0] = provenance(p.evidence_rows[0], fixture_only=True)
        broken = RealEvidenceStudyPartition(p.partition_id, p.role, p.evidence_rows, tuple(prov), p.outcomes, p.metadata)
        with self.assertRaisesRegex(ValueError, "fixture_only provenance"):
            broken.validate()

    def test_synthetic_outcome_source_rejected(self):
        p = partition("train", "TRAIN", 600)
        outs = list(p.outcomes)
        row = p.evidence_rows[0]
        outs[0] = outcome(row, 1.0, 2.0, -0.5, source_kind="SYNTHETIC")
        broken = RealEvidenceStudyPartition(p.partition_id, p.role, p.evidence_rows, p.provenances, tuple(outs), p.metadata)
        with self.assertRaisesRegex(ValueError, "synthetic/fixture outcome"):
            broken.validate()

    def test_observation_cutoff_must_equal_evidence_as_of(self):
        p = partition("train", "TRAIN", 700)
        prov = list(p.provenances)
        prov[0] = provenance(p.evidence_rows[0], cutoff="20260829000000")
        broken = RealEvidenceStudyPartition(p.partition_id, p.role, p.evidence_rows, tuple(prov), p.outcomes, p.metadata)
        with self.assertRaisesRegex(ValueError, "observation_cutoff"):
            broken.validate()

    def test_outcome_must_start_after_observation(self):
        p = partition("train", "TRAIN", 800)
        outs = list(p.outcomes)
        row = p.evidence_rows[0]
        outs[0] = outcome(row, 1.0, 2.0, -0.5, start=row["as_of"])
        broken = RealEvidenceStudyPartition(p.partition_id, p.role, p.evidence_rows, p.provenances, tuple(outs), p.metadata)
        with self.assertRaisesRegex(ValueError, "outcome_start"):
            broken.validate()

    def test_exact_provenance_coverage_required(self):
        p = partition("train", "TRAIN", 900)
        broken = RealEvidenceStudyPartition(p.partition_id, p.role, p.evidence_rows, p.provenances[:-1], p.outcomes, p.metadata)
        with self.assertRaisesRegex(ValueError, "exact provenance coverage"):
            broken.validate()

    def test_lfout1_regression_still_rejects(self):
        result = MultiSymbolFollowerRealEvidenceStudy.run(
            partitions=self.parts(validation_degrade=1.0),
            outcome_contract=FollowerOutcomeContract(max_holdout_edge_regression_pct=0.25),
        )
        self.assertEqual(result["outcome_validation_status"], "FAIL")
        self.assertEqual(result["evidence_status"], "REJECTED")
        self.assertFalse(result["deployment_authority"])


if __name__ == "__main__":
    unittest.main()
