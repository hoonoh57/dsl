from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHART_ROOT = ROOT / "vendor" / "kiwoom-condition" / "condition1516" / "chart-platform"


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return modules


def python_files(root: Path):
    if not root.exists():
        return []
    return [path for path in root.rglob("*.py") if "__pycache__" not in path.parts]


class ImplementationComplianceGateTest(unittest.TestCase):
    def test_active_policy_exists_and_is_authoritative(self):
        policy = (ROOT / "DSL_IMPLEMENTATION_COMPLIANCE_GATE.md").read_text(encoding="utf-8")
        authority = (ROOT / "DSL_DOCUMENT_AUTHORITY_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("ACTIVE PRE-IMPLEMENTATION AUTHORITY", policy)
        self.assertIn("architecture invariant test", policy)
        self.assertIn("JSON compare node", policy)
        self.assertIn("DSL_IMPLEMENTATION_COMPLIANCE_GATE.md", authority)

    def test_current_work_declares_ownership_before_implementation(self):
        work_order = (ROOT / "DSL_NEXT_WORK_ORDER.md").read_text(encoding="utf-8")
        required = [
            "CURRENT_IMPLEMENTATION_CONTRACT",
            "OWNER_BOUNDARY =",
            "STATE_SSOT =",
            "LIFECYCLE_AUTHORITY =",
            "FORBIDDEN_NEIGHBORS =",
            "ALTERNATE_PATHS = NONE",
            "FAILURE_MODE =",
            "ARCH_INVARIANT =",
        ]
        missing = [item for item in required if item not in work_order]
        self.assertEqual(missing, [], f"implementation contract is incomplete: {missing}")

    def test_axis_packages_do_not_import_sibling_axes_or_legacy_core(self):
        roots = {
            "axis1_dsl": {"axes.axis2_selection", "axes.axis3_monetization"},
            "axis2_selection": {"axes.axis1_dsl", "axes.axis3_monetization"},
            "axis3_monetization": {"axes.axis1_dsl", "axes.axis2_selection"},
        }
        violations: list[str] = []
        for axis_name, forbidden in roots.items():
            for path in python_files(ROOT / "axes" / axis_name):
                for module in imported_modules(path):
                    if module == "core" or module.startswith("core."):
                        violations.append(f"{path.relative_to(ROOT)} imports frozen legacy {module}")
                    if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden):
                        violations.append(f"{path.relative_to(ROOT)} imports sibling axis {module}")
        self.assertEqual(violations, [], "\n".join(violations))

    def test_bridge_contracts_are_data_only(self):
        violations: list[str] = []
        forbidden = ("axes", "authoring", "acceptance", "core")
        for path in python_files(ROOT / "bridges" / "contracts"):
            for module in imported_modules(path):
                if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden):
                    violations.append(f"{path.relative_to(ROOT)} imports forbidden implementation {module}")
        self.assertEqual(violations, [], "\n".join(violations))

    def test_compare_subject_objects_are_runtime_owned_not_ui_owned(self):
        workspace = (CHART_ROOT / "src" / "shell" / "index-wysiwyg" / "MarketChartWorkspace.mjs").read_text(encoding="utf-8")
        shell = (CHART_ROOT / "src" / "addons" / "research" / "CompareSubjectsShellController.mjs").read_text(encoding="utf-8")
        runtime_addon = (CHART_ROOT / "src" / "addons" / "research" / "CompareSubjectsRuntimeAddon.mjs").read_text(encoding="utf-8")

        self.assertNotIn(
            "createPersistentAddonPane(COMPARE_SUBJECTS_ADDON_ID",
            workspace,
            "UI workspace must not create persistent compare panes; JSON -> Runtime Add-on must own lifecycle.",
        )
        self.assertNotIn(
            "#createView",
            shell,
            "Compare shell may edit state/selection but must not own persistent view creation.",
        )
        self.assertNotIn(
            "options.createView",
            shell,
            "Compare shell may not receive a persistent view factory from UI composition.",
        )
        self.assertIn(
            "capabilities.subjectViews",
            runtime_addon,
            "Compare Runtime Add-on must project JSON subjects through the generic subject-view runtime capability.",
        )

    def test_persistence_layer_has_no_feature_specific_authority(self):
        paths = [
            CHART_ROOT / "src" / "runtime" / "chart" / "ChartAddonJsonPersistenceClient.mjs",
            CHART_ROOT / "src" / "server" / "chart" / "ChartAddonJsonStore.mjs",
            CHART_ROOT / "src" / "shell" / "index-wysiwyg" / "ChartAddonPersistenceHttpHost.mjs",
        ]
        violations: list[str] = []
        forbidden_tokens = ["research.compare-subjects", "indicator.supertrend", "localStorage"]
        for path in paths:
            source = path.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                if token in source:
                    violations.append(f"{path.relative_to(ROOT)} contains feature-specific persistence token {token}")
        self.assertEqual(violations, [], "\n".join(violations))

    def test_verifier_runs_architecture_gate_before_behavior_regressions(self):
        source = (ROOT / "scripts" / "verify_current.ps1").read_text(encoding="utf-8")
        architecture = source.index("'architecture-compliance'")
        first_behavior = source.index("'chart-state'")
        self.assertLess(architecture, first_behavior)


if __name__ == "__main__":
    unittest.main()
