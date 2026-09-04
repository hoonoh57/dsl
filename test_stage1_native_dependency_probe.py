import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "scripts" / "start_stage1_stack.ps1"


class Stage1NativeDependencyProbeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = LAUNCHER.read_text(encoding="utf-8")

    def test_dependency_probe_captures_native_stderr_without_terminating_preflight(self):
        self.assertIn("function Invoke-NativeCaptured", self.script)
        self.assertIn("$previousErrorActionPreference = $ErrorActionPreference", self.script)
        self.assertIn("$ErrorActionPreference = 'Continue'", self.script)
        self.assertIn("$exitCode = $LASTEXITCODE", self.script)
        self.assertIn("$ErrorActionPreference = $previousErrorActionPreference", self.script)
        self.assertIn("$pythonImport = Invoke-NativeCaptured $python $importArgs", self.script)
        self.assertIn("if ($pythonImport.ExitCode -ne 0)", self.script)
        self.assertIn("Details: ", self.script)
        self.assertNotIn(
            "& $python -c 'import fastapi, uvicorn, numpy, pydantic' 2>$null",
            self.script,
        )

    def test_dependency_install_is_native_captured_and_rechecked(self):
        self.assertIn(
            "$install = Invoke-NativeCaptured $python @('-m', 'pip', 'install', '-r', (Join-Path $DslRoot 'requirements.txt'))",
            self.script,
        )
        self.assertIn("if ($install.ExitCode -ne 0)", self.script)
        first_probe = self.script.index("$pythonImport = Invoke-NativeCaptured $python $importArgs")
        install = self.script.index("$install = Invoke-NativeCaptured $python")
        second_probe = self.script.index(
            "$pythonImport = Invoke-NativeCaptured $python $importArgs",
            first_probe + 1,
        )
        self.assertLess(first_probe, install)
        self.assertLess(install, second_probe)


if __name__ == "__main__":
    unittest.main()
