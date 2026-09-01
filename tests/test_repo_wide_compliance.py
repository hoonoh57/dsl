from __future__ import annotations

import json
from pathlib import Path
import unittest

from compliance.repo_audit import REPORT_SCHEMA, audit_repository


ROOT = Path(__file__).resolve().parents[1]


class RepoWideComplianceTests(unittest.TestCase):
    def test_current_product_surface_passes_architecture_and_authority_audit(self):
        report = audit_repository(ROOT)
        self.assertTrue(
            report.passed,
            "\n".join(
                f"{item.check_id}: {item.path}: {item.message}"
                for item in report.findings
            ),
        )
        self.assertEqual(report.findings, ())

    def test_compliance_report_is_json_safe_deterministic_and_hash_stable(self):
        first = audit_repository(ROOT)
        second = audit_repository(ROOT)
        self.assertEqual(first.public_dict(), second.public_dict())
        self.assertEqual(first.report_hash, second.report_hash)
        self.assertEqual(first.public_dict()["schema"], REPORT_SCHEMA)
        self.assertEqual(first.public_dict()["status"], "PASS")
        encoded = json.dumps(
            first.public_dict(),
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        self.assertTrue(encoded)

    def test_document_disposition_preserves_history_without_restoring_old_authority(self):
        index = (ROOT / "DSL_DOCUMENT_AUTHORITY_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("HISTORICAL / NON-AUTHORITATIVE", index)
        self.assertIn("DSL_LIVE_STUDIO_FEATURE_CATALOG_V2.md", index)
        self.assertIn("DSL_LIVE_STUDIO_FEATURE_CATALOG_V3.md", index)
        self.assertIn("DSL_LIVE_STUDIO_FEATURE_CATALOG_V4.md", index)
        self.assertIn("CTX*.md", index)
        self.assertIn("E*.md", index)
        self.assertIn("current support SSOT", index)

        # Historical documents remain available as evidence rather than being
        # deleted or silently rewritten into current authority.
        for name in (
            "DSL_LIVE_STUDIO_FEATURE_CATALOG_V2.md",
            "DSL_LIVE_STUDIO_FEATURE_CATALOG_V3.md",
            "DSL_LIVE_STUDIO_FEATURE_CATALOG_V4.md",
            "CTXDSL1_GENERIC_PARENT_CONTEXT_REFERENCE_IMPLEMENTATION.md",
            "E3_MULTI_BATTLE_PARAMETER_SEEKER_IMPLEMENTATION.md",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_active_docs_express_final_axis_ownership_and_execution_order(self):
        target = (ROOT / "DSL_THREE_AXIS_FINAL_TARGET.md").read_text(encoding="utf-8")
        boundary = (ROOT / "DSL_THREE_AXIS_MODULE_BOUNDARY.md").read_text(encoding="utf-8")
        axis1 = (ROOT / "axes" / "axis1_dsl" / "README.md").read_text(encoding="utf-8")
        axis2 = (ROOT / "axes" / "axis2_selection" / "README.md").read_text(encoding="utf-8")
        axis3 = (ROOT / "axes" / "axis3_monetization" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Condition의 **선별 의미**는 AXIS 2", target)
        self.assertIn("Condition의 저장·버전·계보·승격 lifecycle은 AXIS 3", target)
        self.assertIn("AXIS 2 snapshot/spec", boundary)
        self.assertIn("-> AXIS 3 exact promoted Condition/Strategy + RunPlan", boundary)
        self.assertIn("-> AXIS 1 one-symbol execution requests", boundary)
        self.assertIn("MIGRATION COMPLETE", axis1)
        self.assertNotIn("MIGRATION NOT YET STARTED", axis1)
        self.assertIn("Condition **selection semantics**", axis2)
        self.assertNotIn("generic Condition CRUD", axis2)
        self.assertIn("Condition **artifact lifecycle**", axis3)

    def test_compliance_audit_is_read_only_and_has_no_axis_or_frozen_core_dependency(self):
        import compliance.repo_audit as audit_module

        source = Path(audit_module.__file__).read_text(encoding="utf-8")
        for token in (
            "from axes.",
            "import axes.",
            "from core",
            "import core",
            "update_file(",
            "delete_file(",
        ):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
