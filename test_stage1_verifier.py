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
        self.assertIn("'Stage 1 scoped Chart SSOT contracts'", self.script)
        self.assertIn("'Stage 1 quick stress'", self.script)
        self.assertIn("'--full'", self.script)
        self.assertIn("'-Action', 'Smoke'", self.script)

    def test_launcher_is_invoked_in_child_powershell_so_exit_cannot_kill_parent(self):
        self.assertIn("Get-CommandPath 'powershell.exe'", self.script)
        self.assertIn("'-File', $Launcher", self.script)
        self.assertIn("Invoke-External 'preflight' $powershell", self.script)
        self.assertIn("Invoke-External 'live operational smoke' $powershell", self.script)
        self.assertNotIn("& $Launcher", self.script)

    def test_chart_repo_resolution_prefers_explicit_env_sibling_then_bounded_discovery(self):
        self.assertIn("function Resolve-ChartRepo", self.script)
        self.assertIn("$env:CASCADE_CHART_REPO", self.script)
        self.assertIn("Join-Path (Split-Path -Parent $DslRoot) 'cascading-feature-solution'", self.script)
        self.assertIn("$workspaceRoot = Split-Path -Parent (Split-Path -Parent $DslRoot)", self.script)
        self.assertIn("Get-ChildItem -LiteralPath $workspaceRoot -Directory", self.script)
        self.assertIn("Get-ChildItem -LiteralPath $first.FullName -Directory", self.script)
        self.assertIn("Multiple Chart repos found. Pass -ChartRepo explicitly", self.script)
        self.assertNotIn("Get-ChildItem -Recurse", self.script)

    def test_scoped_chart_dependency_contracts_do_not_claim_full_donor_compliance(self):
        self.assertIn("Get-NodePath", self.script)
        self.assertIn("'--test', '--test-reporter=tap'", self.script)
        for name in (
            "chart_document_renderer.test.mjs",
            "chart_drawing_primitives_contract.test.mjs",
            "chart_drawing_ssot_boundary.test.mjs",
            "responsive_chart_surface.test.mjs",
            "stable_pane_identity_surface.test.mjs",
        ):
            self.assertIn(name, self.script)
        self.assertNotIn("scripts/run-tests.mjs", self.script)
        self.assertNotIn("npm test", self.script)

    def test_native_stderr_is_captured_without_becoming_powershell_failure(self):
        self.assertIn("$previousErrorActionPreference = $ErrorActionPreference", self.script)
        self.assertIn("$ErrorActionPreference = 'Continue'", self.script)
        self.assertIn("$exitCode = $LASTEXITCODE", self.script)
        self.assertIn("$ErrorActionPreference = $previousErrorActionPreference", self.script)
        self.assertIn("if ($exitCode -ne 0)", self.script)

    def test_default_live_smoke_uses_isolated_ports_but_explicit_ports_remain_authoritative(self):
        self.assertIn("function Get-FreeTcpPort", self.script)
        self.assertIn("$PSBoundParameters.ContainsKey('Stage1Port')", self.script)
        self.assertIn("$PSBoundParameters.ContainsKey('ChartPort')", self.script)
        self.assertIn("$smokeStage1Port = Get-FreeTcpPort $BindHost $python", self.script)
        self.assertIn("$smokeChartPort = Get-FreeTcpPort $BindHost $python", self.script)
        self.assertIn("while ($smokeChartPort -eq $smokeStage1Port)", self.script)
        self.assertIn("'-Stage1Port', [string]$smokeStage1Port", self.script)
        self.assertIn("'-ChartPort', [string]$smokeChartPort", self.script)
        self.assertIn("$smokeStage1Port = $Stage1Port", self.script)
        self.assertIn("$smokeChartPort = $ChartPort", self.script)
        self.assertNotIn("Stop-Process", self.script)

    def test_success_output_is_single_final_pass_line(self):
        self.assertEqual(self.script.count("[PASS]"), 1)
        self.assertIn("Stage 1 verification completed: mode=", self.script)
        self.assertIn("[FAIL]", self.script)
        self.assertIn("Select-Object -Last 60", self.script)
        self.assertIn("[Environment]::NewLine", self.script)

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
