import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "scripts" / "start_stage1_stack.ps1"
STAGE1_JS = ROOT / "core" / "static" / "stage1.js"


class Stage1StackLauncherContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = LAUNCHER.read_text(encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
