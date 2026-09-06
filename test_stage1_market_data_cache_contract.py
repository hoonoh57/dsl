import inspect
import unittest

from cascade_lab.data.cache_contract import (
    CACHE_MANIFEST_SCHEMA,
    CacheContractError,
    CacheDatasetManifest,
    SourceDatasetStatus,
    assess_cache,
    source_fingerprint,
)


class MarketDataCacheContractTests(unittest.TestCase):
    def _status(self, **overrides):
        raw = {
            "dataset_id": "korean-equity-daily",
            "row_count": 3307249,
            "instrument_count": 2599,
            "earliest": "2021-01-04",
            "latest": "2026-09-04",
            "revision": "source-revision-1",
        }
        raw.update(overrides)
        return SourceDatasetStatus.from_mapping(raw)

    def _manifest(self, status=None, **cache_overrides):
        status = status or self._status()
        cache = {
            "format": "parquet",
            "root": "parquet/daily",
            "partition_by": ["year", "month"],
        }
        cache.update(cache_overrides)
        return CacheDatasetManifest.from_mapping(
            {
                "schema": CACHE_MANIFEST_SCHEMA,
                "dataset_id": status.dataset_id,
                "cache": cache,
                "source": status.public_dict(),
                "source_fingerprint": source_fingerprint(status),
                "generated_at_utc": "2026-09-06T01:00:00Z",
            }
        )

    def test_identical_source_status_is_cache_ready(self):
        status = self._status()
        assessment = assess_cache(self._manifest(status), status)
        self.assertTrue(assessment.ready)
        self.assertEqual(assessment.reasons, ())

    def test_any_source_revision_change_invalidates_cache(self):
        original = self._status()
        current = self._status(revision="source-revision-2")
        assessment = assess_cache(self._manifest(original), current)
        self.assertFalse(assessment.ready)
        self.assertEqual(assessment.reasons, ("SOURCE_FINGERPRINT_CHANGED",))

    def test_coverage_change_invalidates_cache(self):
        original = self._status()
        current = self._status(row_count=3307250, latest="2026-09-05")
        self.assertFalse(assess_cache(self._manifest(original), current).ready)

    def test_manifest_is_parquet_only_and_path_is_relative(self):
        with self.assertRaises(CacheContractError):
            self._manifest(format="csv")
        with self.assertRaises(CacheContractError):
            self._manifest(root="../outside")
        with self.assertRaises(CacheContractError):
            self._manifest(partition_by=[])

    def test_manifest_fingerprint_is_self_validating(self):
        status = self._status()
        raw = self._manifest(status).public_dict()
        raw["source_fingerprint"] = "wrong"
        with self.assertRaises(CacheContractError):
            CacheDatasetManifest.from_mapping(raw)

    def test_cache_contract_does_not_own_mysql_or_market_schema(self):
        source = inspect.getsource(__import__("cascade_lab.data.cache_contract", fromlist=["*"]))
        lowered = source.lower()
        for forbidden in (
            "pymysql",
            "mysql_host",
            "mysql_password",
            "korean_equity_daily",
            "korean_equity_minute_1m",
            "select ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
