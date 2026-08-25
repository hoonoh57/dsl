import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "scripts" / "start_stage1_stack.ps1"
SMOKE = ROOT / "scripts" / "stage1_operational_smoke.py"
STAGE1_JS = ROOT / "core" / "static" / "stage1.js"


class Stage1StackLauncherContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = LAUNCHER.read_text(encoding="utf-8")
        cls.smoke = SMOKE.read_text(encoding="utf-8")
        cls.stage1_js = STAGE1_JS.read_text(encoding="utf-8")

    def test_launcher_owns_process_orchestration_not_chart_rendering(self):
        self.assertIn("cascading-feature-solution", self.script)
        self.assertIn("scripts\\serve.mjs", self.script)
        self.assertIn("stage1_main:app", self.script)
        self.assertIn("/__cascade_health", self.script)
        self.assertIn("/api/stage1/health", self.script)
        self.assertNotIn("Copy-Item", self.script)
        self.assertNotIn("ChartDocumentRenderer", self.script)
        self.assertNotIn("createChart", self.script)
        self.assertNotIn("setMarkers(", self.script)

    def test_launcher_and_stage1_ui_share_chart_ssot_contract(self):
        self.assertIn("[int]$ChartPort = 5174", self.script)
        self.assertIn("chartSsot=", self.script)
        self.assertIn("http://127.0.0.1:5174", self.stage1_js)
        self.assertIn("chart-document-viewer.html", self.stage1_js)

    def test_launcher_is_powershell_51_safe_and_fail_closed(self):
        self.assertIn("Set-StrictMode -Version 2.0", self.script)
        self.assertIn("Invoke-WebRequest -UseBasicParsing", self.script)
        self.assertIn("Node.js >= 24", self.script)
        self.assertIn("-InstallDependencies", self.script)
        self.assertNotIn("ForEach-Object -Parallel", self.script)
        self.assertNotIn("??", self.script)
        self.assertNotIn("&&", self.script)
        self.assertNotIn("pwsh", self.script.lower())

    def test_launcher_tracks_only_processes_it_can_stop_safely(self):
        self.assertIn("Get-CimInstance Win32_Process", self.script)
        self.assertIn("stage1_main:app", self.script)
        self.assertIn("serve.mjs", self.script)
        self.assertIn("Remove-PidState", self.script)
        self.assertIn("Stop-Process -Id $stage1Process.Id", self.script)
        self.assertIn("Stop-Process -Id $chartProcess.Id", self.script)

    def test_smoke_action_runs_the_live_http_workflow_without_copying_chart_code(self):
        self.assertIn("'Smoke'", self.script)
        self.assertIn("stage1_operational_smoke.py", self.script)
        self.assertIn("--stage1-base", self.script)
        self.assertIn("--chart-base", self.script)
        self.assertIn("/api/stage1/baseline", self.smoke)
        self.assertIn("/api/stage1/seeker-sessions", self.smoke)
        self.assertIn("/api/stage1/feedback", self.smoke)
        self.assertIn("/api/stage1/apply-llm", self.smoke)
        self.assertIn("/api/stage1/oos/", self.smoke)
        self.assertIn("/api/stage1/target-loops", self.smoke)
        self.assertIn("/api/stage1/methodology/", self.smoke)
        self.assertIn("/__cascade_health", self.smoke)
        self.assertNotIn("lightweight-charts", self.smoke)
        self.assertNotIn("ChartDocumentRenderer", self.smoke)

    def test_smoke_success_prefix_is_literal_not_wildcard(self):
        self.assertIn("$passLine.StartsWith('[PASS]')", self.script)
        self.assertNotIn("$passLine -notlike '[PASS]*'", self.script)


if __name__ == "__main__":
    unittest.main()
