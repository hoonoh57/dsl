import ast
from dataclasses import replace
from pathlib import Path
import unittest

from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)
from core.tactical_context_attribution import ContextDeploymentPolicy, ContextSliceRule
from core.tactical_context_deployment_evidence import ValidatedContextDeploymentPolicyEvidence
from core.tactical_context_gate_preview import (
    COMPOSITION_POLICY,
    EXECUTION_INTEGRATION,
    ValidatedContextGatePreviewBuilder,
)


TACTIC_ID = "candidate-context-gate-preview"
FEATURE_ID = "group.semiconductor_favorable_breadth_rate"
MANIFEST = ParentFeatureManifest(
    provider_id="fixture_group_gate_preview",
    provider_version="v1",
    layer="GROUP",
    context_id="SEMICONDUCTOR_GROUP",
    max_staleness_seconds=0,
    features=(
        ParentFeatureSpec(
            FEATURE_ID,
            "favorable_breadth_rate",
            "NUMBER",
        ),
    ),
    metadata={"publication_state": "VALIDATED_INPUT_FIXTURE", "operational_authority": False},
)
MANIFEST.validate()
REGISTRY = ParentFeatureRegistry(manifests=(MANIFEST,))
REGISTRY.validate()
TIMES = (
    "20260828090000",
    "20260828090500",
    "20260828091000",
    "20260828091500",
)


def policy_evidence(*, required_manifest_hash=None, tactic_id=TACTIC_ID):
    rule = ContextSliceRule(
        slice_id="GROUP_BREADTH_GTE_060",
        layer="GROUP",
        context_id="SEMICONDUCTOR_GROUP",
        feature_key="favorable_breadth_rate",
        operator="GTE",
        value=0.60,
        metadata={"source": "CTXVAL1_VALIDATED_FIXTURE"},
    )
    policy = ContextDeploymentPolicy(
        policy_id="SEMICONDUCTOR_BREADTH_POLICY",
        policy_version="v1",
        tactic_id=tactic_id,
        rule=rule,
        attribution_hash="train-attribution-hash",
        evidence_status="VALIDATED",
        validation_evidence_hash="ctxval1-validation-evidence-hash",
        priority_if_allowed=1.0,
    )
    evidence = ValidatedContextDeploymentPolicyEvidence(
        policy=policy,
        feature_id=FEATURE_ID,
        required_manifest_hash=required_manifest_hash or MANIFEST.manifest_hash,
        validation_arena_hash="ctxval1-arena-hash",
        validation_evidence_hash="ctxval1-validation-evidence-hash",
        validation_contract_hash="ctxval1-contract-hash",
        partition_attribution_hashes=(
            ("TRAIN_GROUP", "train-attribution-hash"),
            ("VALIDATION_GROUP", "validation-attribution-hash"),
            ("OOS_GROUP", "oos-attribution-hash"),
            ("HARSH_GROUP", "harsh-attribution-hash"),
        ),
    )
    evidence.validate()
    return evidence


def frame(*, mode="DEPLOYMENT", breadths=(0.8, 0.8, 0.2, 0.9)):
    assemblies = []
    for target_time, breadth in zip(TIMES, breadths):
        result = ParentFeatureProviderResult(
            manifest=MANIFEST,
            as_of=target_time,
            knowledge_cutoff=target_time,
            source="fixture://ctxint1/group",
            features={"favorable_breadth_rate": float(breadth)},
            metadata={"fixture": "CTXINT1"},
        )
        assemblies.append(
            ParentContextAssembler.assemble(
                as_of=target_time,
                knowledge_cutoff=target_time,
                results=(result,),
                mode=mode,
                metadata={"fixture": "CTXINT1"},
            )
        )
    return ParentContextFrame.create(
        frame_id=f"CTXINT1_{mode}",
        target_symbol="005930",
        registry=REGISTRY,
        assemblies=tuple(assemblies),
        mode=mode,
        metadata={"fixture": "CTXINT1"},
    )


