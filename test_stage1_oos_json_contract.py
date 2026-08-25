import json
import math
import unittest

from core.stage1_oos import _json_safe


class Stage1OOSJsonContractTest(unittest.TestCase):
    def test_non_finite_metrics_are_strict_json_safe(self):
        payload = {
            "metrics_numeric": {
                "profit_factor": float("inf"),
                "other": 1.25,
            },
            "nested": [float("-inf"), float("nan"), 3.0],
        }
        safe = _json_safe(payload)
        self.assertIsNone(safe["metrics_numeric"]["profit_factor"])
        self.assertEqual(safe["metrics_numeric"]["other"], 1.25)
        self.assertEqual(safe["nested"], [None, None, 3.0])
        encoded = json.dumps(safe, allow_nan=False)
        self.assertNotIn("Infinity", encoded)
        self.assertNotIn("NaN", encoded)


if __name__ == "__main__":
    unittest.main()
