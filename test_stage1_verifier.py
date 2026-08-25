import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VERIFIER = ROOT / "scripts" / "verify_stage1.ps1"


class Stage1VerifierContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = VERIFIER.read_text(encoding="utf-8")

    def test_full_mode_is_default_and_runs_complete_sequence(self):
        self.assertIn("[ValidateSet('Quick', 'Full')]", self.script)
        self.assertIn("[string]$Mode = 'Full'", self.script)
        self.assertIn("'-Action', 'Preflight'", self.script)
        self.assertIn("'compileall', '-q', '.'", self.script)
        self.assertIn("'test_core.py'", self.script)
        self.assertIn("'unittest', 'discover', '-v', '-p', 'test_stage1_*.py'", self.script)
        self.assertIn("'Stage 1 quick stress'", self.script)
        self.assertIn("'--full'", self.script)
        self.assertIn("'-Action', 'Smoke'", self.script)

    def test_launcher_is_invoked_in_child_powershell_so_exit_cannot_kill_parent(self):
        self.assertIn("Get-CommandPath 'powershell.exe'", self.script)
        self.assertIn("'-File', $Launcher", self.script)
        self.assertIn("Invoke-External 'preflight' $powershell", self.script)
        self.assertIn("Invoke-External 'live operational smoke' $powershell", self.script)
        self.assertNotIn("& $Launcher", self.script)

    def test_success_output_is_single_final_pass_line(self):
        self.assertEqual(self.script.count("[PASS]"), 1)
        self.assertIn("Stage 1 verification completed: mode=", self.script)
        self.assertIn("[FAIL]", self.script)
        self.assertIn("Select-Object -Last 8", self.script)

    def test_verifier_is_powershell_51_safe_and_feature_blind(self):
        self.assertIn("Set-StrictMode -Version 2.0", self.script)
        self.assertNotIn("ForEach-Object -Parallel", self.script)
        self.assertNotIn("??", self.script)
        self.assertNotIn("&&", self.script)
        self.assertNotIn("pwsh", self.script.lower())
        self.assertNotIn("Copy-Item", self.script)
        self.assertNotIn("ChartDocumentRenderer", self.script)
        self.assertNotIn("createChart", self.script)
        self.assertNotIn("setMarkers(", self.script)

    def test_dependency_install_requires_explicit_switch(self):
        self.assertIn("[switch]$InstallDependencies", self.script)
        self.assertIn("if ($InstallDependencies) { $preflightArgs += '-InstallDependencies' }", self.script)
        self.assertIn("if ($InstallDependencies) { $smokeArgs += '-InstallDependencies' }", self.script)


if __name__ == "__main__":
    unittest.main()
