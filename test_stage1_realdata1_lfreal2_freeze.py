import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import freeze_realdata1_dataset as realdata1


ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "tools" / "freeze_realdata1_dataset.py"


class RealData1Lfreal2FreezeTests(unittest.TestCase):
    def test_declaration_pins_realdata1_provenance_without_granting_core_io(self):
        declaration = realdata1.build_declaration()
        self.assertEqual(
            declaration.source_id,
            "github:hyekong/sk-hynix-news-dataset@339f0b6dc15531f374c51f715f12555153054009:sk_hynix_price.csv",
        )
        self.assertEqual(declaration.source_kind, "EXTERNAL_HISTORICAL")
        self.assertEqual(declaration.media_format, "CSV")
        self.assertEqual(declaration.timeframe, "1d")
        self.assertEqual(tuple(declaration.symbols), ("000660.KS",))
        self.assertEqual(declaration.first_observation, "20240415000000")
        self.assertEqual(declaration.last_observation, "20260413000000")
        self.assertEqual(declaration.record_count, 483)
        self.assertEqual(
            declaration.metadata["source_git_blob_sha1"],
            "84fb250326def7148cce6466026aaecf057e2013",
        )
        self.assertNotIn("source_path", declaration.metadata)
        self.assertNotIn("manifest_path", declaration.metadata)

    def test_adapter_delegates_exact_caller_bytes_to_existing_lfreal2_freezer(self):
        raw = b"x" * realdata1.EXPECTED_BYTE_COUNT
        expected_manifest = {
            "byte_count": realdata1.EXPECTED_BYTE_COUNT,
            "content_sha256": realdata1.EXPECTED_CONTENT_SHA256,
            "dataset_manifest_hash": "manifest-hash",
        }
        with patch.object(realdata1.ExternalDatasetFreezer, "freeze", return_value=expected_manifest) as freeze:
            result = realdata1.freeze_realdata1_bytes(raw)

        self.assertIs(result, expected_manifest)
        freeze.assert_called_once()
        kwargs = freeze.call_args.kwargs
        self.assertEqual(kwargs["raw_bytes"], raw)
        self.assertEqual(kwargs["expected_sha256"], realdata1.EXPECTED_CONTENT_SHA256)
        self.assertEqual(kwargs["declaration"], realdata1.build_declaration())

    def test_wrong_byte_count_or_content_hash_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "byte count mismatch"):
            realdata1.freeze_realdata1_bytes(b"not-the-pinned-source")

        wrong_but_same_length = b"x" * realdata1.EXPECTED_BYTE_COUNT
        self.assertNotEqual(hashlib.sha256(wrong_but_same_length).hexdigest(), realdata1.EXPECTED_CONTENT_SHA256)
        with self.assertRaisesRegex(ValueError, "expected_sha256"):
            realdata1.freeze_realdata1_bytes(wrong_but_same_length)

    def test_manifest_file_output_is_deterministic_and_path_independent(self):
        manifest = {
            "schema": "multi_symbol_follower_external_dataset/v1",
            "mode": "RESEARCH_DATASET_ONLY",
            "byte_count": realdata1.EXPECTED_BYTE_COUNT,
            "content_sha256": realdata1.EXPECTED_CONTENT_SHA256,
            "dataset_manifest_hash": "stable-manifest-hash",
            "market_data_authenticity_verified": False,
            "real_data_claim": False,
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "caller-source.csv"
            first = root / "manifest-a.json"
            second = root / "manifest-b.json"
            source.write_bytes(b"caller bytes")

            with patch.object(realdata1, "freeze_realdata1_bytes", return_value=manifest):
                one = realdata1.freeze_source_file(source_path=source, manifest_path=first)
                two = realdata1.freeze_source_file(source_path=source, manifest_path=second)

            self.assertEqual(one, two)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertNotIn(str(source), first.read_text(encoding="utf-8"))
            self.assertNotIn(str(first), first.read_text(encoding="utf-8"))

    def test_tool_keeps_provider_network_and_row_parsing_outside_this_boundary(self):
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn("ExternalDatasetFreezer", text)
        self.assertIn("source_path.read_bytes()", text)
        self.assertNotIn("import requests", text)
        self.assertNotIn("import urllib", text)
        self.assertNotIn("WebClient", text)
        self.assertNotIn("import yfinance", text)
        self.assertNotIn("import pandas", text)
        self.assertNotIn("csv.reader", text)
        self.assertNotIn("next_close", text)
        self.assertNotIn("direction", text)


if __name__ == "__main__":
    unittest.main()
