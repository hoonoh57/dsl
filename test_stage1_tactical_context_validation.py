from copy import deepcopy
import unittest
from pathlib import Path

from core.battlefield_context import BattlefieldContext
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureSpec,
)
from core.tactical_context_attribution import ContextDeploymentPolicy, ContextSliceRule
from core.tactical_context_validation import (
    ContextSliceValidationContract,
    ContextValidationPartition,
    RegisteredContextSlice,
    TacticalContextValidationArena,
)


CANDIDATE_HASH = "candidate-jma-group-validation"
GROUP_MANIFEST = ParentFeatureManifest(
    provider_id="msa2_group_evidence_semiconductor",
    provider_version="v1",
    layer="GROUP",
    context_id="SEMICONDUCTOR_MSA2_GROUP_EVIDENCE",
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
GROUP_MANIFEST.validate()


def profile(role, dates, returns, *, candidate_hash=CANDIDATE_HASH, case_ids=None):
    role = role.upper()
    case_ids = tuple(case_ids or (f"{role[0]}{i + 1}" for i in range(len(dates))))
    rows = []
    for i, (case_id, date, return_pct) in enumerate(zip(case_ids, dates, returns)):
        profitable = return_pct > 0.0
        rows.append(
            {
                "case_id": case_id,
                "knowledge_cutoff": f"{date}093000",
                "return_pct": float(return_pct),
                "mdd_pct": (-0.4 - 0.1 * i) if profitable else (-1.5 - 0.2 * i),
                "closed_trade_count": 1,
                "total_cost": (8.0 + i) if profitable else (16.0 + i),
                "mfe_giveback_pct": (0.3 + 0.05 * i) if profitable else (1.1 + 0.1 * i),
            }
        )
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {"candidate_hash": candidate_hash},
        "case_set_hash": f"{role.lower()}-case-set",
        "context_policy": {"require_neutral_context": True, "require_uniform_settings": True},
        "results": rows,
        "run_hash": f"{role.lower()}-neutral-run",
    }


def group_context(cutoff, breadth):
    result = ParentFeatureProviderResult(
        manifest=GROUP_MANIFEST,
        as_of=cutoff,
        knowledge_cutoff=cutoff,
        source="fixture://msa3/group",
        features={"favorable_breadth_rate": float(breadth)},
        metadata={"publication_state": "RESEARCH_ONLY", "operational_authority": False},
    )
    return ParentContextAssembler.assemble(
        as_of=cutoff,
        knowledge_cutoff=cutoff,
        results=(result,),
        mode="OBSERVED",
        metadata={"fixture": "CTXVAL1_GROUP"},
    ).context


def partition(role, dates, returns, breadths, *, adverse_reason="", candidate_hash=CANDIDATE_HASH):
    neutral = profile(role, dates, returns, candidate_hash=candidate_hash)
    contexts = {
        row["case_id"]: group_context(row["knowledge_cutoff"], breadth)
        for row, breadth in zip(neutral["results"], breadths)
    }
    metadata = {"adverse_reason": adverse_reason} if role.upper() == "HARSH" and adverse_reason else {}
    return ContextValidationPartition(
        partition_id=f"{role.upper()}_GROUP",
        role=role,
        profile=neutral,
        contexts=contexts,
        metadata=metadata,
    )


def partitions(*, bad_oos=False):
    return (
        partition(
            "TRAIN",
            ("20260801", "20260802", "20260803", "20260804"),
            (-1.0, 2.0, -0.5, 1.5),
            (0.2, 0.8, 0.3, 0.7),
        ),
        partition(
            "VALIDATION",
            ("20260805", "20260806", "20260807", "20260808"),
            (-0.8, 1.2, -0.3, 1.0),
            (0.3, 0.75, 0.4, 0.8),
        ),
        partition(
            "OOS",
            ("20260809", "20260810", "20260811", "20260812"),
            (1.2, -1.0, 0.8, -0.9) if bad_oos else (-1.2, 0.8, -0.2, 1.3),
            (0.2, 0.65, 0.4, 0.9),
        ),
        partition(
            "HARSH",
            ("20260813", "20260814", "20260815", "20260816"),
            (-2.0, 0.2, -1.0, 0.4),
            (0.3, 0.7, 0.2, 0.8),
            adverse_reason="volatile weak-tape fixture",
        ),
    )


