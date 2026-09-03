import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "scripts" / "start_stage1_stack.ps1"


class Stage1NativeVersionProbeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = LAUNCHER.read_text(encoding="utf-8")

    def test_native_version_exit_code_is_captured_before_output_selection(self):
        contracts = (
            (
                "$nodeVersionOutput = & $node --version 2>&1",
                "$nodeVersionExitCode = $LASTEXITCODE",
                "if ($nodeVersionExitCode -ne 0)",
                "$nodeText = [string]($nodeVersionOutput | Select-Object -First 1)",
                "$nodeText = (& $node --version 2>&1 | Select-Object -First 1)",
            ),
            (
                "$pythonVersionOutput = & $python --version 2>&1",
                "$pythonVersionExitCode = $LASTEXITCODE",
                "if ($pythonVersionExitCode -ne 0)",
                "$pythonVersionText = [string]($pythonVersionOutput | Select-Object -First 1)",
                "$pythonVersionText = (& $python --version 2>&1 | Select-Object -First 1)",
            ),
        )

        for invoke, capture, fail_closed, select_text, unsafe_pipeline in contracts:
            with self.subTest(invoke=invoke):
                self.assertIn(invoke, self.script)
                self.assertIn(capture, self.script)
                self.assertIn(fail_closed, self.script)
                self.assertIn(select_text, self.script)
                self.assertNotIn(unsafe_pipeline, self.script)
                self.assertLess(self.script.index(invoke), self.script.index(capture))
                self.assertLess(self.script.index(capture), self.script.index(fail_closed))
                self.assertLess(self.script.index(fail_closed), self.script.index(select_text))


if __name__ == "__main__":
    unittest.main()
