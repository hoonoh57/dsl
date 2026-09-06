import inspect
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from cascade_lab.data.cache_contract import (
    CACHE_MANIFEST_SCHEMA,
    SourceDatasetStatus,
    source_fingerprint,
)
from cascade_lab.data.local_cache import assess_local_cache
from cascade_lab.data.market_data_factory_port import MarketDataFactoryPort


class MarketDataFactoryPortTests(unittest.TestCase):
    def _status(self, revision="revision-1"):
        return SourceDatasetStatus.from_mapping(
            {
                "dataset_id": "korean-equity-daily",
                "row_count": 2,
                "instrument_count": 1,
                "earliest": "2026-09-03",
                "latest": "2026-09-04",
                "revision": revision,
            }
        )

    def _factory_root(self, root: Path) -> Path:
        factory = root / "market-data-factory"
        factory.mkdir()
        (factory / "package.json").write_text("{}\n", encoding="utf-8")
        return factory

    def test_port_uses_process_request_response_and_validates_status_fingerprint(self):
        calls = []
        status = self._status()

        def runner(args, **kwargs):
            calls.append((args, kwargs))
            payload = {
                "event": "status",
                "dataset_id": status.dataset_id,
                "source": status.public_dict(),
                "source_fingerprint": source_fingerprint(status),
            }
            return subprocess.CompletedProcess(args, 0, f"CACHE_EVENT {json.dumps(payload)}\n", "")

        with tempfile.TemporaryDirectory() as tmp:
            port = MarketDataFactoryPort(self._factory_root(Path(tmp)), runner=runner, npm_command="npm")
            actual = port.status("daily")

        self.assertEqual(actual, status)
        self.assertEqual(calls[0][0][0:4], ["npm", "run", "data:cache", "--"])
        self.assertIn("--command", calls[0][0])
        self.assertIn("status", calls[0][0])
        self.assertEqual(calls[0][1]["check"], False)

    def test_sync_requires_consistent_partition_counters(self):
        def runner(args, **kwargs):
            payload = {
                "event": "complete",
                "dataset_id": "korean-equity-daily",
                "source_fingerprint": "abc",
                "partitions": 5,
                "materialized": 2,
                "reused": 3,
            }
            return subprocess.CompletedProcess(args, 0, f"CACHE_EVENT {json.dumps(payload)}\n", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            port = MarketDataFactoryPort(self._factory_root(root), runner=runner, npm_command="npm")
            result = port.sync("daily", root / "DATA")

        self.assertEqual(result.partitions, 5)
        self.assertEqual(result.materialized, 2)
        self.assertEqual(result.reused, 3)

    def test_local_cache_requires_current_manifest_and_every_partition_file(self):
        status = self._status()
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "DATA"
            relative = "parquet/daily/generation=abc/year=2026/month=09/part.parquet"
            manifest = {
                "schema": CACHE_MANIFEST_SCHEMA,
                "dataset_id": status.dataset_id,
                "cache": {
                    "format": "parquet",
                    "root": "parquet/daily/generation=abc",
                    "partition_by": ["year", "month"],
                },
                "source": status.public_dict(),
                "source_fingerprint": source_fingerprint(status),
                "generated_at_utc": "2026-09-06T02:00:00Z",
                "partitions": {
                    "2026-09": {
                        "file": relative,
                        "row_count": 2,
                        "revision": "partition-revision",
                    }
                },
            }
            manifest_path = data_root / "manifest" / f"{status.dataset_id}.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            missing = assess_local_cache(data_root, status)
            self.assertFalse(missing.ready)
            self.assertEqual(missing.reasons, ("PARTITION_FILE_MISSING",))

            parquet = data_root.joinpath(*relative.split("/"))
            parquet.parent.mkdir(parents=True)
            parquet.write_bytes(b"PAR1")
            ready = assess_local_cache(data_root, status)
            self.assertTrue(ready.ready)

            stale = assess_local_cache(data_root, self._status(revision="revision-2"))
            self.assertFalse(stale.ready)
            self.assertEqual(stale.reasons, ("SOURCE_FINGERPRINT_CHANGED",))

    def test_dsl_cache_boundary_has_no_database_credentials_or_table_authority(self):
        from cascade_lab.data import local_cache, market_data_factory_port

        source = inspect.getsource(local_cache) + inspect.getsource(market_data_factory_port)
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
