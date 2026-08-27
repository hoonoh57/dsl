from copy import deepcopy
from pathlib import Path
import unittest

from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureSpec,
)
from core.tactical_context_attribution import ContextSliceRule
from core.tactical_context_deployment_evidence import (
    EXECUTION_INTEGRATION,
    PROMOTION_POLICY,
    ValidatedContextDeploymentPolicyFactory,
)
from core.tactical_context_validation import (
    ContextValidationPartition,
    RegisteredContextSlice,
    TacticalContextValidationArena,
)


CANDIDATE_HASH = "candidate-group-policy-evidence"
MANIFEST = ParentFeatureManifest(
    provider_id="fixture_group",
    provider_version="v1",
    layer="GROUP",
    context_id="SEMICONDUCTOR_GROUP",
    max_staleness_seconds=0,
    features=(
        ParentFeatureSpec(
            "group.semiconductor_favorable_breadth_rate",
            "favorable_breadth_rate",
            "NUMBER",
        ),
    ),
    metadata={"publication_state": "RESEARCH_ONLY", "operational_authority": False},
)
MANIFEST.validate()


def context(cutoff, breadth):
    result = ParentFeatureProviderResult(
        manifest=MANIFEST,
        as_of=cutoff,
        knowledge_cutoff=cutoff,
        source="fixture://ctxdep1/group",
        features={"favorable_breadth_rate": float(breadth)},
        metadata={"publication_state": "RESEARCH_ONLY", "operational_authority": False},
    )
    return ParentContextAssembler.assemble(
        as_of=cutoff,
        knowledge_cutoff=cutoff,
        results=(result,),
        mode="OBSERVED",
        metadata={"fixture": "CTXDEP1"},
    ).context


def profile(role, dates, returns):
    role = role.upper()
    prefix = {"TRAIN": "T", "VALIDATION": "V", "OOS": "O", "HARSH": "H"}[role]
    rows = []
    for index, (date, return_pct) in enumerate(zip(dates, returns)):
        good = return_pct > 0.0
        rows.append(
            {
                "case_id": f"{prefix}{index + 1}",
                "knowledge_cutoff": f"{date}093000",
                "return_pct": float(return_pct),
                "mdd_pct": -0.4 if good else -1.5,
                "closed_trade_count": 1,
                "total_cost": 8.0 if good else 16.0,
                "mfe_giveback_pct": 0.3 if good else 1.1,
            }
        )
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {"candidate_hash": CANDIDATE_HASH},
        "case_set_hash": f"{role.lower()}-set",
        "context_policy": {"require_neutral_context": True, "require_uniform_settings": True},
        "results": rows,
        "run_hash": f"{role.lower()}-run",
    }


def partition(role, dates, returns, *, adverse_reason=""):
    neutral = profile(role, dates, returns)
    breadths = (0.2, 0.8)
    contexts = {
        row["case_id"]: context(row["knowledge_cutoff"], breadth)
        for row, breadth in zip(neutral["results"], breadths)
    }
    metadata = {"adverse_reason": adverse_reason} if adverse_reason else {}
    return ContextValidationPartition(
        partition_id=f"{role.upper()}_CTXDEP1",
        role=role,
        profile=neutral,
        contexts=contexts,
        metadata=metadata,
    )


def partitions(*, bad_oos=False):
    return (
        partition("TRAIN", ("20260801", "20260802"), (-1.0, 1.0)),
        partition("VALIDATION", ("20260803", "20260804"), (-0.5, 0.7)),
        partition(
            "OOS",
            ("20260805", "20260806"),
            (0.8, -0.8) if bad_oos else (-0.8, 0.8),
        ),
        partition(
            "HARSH",
            ("20260807", "20260808"),
            (-2.0, 0.2),
            adverse_reason="weak volatile fixture",
        ),
    )


def registered_slice():
    return RegisteredContextSlice(
        feature_id="group.semiconductor_favorable_breadth_rate",
        required_manifest_hash=MANIFEST.manifest_hash,
        rule=ContextSliceRule(
            slice_id="GROUP_BREADTH_GTE_060",
            layer="GROUP",
            context_id="SEMICONDUCTOR_GROUP",
            feature_key="favorable_breadth_rate",
            operator="GTE",
            value=0.60,
            metadata={"source": "CTXVAL1"},
        ),
    )


