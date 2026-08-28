import hashlib
import unittest

from core.multi_symbol_follower_external_dataset import (
    ExternalDatasetDeclaration,
    ExternalDatasetFreezer,
)


def declaration(**overrides):
    values = {
        "source_id": "vendor-file-202608",
        "source_kind": "EXTERNAL_HISTORICAL",
        "media_format": "CSV",
        "timeframe": "5m",
        "symbols": ("005930", "000660"),
        "first_observation": "20260801090000",
        "last_observation": "20260828153000",
        "record_count": 100,
        "metadata": {"fixture_contract_only": True},
    }
    values.update(overrides)
    return ExternalDatasetDeclaration(**values)


class ExternalDatasetFreezeTests(unittest.TestCase):
    def test_freeze_is_deterministic_and_research_only(self):
        raw = b"time,symbol,open,high,low,close,volume\n20260801090000,005930,1,2,1,2,10\n"
        one = ExternalDatasetFreezer.freeze(raw_bytes=raw, declaration=declaration())
        two = ExternalDatasetFreezer.freeze(raw_bytes=raw, declaration=declaration())
        self.assertEqual(one["dataset_manifest_hash"], two["dataset_manifest_hash"])
        self.assertTrue(one["content_hash_verified"])
        self.assertFalse(one["market_data_authenticity_verified"])
        self.assertFalse(one["real_data_claim"])
        self.assertFalse(one["operational_authority"])
        self.assertFalse(one["execution_authority"])
        self.assertFalse(one["deployment_authority"])

    def test_fixture_or_synthetic_source_kind_is_rejected(self):
        for kind in ("FIXTURE", "SYNTHETIC", "GENERATED", "MOCK", "TEST"):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, "source_kind"):
                    declaration(source_kind=kind).validate()

    def test_empty_or_non_bytes_payload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "비어"):
            ExternalDatasetFreezer.freeze(raw_bytes=b"", declaration=declaration())
        with self.assertRaisesRegex(ValueError, "bytes"):
            ExternalDatasetFreezer.freeze(raw_bytes="abc", declaration=declaration())

    def test_time_range_must_be_ordered(self):
        with self.assertRaisesRegex(ValueError, "last_observation"):
            declaration(first_observation="20260802100000", last_observation="20260801090000").validate()

    def test_symbols_and_record_count_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "symbols"):
            declaration(symbols=()).validate()
        with self.assertRaisesRegex(ValueError, "중복"):
            declaration(symbols=("005930", "005930")).validate()
        with self.assertRaisesRegex(ValueError, "record_count"):
            declaration(record_count=0).validate()

    def test_expected_hash_mismatch_fails_closed(self):
        raw = b"authoritative bytes"
        expected = hashlib.sha256(raw).hexdigest()
        result = ExternalDatasetFreezer.freeze(raw_bytes=raw, declaration=declaration(), expected_sha256=expected)
        self.assertEqual(result["content_sha256"], expected)
        with self.assertRaisesRegex(ValueError, "expected_sha256"):
            ExternalDatasetFreezer.freeze(raw_bytes=raw, declaration=declaration(), expected_sha256="0" * 64)

    def test_content_change_changes_dataset_identity(self):
        one = ExternalDatasetFreezer.freeze(raw_bytes=b"dataset-a", declaration=declaration())
        two = ExternalDatasetFreezer.freeze(raw_bytes=b"dataset-b", declaration=declaration())
        self.assertNotEqual(one["content_sha256"], two["content_sha256"])
        self.assertNotEqual(one["dataset_manifest_hash"], two["dataset_manifest_hash"])


if __name__ == "__main__":
    unittest.main()
