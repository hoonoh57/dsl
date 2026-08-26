import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class TacticalLauncherContractTests(unittest.TestCase):
    def test_tactical_launcher_uses_tactical_app_and_shared_chart_health(self):
        text = (ROOT / "scripts" / "start_tactical_stack.ps1").read_text(encoding="utf-8")
        self.assertIn("tactical_main:app", text)
        self.assertIn("/api/stage1/tactical/health", text)
        self.assertIn('"app":"cascading-feature-solution"', text)
        self.assertIn("Node.js >= 24", text)
        self.assertIn("pymysql", text)
        self.assertIn("$tacticalPidValue = $null", text)
        self.assertIn("$chartPidValue = $null", text)
        self.assertNotIn("dummy", text.lower())

    def test_consolidated_verifier_keeps_base_full_boundary_then_adds_tactical_stress_and_smoke(self):
        text = (ROOT / "scripts" / "verify_tactical_p1.ps1").read_text(encoding="utf-8")
        self.assertIn("verify_stage1.ps1", text)
        self.assertIn("tactical_contract_stress.py", text)
        self.assertIn("start_tactical_stack.ps1", text)
        self.assertIn("Select-Object -Last 80", text)
        self.assertIn("[PASS] Tactical P1 verification completed", text)

    def test_tactical_stress_direct_script_bootstraps_repository_root_before_core_imports(self):
        text = (ROOT / "scripts" / "tactical_contract_stress.py").read_text(encoding="utf-8")
        root_index = text.index("ROOT = Path(__file__).resolve().parents[1]")
        path_index = text.index("sys.path.insert(0, str(ROOT))")
        core_index = text.index("from core.multi_symbol import")
        self.assertLess(root_index, path_index)
        self.assertLess(path_index, core_index)

    def test_tactical_app_cohort_inspection_does_not_return_outcomes(self):
        text = (ROOT / "tactical_main.py").read_text(encoding="utf-8")
        cohort_start = text.index("def tactical_1516_cohort")
        beta_start = text.index("def tactical_high_beta_cohort")
        cohort_block = text[cohort_start:beta_start]
        self.assertIn("bundle.public_snapshot()", cohort_block)
        self.assertNotIn("bundle.outcomes", cohort_block)
        self.assertNotIn("to_evaluation_payload", cohort_block)

    def test_tactical_app_exposes_high_beta_inspection_without_guessing_minute_table(self):
        text = (ROOT / "tactical_main.py").read_text(encoding="utf-8")
        self.assertIn('/api/stage1/tactical/high-beta/cohort', text)
        self.assertIn('market_database: str = ""', text)
        self.assertIn('market_table: str = ""', text)
        self.assertNotIn('market_table: str = "minute_candles_5m"', text)
        self.assertIn("database=req.market_database or None", text)
        self.assertIn("table=req.market_table or None", text)


if __name__ == "__main__":
    unittest.main()