def registered_slice(manifest_hash=None):
    return RegisteredContextSlice(
        feature_id="group.semiconductor_favorable_breadth_rate",
        required_manifest_hash=manifest_hash or GROUP_MANIFEST.manifest_hash,
        rule=ContextSliceRule(
            slice_id="SEMICONDUCTOR_BREADTH_GTE_060",
            layer="GROUP",
            context_id="SEMICONDUCTOR_MSA2_GROUP_EVIDENCE",
            feature_key="favorable_breadth_rate",
            operator="GTE",
            value=0.60,
            metadata={"source": "MSA3_REGISTERED_GROUP_FEATURE"},
        ),
    )


class TacticalContextValidationTests(unittest.TestCase):
    def test_registered_group_slice_passes_all_partitions_without_operational_authority(self):
        result = TacticalContextValidationArena.run(partitions=partitions(), slices=(registered_slice(),))
        self.assertEqual(result["schema"], "tactical_context_validation_arena/v1")
        self.assertEqual(result["arena_status"], "PASS")
        self.assertEqual(result["validated_slice_ids"], ("SEMICONDUCTOR_BREADTH_GTE_060",))
        self.assertEqual(result["rejected_slice_ids"], ())
        self.assertFalse(result["operational_authority"])
        self.assertEqual(
            result["execution_integration"],
            "EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER",
        )
        slice_result = result["slices"][0]
        self.assertEqual(slice_result["evidence_status"], "VALIDATED")
        self.assertTrue(slice_result["deployment_policy_evidence_eligible"])
        self.assertTrue(slice_result["validation_evidence_hash"])
        self.assertEqual(
            tuple(item["role"] for item in slice_result["partition_evidence"]),
            ("TRAIN", "VALIDATION", "OOS", "HARSH"),
        )
        self.assertTrue(all(item["status"] == "PASS" for item in slice_result["partition_evidence"]))
        self.assertNotIn("allowed_symbols", result)
        self.assertNotIn("blocked_symbols", result)

        ContextDeploymentPolicy(
            policy_id="GROUP_BREADTH_EVIDENCE_ONLY",
            policy_version="v1",
            tactic_id=CANDIDATE_HASH,
            rule=registered_slice().rule,
            attribution_hash=result["partitions"][0]["attribution_hash"],
            evidence_status="VALIDATED",
            validation_evidence_hash=slice_result["validation_evidence_hash"],
        ).validate()

    def test_oos_regression_rejects_slice_even_when_train_is_good(self):
        result = TacticalContextValidationArena.run(
            partitions=partitions(bad_oos=True), slices=(registered_slice(),)
        )
        self.assertEqual(result["arena_status"], "FAIL")
        slice_result = result["slices"][0]
        self.assertEqual(slice_result["evidence_status"], "REJECTED")
        self.assertFalse(slice_result["deployment_policy_evidence_eligible"])
        oos = next(item for item in slice_result["partition_evidence"] if item["role"] == "OOS")
        self.assertEqual(oos["status"], "FAIL")
        self.assertIn("average_return_pct", oos["violations"])

    def test_harsh_reason_and_required_roles_fail_independently(self):
        normal = list(partitions())
        harsh = normal[-1]
        invalid_harsh = ContextValidationPartition(
            partition_id=harsh.partition_id,
            role="HARSH",
            profile=harsh.profile,
            contexts=harsh.contexts,
            metadata={},
        )
        with self.assertRaisesRegex(ValueError, "adverse_reason"):
            TacticalContextValidationArena.run(
                partitions=tuple(normal[:-1] + [invalid_harsh]), slices=(registered_slice(),)
            )

        complete = list(partitions())
        without_oos = (complete[0], complete[1], complete[3])
        with self.assertRaisesRegex(ValueError, "OOS"):
            TacticalContextValidationArena.run(partitions=without_oos, slices=(registered_slice(),))

    def test_context_must_be_exact_registered_pctx1_observed_evidence(self):
        with self.assertRaisesRegex(ValueError, "manifest"):
            TacticalContextValidationArena.run(
                partitions=partitions(), slices=(registered_slice("wrong-manifest-hash"),)
            )

        items = list(partitions())
        train = items[0]
        contexts = dict(train.contexts)
        case_id = train.case_ids[0]
        original = contexts[case_id]
        contexts[case_id] = BattlefieldContext(
            as_of="20260801092959",
            mode="OBSERVED",
            layers=original.layers,
            metadata=original.metadata,
        )
        items[0] = ContextValidationPartition(
            partition_id=train.partition_id,
            role=train.role,
            profile=train.profile,
            contexts=contexts,
            metadata=train.metadata,
        )
        with self.assertRaisesRegex(ValueError, "exact context.as_of"):
            TacticalContextValidationArena.run(partitions=tuple(items), slices=(registered_slice(),))

    def test_partitions_require_same_candidate_and_globally_disjoint_cases(self):
        items = list(partitions())
        validation = items[1]
        drifted = deepcopy(validation.profile)
        drifted["candidate"]["candidate_hash"] = "other-candidate"
        items[1] = ContextValidationPartition(
            partition_id=validation.partition_id,
            role=validation.role,
            profile=drifted,
            contexts=validation.contexts,
            metadata=validation.metadata,
        )
        with self.assertRaisesRegex(ValueError, "candidate_hash"):
            TacticalContextValidationArena.run(partitions=tuple(items), slices=(registered_slice(),))

        items = list(partitions())
        validation = items[1]
        duplicate_profile = deepcopy(validation.profile)
        old_id = duplicate_profile["results"][0]["case_id"]
        duplicate_profile["results"][0]["case_id"] = items[0].case_ids[0]
        duplicate_contexts = dict(validation.contexts)
        duplicate_contexts[items[0].case_ids[0]] = duplicate_contexts.pop(old_id)
        items[1] = ContextValidationPartition(
            partition_id=validation.partition_id,
            role=validation.role,
            profile=duplicate_profile,
            contexts=duplicate_contexts,
            metadata=validation.metadata,
        )
        with self.assertRaisesRegex(ValueError, "전역적으로 분리"):
            TacticalContextValidationArena.run(partitions=tuple(items), slices=(registered_slice(),))

    def test_input_order_does_not_change_validation_identity(self):
        normal = partitions()
        reordered = tuple(
            ContextValidationPartition(
                partition_id=item.partition_id,
                role=item.role,
                profile=item.profile,
                contexts=dict(reversed(list(item.contexts.items()))),
                metadata=item.metadata,
            )
            for item in normal
        )
        first = TacticalContextValidationArena.run(partitions=normal, slices=(registered_slice(),))
        second = TacticalContextValidationArena.run(
            partitions=tuple(reversed(reordered)), slices=(registered_slice(),)
        )
        self.assertEqual(first["arena_hash"], second["arena_hash"])
        self.assertEqual(first["slices"], second["slices"])

    def test_contract_is_explicit_and_module_has_no_execution_or_provider_calls(self):
        contract = ContextSliceValidationContract(
            min_retained_case_rate=0.25,
            max_average_return_regression_pct=0.10,
            require_train_material_improvement=True,
        )
        result = TacticalContextValidationArena.run(
            partitions=partitions(), slices=(registered_slice(),), contract=contract
        )
        self.assertEqual(result["contract"]["min_retained_case_rate"], 0.25)
        self.assertEqual(result["contract"]["max_average_return_regression_pct"], 0.10)
        self.assertTrue(result["contract"]["contract_hash"])

        source = Path("core/tactical_context_validation.py").read_text(encoding="utf-8")
        for forbidden in (
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "ContextDeploymentPolicy",
            "provider.build(",
            "entry_gate",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
