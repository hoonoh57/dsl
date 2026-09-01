from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConsoleOutputPolicyTest(unittest.TestCase):
    def test_stack_launcher_is_quiet_on_success(self):
        source = (ROOT / "scripts" / "dsl_stack.ps1").read_text(encoding="utf-8")
        self.assertNotIn("[INFO]", source)
        self.assertNotIn("function Write-Info", source)
        self.assertIn("RedirectStandardOutput $LiveOutLog", source)
        self.assertIn("RedirectStandardError $LiveErrLog", source)
        self.assertIn("RedirectStandardOutput $ChartOutLog", source)
        self.assertIn("RedirectStandardError $ChartErrLog", source)
        self.assertIn("Show-FailureEvidence", source)
        self.assertEqual(source.count("Write-Pass 'DSL chart stack started'"), 1)
        self.assertEqual(source.count("Write-Pass 'Chart restarted'"), 1)
        self.assertEqual(source.count("Write-Pass 'DSL chart stack stopped'"), 1)

    def test_verification_uses_exit_code_not_stderr_as_failure_authority(self):
        source = (ROOT / "scripts" / "verify_current.ps1").read_text(encoding="utf-8")
        self.assertIn("Start-Process -FilePath $Executable", source)
        self.assertIn("RedirectStandardOutput $outLog", source)
        self.assertIn("RedirectStandardError $errLog", source)
        self.assertIn("-Wait -PassThru", source)
        self.assertIn("$process.ExitCode -ne 0", source)
        self.assertNotIn("& $Executable @Arguments > $log 2>&1", source)

    def test_verification_hides_success_detail_and_preserves_failure_source_context(self):
        source = (ROOT / "scripts" / "verify_current.ps1").read_text(encoding="utf-8")
        self.assertIn("Show-FailedCommandOutput", source)
        self.assertIn("Get-Content -Path $path -Tail 120", source)
        self.assertIn("$matchIndex - 3", source)
        self.assertIn("SyntaxError", source)
        self.assertIn("'syntax-product-state-test'", source)
        self.assertIn("'syntax-chart-server'", source)
        self.assertIn("@('--check'", source)
        self.assertIn("[PASS] current verification passed", source)
        self.assertNotIn("Write-Host \"[PASS] $Label", source)


if __name__ == "__main__":
    unittest.main()