def build_preview(**overrides):
    arguments = {
        "policy_evidence": policy_evidence(),
        "frame": frame(),
        "registry": REGISTRY,
        "tactic_id": TACTIC_ID,
        "target_times": TIMES,
        "tactic_trigger": (False, True, True, True),
        "local_hard_guard_pass": (True, False, True, True),
    }
    arguments.update(overrides)
    return ValidatedContextGatePreviewBuilder.build(**arguments)


class TacticalContextGatePreviewTests(unittest.TestCase):
    def test_preview_composes_local_trigger_guard_and_validated_context_permission(self):
        preview = build_preview()
        public = preview.public_dict()
        self.assertEqual(public["schema"], "validated_context_entry_gate_preview/v1")
        self.assertEqual(public["composition_policy"], COMPOSITION_POLICY)
        self.assertEqual(public["execution_integration"], EXECUTION_INTEGRATION)
        self.assertFalse(public["operational_authority"])
        self.assertFalse(public["can_create_entry_without_local_opportunity"])
        self.assertEqual(public["local_entry_opportunity_count"], 2)
        self.assertEqual(public["context_blocked_local_count"], 1)
        self.assertEqual(public["effective_entry_eligible_count"], 1)
        rows = public["points"]
        self.assertEqual(
            tuple(row["effective_entry_eligible"] for row in rows),
            (False, False, False, True),
        )

    def test_context_permission_cannot_create_entry_or_bypass_local_hard_guard(self):
        preview = build_preview()
        rows = preview.public_dict()["points"]
        self.assertTrue(rows[0]["context_allowed"])
        self.assertFalse(rows[0]["tactic_trigger"])
        self.assertFalse(rows[0]["effective_entry_eligible"])
        self.assertTrue(rows[1]["context_allowed"])
        self.assertTrue(rows[1]["tactic_trigger"])
        self.assertFalse(rows[1]["local_hard_guard_pass"])
        self.assertFalse(rows[1]["effective_entry_eligible"])

    def test_context_miss_only_removes_existing_local_opportunity(self):
        preview = build_preview()
        row = preview.public_dict()["points"][2]
        self.assertTrue(row["tactic_trigger"])
        self.assertTrue(row["local_hard_guard_pass"])
        self.assertFalse(row["context_allowed"])
        self.assertFalse(row["effective_entry_eligible"])

    def test_observed_frame_and_identity_mismatches_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "DEPLOYMENT"):
            build_preview(frame=frame(mode="OBSERVED"))
        with self.assertRaisesRegex(ValueError, "tactic_id"):
            build_preview(tactic_id="other-tactic")
        with self.assertRaisesRegex(ValueError, "required manifest"):
            build_preview(policy_evidence=policy_evidence(required_manifest_hash="wrong-manifest"))

    def test_timeline_and_bool_inputs_must_match_exact_frame(self):
        with self.assertRaisesRegex(ValueError, "timeline"):
            build_preview(target_times=TIMES[:-1])
        with self.assertRaisesRegex(ValueError, "길이"):
            build_preview(tactic_trigger=(True,))
        with self.assertRaisesRegex(ValueError, "bool"):
            build_preview(local_hard_guard_pass=(True, True, 1, True))

    def test_preview_identity_is_deterministic_and_changes_with_local_evidence(self):
        first = build_preview()
        second = build_preview()
        changed = build_preview(tactic_trigger=(True, True, True, True))
        self.assertEqual(first.preview_hash, second.preview_hash)
        self.assertNotEqual(first.preview_hash, changed.preview_hash)
        self.assertEqual(first.policy_evidence_hash, policy_evidence().evidence_hash)

    def test_preview_module_has_no_backtest_runtime_broker_or_provider_calculation_imports(self):
        source = Path("core/tactical_context_gate_preview.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add(node.module or "")
        forbidden_modules = {
            "core.backtest",
            "core.broker",
            "core.dsl_runtime",
            "core.market_parent_feature_provider",
            "core.sector_parent_feature_provider",
            "core.group_evidence_parent_feature_provider",
        }
        self.assertTrue(forbidden_modules.isdisjoint(imported_modules))
        self.assertNotIn("provider.build(", source)


if __name__ == "__main__":
    unittest.main()
