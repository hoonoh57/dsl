import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "tools" / "acquire_realdata2_source.ps1"
DOC = ROOT / "REALDATA2_EXTERNAL_SOURCE_ACQUISITION.md"


class RealData2SourceAcquisitionContractTests(unittest.TestCase):
    def test_source_is_pinned_to_exact_commit_and_git_blob(self):
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn(
            "https://raw.githubusercontent.com/nileshiq/Samsung-Stock-Price/"
            "bcef6f27b803ce89000e2fc336201ddeef7df015/Samsung%20Dataset.csv",
            text,
        )
        self.assertIn(
            '$ExpectedGitBlobSha1 = "68e3b6d861b4bfcf39d9c09c6a073c271369d3a9"',
            text,
        )
        self.assertIn('"blob $($bytes.Length)`0"', text)
        self.assertIn("ComputeHash($gitBlobBytes)", text)

    def test_tool_reports_sha256_without_granting_core_or_provider_authority(self):
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn("DownloadData($SourceUrl)", text)
        self.assertIn("SHA256", text)
        self.assertIn("[PASS] REALDATA2 exact source verified", text)
        self.assertNotIn("ExternalDatasetFreezer", text)
        self.assertNotIn("CausalRowProducer", text)
        self.assertNotIn("import yfinance", text)
        self.assertNotIn("yf.download", text)

    def test_authority_doc_records_narrow_provenance_and_nonclaims(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("005930.KS", text)
        self.assertIn("bcef6f27b803ce89000e2fc336201ddeef7df015", text)
        self.assertIn("68e3b6d861b4bfcf39d9c09c6a073c271369d3a9", text)
        self.assertIn("market_data_authenticity_verified = false", text)
        self.assertIn("real_data_claim = false", text)
        self.assertIn("nearest-time", text)
        self.assertIn("fill-forward", text)
        self.assertIn("interpolation", text)


if __name__ == "__main__":
    unittest.main()