def arena(*, bad_oos=False):
    return TacticalContextValidationArena.run(
        partitions=partitions(bad_oos=bad_oos),
        slices=(registered_slice(),),
    )


class TacticalContextDeploymentEvidenceTests(unittest.TestCase):
    def test_validated_slice_becomes_non_operational_e8_policy_evidence(self):
        validation = arena()
        evidence = ValidatedContextDeploymentPolicyFactory.create(
            validation_arena=validation,
            slice_id="GROUP_BREADTH_GTE_060",
            policy_id="SEMICONDUCTOR_BREADTH_POLICY",
            policy_version="v1",
            priority_if_allowed=1.0,
        )
        public = evidence.public_dict()

        self.assertEqual(public["promotion_policy"], PROMOTION_POLICY)
        self.assertEqual(public["execution_integration"], EXECUTION_INTEGRATION)
        self.assertFalse(public["operational_authority"])
        self.assertTrue(public["policy_evidence_validated"])
        self.assertEqual(public["policy"]["tactic_id"], CANDIDATE_HASH)
        self.assertEqual(public["policy"]["evidence_status"], "VALIDATED")
        self.assertEqual(
            public["policy"]["validation_evidence_hash"],
            validation["slices"][0]["validation_evidence_hash"],
        )
        self.assertEqual(public["validation_arena_hash"], validation["arena_hash"])
        self.assertEqual(public["required_manifest_hash"], MANIFEST.manifest_hash)
        self.assertTrue(public["evidence_hash"])
        self.assertNotIn("allowed_symbols", public)
        self.assertNotIn("blocked_symbols", public)

    def test_failed_oos_slice_cannot_be_promoted(self):
        validation = arena(bad_oos=True)
        self.assertEqual(validation["arena_status"], "FAIL")
        with self.assertRaisesRegex(ValueError, "PASS slice"):
            ValidatedContextDeploymentPolicyFactory.create(
                validation_arena=validation,
                slice_id="GROUP_BREADTH_GTE_060",
                policy_id="SHOULD_FAIL",
                policy_version="v1",
            )

    def test_tampered_validation_payload_is_rejected_by_arena_hash(self):
        validation = deepcopy(arena())
        validation["slices"][0]["validation_evidence_hash"] = "tampered"
        with self.assertRaisesRegex(ValueError, "arena_hash"):
            ValidatedContextDeploymentPolicyFactory.create(
                validation_arena=validation,
                slice_id="GROUP_BREADTH_GTE_060",
                policy_id="SHOULD_FAIL",
                policy_version="v1",
            )

    def test_unknown_slice_and_invalid_priority_fail_closed(self):
        validation = arena()
        with self.assertRaisesRegex(ValueError, "정확히 하나"):
            ValidatedContextDeploymentPolicyFactory.create(
                validation_arena=validation,
                slice_id="UNKNOWN",
                policy_id="UNKNOWN",
                policy_version="v1",
            )
        with self.assertRaisesRegex(ValueError, "유한한 숫자"):
            ValidatedContextDeploymentPolicyFactory.create(
                validation_arena=validation,
                slice_id="GROUP_BREADTH_GTE_060",
                policy_id="BAD_PRIORITY",
                policy_version="v1",
                priority_if_allowed=float("nan"),
            )

    def test_policy_identity_is_deterministic_for_same_validation_evidence(self):
        validation = arena()
        first = ValidatedContextDeploymentPolicyFactory.create(
            validation_arena=validation,
            slice_id="GROUP_BREADTH_GTE_060",
            policy_id="SEMICONDUCTOR_BREADTH_POLICY",
            policy_version="v1",
        )
        second = ValidatedContextDeploymentPolicyFactory.create(
            validation_arena=deepcopy(validation),
            slice_id="GROUP_BREADTH_GTE_060",
            policy_id="SEMICONDUCTOR_BREADTH_POLICY",
            policy_version="v1",
        )
        self.assertEqual(first.policy.policy_hash, second.policy.policy_hash)
        self.assertEqual(first.evidence_hash, second.evidence_hash)

    def test_bridge_has_no_execution_provider_or_selection_wiring(self):
        source = Path("core/tactical_context_deployment_evidence.py").read_text(encoding="utf-8")
        for forbidden in (
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "provider.build(",
            "entry_gate",
            "allowed_symbols",
            "blocked_symbols",
            "allocation",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
