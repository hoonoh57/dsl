from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


class ConsoleOutputPolicyTests(unittest.TestCase):
    def test_governing_policy_requires_compact_success_and_error_first_output(self):
        text = (ROOT / "CONSOLE_OPERATIONS_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("성공 출력은 원칙적으로 **1줄**", text)
        self.assertIn("실패한 내용만", text)
        self.assertIn("compact output != weaker verification", text)
        self.assertIn("python scripts/run_focused_tests.py", text)
        self.assertIn("npm test --", text)

    def test_session_handoff_reads_console_policy_and_uses_only_compact_focused_commands(self):
        text = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("CONSOLE_OPERATIONS_POLICY.md", text)
        self.assertIn("python .\\scripts\\run_focused_tests.py", text)
        self.assertIn("npm test --", text)
        self.assertNotIn("python -m unittest -v", text)
        self.assertNotIn("node --test tests/", text)

    def test_python_focused_runner_suppresses_success_detail_caps_failure_trace_and_imports_repo_root(self):
        text = (ROOT / "scripts" / "run_focused_tests.py").read_text(encoding="utf-8")
        self.assertIn("verbosity=0", text)
        self.assertIn("buffer=True", text)
        self.assertIn("[PASS] Focused tests passed", text)
        self.assertIn("[ERROR] Focused tests failed", text)
        self.assertIn("MAX_TRACE_LINES = 18", text)
        self.assertIn("REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]", text)
        self.assertIn("sys.path.insert(0, str(REPO_ROOT))", text)

    def test_full_verifier_filters_success_noise_before_showing_failure(self):
        text = (ROOT / "scripts" / "verify_tactical_p1.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-CompactFailureOutput", text)
        self.assertIn("if ($trimmed -match '^\\[PASS\\]')", text)
        self.assertIn("Select-Object -Last 40", text)
        self.assertNotIn("Select-Object -Last 80", text)


if __name__ == "__main__":
    unittest.main()
