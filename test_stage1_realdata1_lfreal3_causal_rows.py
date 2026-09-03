import unittest
from unittest.mock import patch

from tools.admit_realdata1_causal_rows import (
    admit_realdata1_bytes,
    parse_causal_rows,
    validate_manifest_identity,
)


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
        "source_id": "github:example/source@commit:data.csv",
        "source_kind": "EXTERNAL_HISTORICAL",
        "media_format": "CSV",
        "timeframe": "1d",
        "symbols": ("000660.KS",),
        "first_observation": "20240415000000",
        "last_observation": "20240416000000",
        "record_count": 2,
        "byte_count": 123,
        "content_sha256": "fixture-sha",
        "metadata": {"contract_fixture_only": True},
        "dataset_manifest_hash": "fixture-manifest",
    }
    base.update(overrides)
    return base


def csv_bytes() -> bytes:
    return (
        "\ufeffdate,open,high,low,close,volume,return,next_close,direction\n"
        "2024-04-15,100,110,90,105,1000,NOT_ADMITTED,999999,FUTURE\n"
        "2024-04-16,105,115,100,110,1200,NOT_ADMITTED,888888,FUTURE\n"
    ).encode("utf-8")


class Realdata1Lfreal3CausalRowsTests(unittest.TestCase):
    def test_parser_keeps_only_causal_ohlcv_and_normalizes_daily_time(self):
        rows = parse_causal_rows(raw_bytes=csv_bytes(), symbol="000660.KS")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].time, "20240415000000")
        self.assertEqual(rows[-1].time, "20240416000000")
        self.assertEqual(rows[0].symbol, "000660.KS")
        self.assertFalse(hasattr(rows[0], "return"))
        self.assertFalse(hasattr(rows[0], "next_close"))
        self.assertFalse(hasattr(rows[0], "direction"))

    def test_missing_causal_column_fails_closed(self):
        raw = b"date,open,high,low,close\n2024-04-15,100,110,90,105\n"
        with self.assertRaisesRegex(ValueError, "missing causal columns"):
            parse_causal_rows(raw_bytes=raw, symbol="000660.KS")

    def test_invalid_daily_date_fails_closed(self):
        raw = b"date,open,high,low,close,volume\n2024/04/15,100,110,90,105,1000\n"
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            parse_causal_rows(raw_bytes=raw, symbol="000660.KS")

    def test_manifest_must_match_identity_recomputed_from_exact_source_bytes(self):
        canonical = manifest()
        with patch(
            "tools.admit_realdata1_causal_rows.freeze_realdata1_bytes",
            return_value=canonical,
        ):
            accepted = validate_manifest_identity(raw_bytes=b"caller-bytes", manifest=dict(canonical))
            self.assertEqual(accepted["dataset_manifest_hash"], "fixture-manifest")
            tampered = dict(canonical)
            tampered["record_count"] = 3
            with self.assertRaisesRegex(ValueError, "does not match"):
                validate_manifest_identity(raw_bytes=b"caller-bytes", manifest=tampered)

    def test_adapter_routes_rows_through_existing_lfreal3_and_excludes_future_columns(self):
        canonical = manifest()
        with patch(
            "tools.admit_realdata1_causal_rows.freeze_realdata1_bytes",
            return_value=canonical,
        ):
            one = admit_realdata1_bytes(raw_bytes=csv_bytes(), manifest=canonical)
            two = admit_realdata1_bytes(raw_bytes=csv_bytes(), manifest=canonical)
        self.assertEqual(one["row_bundle_hash"], two["row_bundle_hash"])
        self.assertEqual(one["mode"], "RESEARCH_ROWS_ONLY")
        self.assertEqual(one["record_count"], 2)
        self.assertEqual(one["first_observation"], "20240415000000")
        self.assertEqual(one["last_observation"], "20240416000000")
        self.assertFalse(one["operational_authority"])
        self.assertFalse(one["deployment_authority"])
        self.assertFalse(one["real_data_claim"])
        for row in one["rows"]:
            self.assertEqual(
                set(row),
                {"symbol", "time", "open", "high", "low", "close", "volume"},
            )

    def test_existing_lfreal3_ohlc_guard_remains_authoritative(self):
        bad = (
            b"date,open,high,low,close,volume,return,next_close,direction\n"
            b"2024-04-15,100,99,90,105,1000,0,0,0\n"
            b"2024-04-16,105,115,100,110,1200,0,0,0\n"
        )
        canonical = manifest()
        with patch(
            "tools.admit_realdata1_causal_rows.freeze_realdata1_bytes",
            return_value=canonical,
        ):
            with self.assertRaisesRegex(ValueError, "OHLC"):
                admit_realdata1_bytes(raw_bytes=bad, manifest=canonical)


if __name__ == "__main__":
    unittest.main()
