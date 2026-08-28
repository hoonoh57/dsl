import unittest

from core.multi_symbol_follower_causal_rows import CausalMarketRow, CausalRowProducer


def manifest(**overrides):
    base = {
        "schema": "multi_symbol_follower_external_dataset/v1",
        "freeze_policy": "CALLER_BYTES_SHA256_IMMUTABLE_MANIFEST_RESEARCH_ONLY_NO_IO_NO_PROVIDER",
        "mode": "RESEARCH_DATASET_ONLY",
        "operational_authority": False,
        "execution_authority": False,
        "deployment_authority": False,
        "provider_authority": False,
        "file_io_authority": False,
        "content_hash_verified": True,
        "market_data_authenticity_verified": False,
        "real_data_claim": False,
        "source_id": "vendor-export-1",
        "source_kind": "VENDOR_EXPORT",
        "media_format": "CSV",
        "timeframe": "5m",
        "symbols": ("005930", "000660"),
        "first_observation": "20260828090000",
        "last_observation": "20260828090500",
        "record_count": 4,
        "byte_count": 100,
        "content_sha256": "abc123",
        "dataset_manifest_hash": "manifest-1",
        "metadata": {},
    }
    base.update(overrides)
    return base


def rows():
    return (
        CausalMarketRow("005930", "20260828090000", 100, 102, 99, 101, 1000),
        CausalMarketRow("000660", "20260828090000", 200, 202, 198, 201, 1200),
        CausalMarketRow("005930", "20260828090500", 101, 103, 100, 102, 1100),
        CausalMarketRow("000660", "20260828090500", 201, 203, 199, 200, 1300),
    )


class CausalRowProducerTests(unittest.TestCase):
    def test_admit_is_research_only_and_deterministic(self):
        one = CausalRowProducer.admit(manifest=manifest(), rows=rows())
        two = CausalRowProducer.admit(manifest=manifest(), rows=tuple(reversed(rows())))
        self.assertEqual(one["row_bundle_hash"], two["row_bundle_hash"])
        self.assertEqual(one["mode"], "RESEARCH_ROWS_ONLY")
        self.assertFalse(one["operational_authority"])
        self.assertFalse(one["execution_authority"])
        self.assertFalse(one["deployment_authority"])
        self.assertFalse(one["real_data_claim"])

    def test_manifest_record_count_must_match_rows(self):
        with self.assertRaisesRegex(ValueError, "row count"):
            CausalRowProducer.admit(manifest=manifest(record_count=3), rows=rows())

    def test_manifest_outside_symbol_rejected(self):
        bad = list(rows())
        bad[-1] = CausalMarketRow("035420", "20260828090500", 50, 52, 49, 51, 100)
        with self.assertRaisesRegex(ValueError, "manifest 밖의 symbol"):
            CausalRowProducer.admit(manifest=manifest(), rows=tuple(bad))

    def test_duplicate_symbol_time_rejected(self):
        bad = list(rows())
        bad[-1] = CausalMarketRow("005930", "20260828090500", 101, 103, 100, 102, 100)
        with self.assertRaisesRegex(ValueError, "중복"):
            CausalRowProducer.admit(manifest=manifest(), rows=tuple(bad))

    def test_manifest_time_boundaries_must_match_exactly(self):
        shifted = (
            CausalMarketRow("005930", "20260828090100", 100, 102, 99, 101, 1000),
            CausalMarketRow("000660", "20260828090100", 200, 202, 198, 201, 1200),
            CausalMarketRow("005930", "20260828090500", 101, 103, 100, 102, 1100),
            CausalMarketRow("000660", "20260828090500", 201, 203, 199, 200, 1300),
        )
        with self.assertRaisesRegex(ValueError, "정확히 일치"):
            CausalRowProducer.admit(manifest=manifest(), rows=shifted)

    def test_snapshot_is_strict_causal_prefix(self):
        bundle = CausalRowProducer.admit(manifest=manifest(), rows=rows())
        snap = CausalRowProducer.snapshot(row_bundle=bundle, cutoff="20260828090000")
        self.assertEqual(snap["row_count"], 2)
        self.assertTrue(snap["future_rows_excluded"])
        self.assertTrue(all(row["time"] <= snap["knowledge_cutoff"] for row in snap["rows"]))
        self.assertFalse(snap["deployment_authority"])

    def test_bad_ohlcv_or_future_cutoff_fails_closed(self):
        bad = list(rows())
        bad[0] = CausalMarketRow("005930", "20260828090000", 100, 99, 98, 101, 1000)
        with self.assertRaisesRegex(ValueError, "OHLC"):
            CausalRowProducer.admit(manifest=manifest(), rows=tuple(bad))
        bundle = CausalRowProducer.admit(manifest=manifest(), rows=rows())
        with self.assertRaisesRegex(ValueError, "observation 범위"):
            CausalRowProducer.snapshot(row_bundle=bundle, cutoff="20260828091000")


if __name__ == "__main__":
    unittest.main()
