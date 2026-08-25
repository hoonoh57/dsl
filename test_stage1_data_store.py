import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from core import stage1_data_store
from core.strategy_factory import DataContract


class Stage1DataStoreContractTest(unittest.TestCase):
    def _market(self):
        return {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000.0, 1100.0, 1200.0],
        }

    def test_same_rows_with_different_provenance_share_one_content_snapshot(self):
        first, first_provenance = DataContract.normalize(
            self._market(), instrument="AAA", timeframe="1d", source="source-a"
        )
        second, second_provenance = DataContract.normalize(
            self._market(), instrument="BBB", timeframe="1d", source="source-b"
        )
        self.assertEqual(first_provenance.data_hash, second_provenance.data_hash)
        self.assertNotEqual(first["_meta"]["instrument"], second["_meta"]["instrument"])

        with tempfile.TemporaryDirectory() as folder, patch.object(
            stage1_data_store, "DATA_DIR", Path(folder) / "stage1_data"
        ):
            data_hash = stage1_data_store.save_market_snapshot(first)
            self.assertEqual(stage1_data_store.save_market_snapshot(second), data_hash)
            loaded = stage1_data_store.load_market_snapshot(data_hash)
            for key in ("time", "open", "high", "low", "close", "volume"):
                self.assertEqual(loaded[key], first[key])

    def test_claimed_hash_must_match_actual_rows(self):
        normalized, provenance = DataContract.normalize(
            self._market(), instrument="AAA", timeframe="1d", source="source-a"
        )
        corrupt = deepcopy(normalized)
        corrupt["close"][1] = 102.5
        with tempfile.TemporaryDirectory() as folder, patch.object(
            stage1_data_store, "DATA_DIR", Path(folder) / "stage1_data"
        ):
            with self.assertRaisesRegex(ValueError, "payload.*data_hash"):
                stage1_data_store.save_market_snapshot(corrupt)
            self.assertFalse(stage1_data_store.has_market_snapshot(provenance.data_hash))


if __name__ == "__main__":
    unittest.main()
