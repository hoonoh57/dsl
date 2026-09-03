import unittest
from unittest.mock import patch

from tools import derive_realdata1_causal_dataset as derived


def fixture_bytes() -> bytes:
    return (
        "\ufeffdate,open,high,low,close,volume,return,next_close,direction\n"
        "2024-10-11,100,110,90,105,1000,0,999,0\n"
        "2024-10-14,106,115,106,105,1200,0,999,0\n"
        "2024-10-15,107,116,104,112,1300,0,999,1\n"
    ).encode("utf-8")


class Realdata1CausalDatasetTests(unittest.TestCase):
    def test_projection_quarantines_invalid_row_without_correcting_source_values(self):
        causal_bytes, rows, quarantined = derived.derive_causal_projection(
            raw_bytes=fixture_bytes(),
            symbol="000660.KS",
        )
        text = causal_bytes.decode("utf-8")
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]["time"], "20241014000000")
        self.assertEqual(quarantined[0]["low"], "106")
        self.assertEqual(quarantined[0]["close"], "105")
        self.assertNotIn("2024-10-14", text)
        self.assertIn("2024-10-11,100,110,90,105,1000", text)
        self.assertIn("2024-10-15,107,116,104,112,1300", text)
        self.assertNotIn("return", text)
        self.assertNotIn("next_close", text)
        self.assertNotIn("direction", text)

    def test_projection_uses_existing_lfreal3_row_guard_as_quarantine_authority(self):
        raw = fixture_bytes()
        with patch(
            "tools.derive_realdata1_causal_dataset.parse_causal_rows",
            wraps=derived.parse_causal_rows,
        ) as parser:
            _, rows, quarantined = derived.derive_causal_projection(raw_bytes=raw, symbol="000660.KS")
        parser.assert_called_once()
        self.assertEqual(len(rows), 2)
        self.assertEqual(quarantined[0]["reason"], "LFREAL3 OHLC 관계가 올바르지 않습니다.")

    def test_exact_parent_manifest_and_expected_quarantine_are_fail_closed(self):
        parent = {
            "dataset_manifest_hash": derived.EXPECTED_PARENT_MANIFEST_HASH,
            "content_sha256": "parent-sha",
            "timeframe": "1d",
            "symbols": ("000660.KS",),
        }
        with patch.object(derived, "freeze_realdata1_bytes", return_value=parent), patch.object(
            derived,
            "derive_causal_projection",
            return_value=(
                b"date,open,high,low,close,volume\n2024-10-11,100,110,90,105,1000\n",
                (derived.parse_causal_rows(raw_bytes=b"date,open,high,low,close,volume\n2024-10-11,100,110,90,105,1000\n", symbol="000660.KS")[0],),
                (),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "quarantine set changed"):
                derived.derive_realdata1_bytes(b"caller")

        wrong_parent = dict(parent)
        wrong_parent["dataset_manifest_hash"] = "wrong"
        with patch.object(derived, "freeze_realdata1_bytes", return_value=wrong_parent):
            with self.assertRaisesRegex(ValueError, "parent LFREAL2 manifest hash"):
                derived.derive_realdata1_bytes(b"caller")

    def test_policy_pins_one_known_quarantine_and_no_source_correction(self):
        self.assertEqual(derived.EXPECTED_QUARANTINED_TIMES, ("20241014000000",))
        self.assertIn("QUARANTINE", derived.DERIVATION_POLICY)
        self.assertEqual(derived.SYMBOL, "000660.KS")


if __name__ == "__main__":
    unittest.main()
