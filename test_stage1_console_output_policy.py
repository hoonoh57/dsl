from __future__ import annotations

import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


def powershell_blocks(text: str) -> str:
    return "\n".join(re.findall(r"```powershell\s*\n(.*?)```", text, flags=re.S | re.I))


class ConsoleOutputPolicyTests(unittest.TestCase):
    def test_rules_and_todo_are_the_only_operating_authorities(self):
        rules = (ROOT / "rules.md").read_text(encoding="utf-8")
        todo = (ROOT / "todo.md").read_text(encoding="utf-8")

        self.assertIn("운영문서는 정확히 두 개만 사용", rules)
        self.assertIn("rules.md  = 불변 원칙", rules)
        self.assertIn("todo.md   = 현재 상태", rules)
        self.assertIn("1. rules.md", rules)
        self.assertIn("2. todo.md", rules)
        self.assertIn("새 운영원칙마다 새 Markdown authority 문서를 생성", rules)
        self.assertIn("이 문서는 현재 상태와 다음 할 일의 유일한 authority", todo)
        self.assertIn("원칙은 `rules.md`만 따른다", todo)

    def test_competing_operating_documents_do_not_exist(self):
        for name in (
            "SESSION_HANDOFF.md",
            "STRATEGY_PRODUCT_FLOW_TODO.md",
            "CONSOLE_OPERATIONS_POLICY.md",
            "CURRENT_STATE.md",
        ):
            self.assertFalse((ROOT / name).exists(), name)

    def test_rules_requires_compact_success_and_error_first_output(self):
        rules = (ROOT / "rules.md").read_text(encoding="utf-8")
        self.assertIn("기본 출력은 1줄", rules)
        self.assertIn("실패 내용만", rules)
        self.assertIn("compact output != weaker verification", rules)
        self.assertIn("python .\\scripts\\run_focused_tests.py", rules)
        self.assertIn("npm test --", rules)

    def test_operating_documents_use_only_compact_executable_commands(self):
        executable = "\n".join(
            powershell_blocks((ROOT / name).read_text(encoding="utf-8"))
            for name in ("rules.md", "todo.md")
        )
        self.assertIn("run_focused_tests.py", executable)
        self.assertIn("npm test --", executable)
        self.assertNotIn("python -m unittest -v", executable)
        self.assertNotIn("node --test", executable)

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
