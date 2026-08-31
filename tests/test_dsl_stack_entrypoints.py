from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DslStackEntrypointTests(unittest.TestCase):
    def test_root_bat_entrypoints_delegate_to_single_launcher(self):
        expected = {
            "start.bat": "-Action start",
            "restart.bat": "-Action restart",
            "stop.bat": "-Action stop",
        }
        for filename, action in expected.items():
            text = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("scripts\\dsl_stack.ps1", text)
            self.assertIn(action, text)

    def test_start_resets_servers_then_waits_for_both_health_endpoints(self):
        text = (ROOT / "scripts" / "dsl_stack.ps1").read_text(encoding="utf-8")
        self.assertIn("Stop-All\n            Start-Servers\n            Start-ChartBrowser", text)
        self.assertIn("http://127.0.0.1:8010/api/capabilities", text)
        self.assertIn("http://127.0.0.1:3032/__chart_health", text)
        self.assertIn("Wait-Url $LiveUrl 'Live Studio'", text)
        self.assertIn("Wait-Url $ChartHealthUrl 'Chart Bridge'", text)

    def test_restart_is_chart_only_and_refuses_to_start_missing_servers(self):
        text = (ROOT / "scripts" / "dsl_stack.ps1").read_text(encoding="utf-8")
        restart_block = text.split("'restart' {", 1)[1].split("'stop' {", 1)[0]
        self.assertIn("Start-ChartBrowser", restart_block)
        self.assertNotIn("Start-Servers", restart_block)
        self.assertIn("restart.bat never restarts servers", restart_block)

    def test_stop_is_scoped_to_managed_processes(self):
        text = (ROOT / "scripts" / "dsl_stack.ps1").read_text(encoding="utf-8")
        self.assertIn("chart_platform_server.mjs", text)
        self.assertIn("live_studio_main.py", text)
        self.assertIn("Refusing to terminate it", text)
        self.assertNotIn("/IM python.exe", text)
        self.assertNotIn("/IM node.exe", text)

    def test_runtime_state_is_ignored(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/.runtime/", text)


if __name__ == "__main__":
    unittest.main()
