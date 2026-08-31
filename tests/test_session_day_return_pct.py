import unittest

import numpy as np

from core.dsl_feature_catalog import FEATURE_CASES
from core.dsl_runtime import DSLRuntime, DSLRuntimeError
from core.function_registry import FUNCTION_SPECS


class SessionDayReturnPctTests(unittest.TestCase):
    @staticmethod
    def market():
        open_ = np.array([100.0, 101.0, 99.0, 200.0, 198.0, 202.0])
        close = np.array([100.0, 103.0, 97.0, 200.0, 210.0, 190.0])
        return {
            "open": open_,
            "high": np.maximum(open_, close) + 1.0,
            "low": np.minimum(open_, close) - 1.0,
            "close": close,
            "volume": np.full(6, 1000.0),
            "date": np.array([20260831.0, 20260831.0, 20260831.0, 20260901.0, 20260901.0, 20260901.0]),
            "time": np.array([90000.0, 90100.0, 90200.0, 90000.0, 90100.0, 90200.0]),
        }

    @staticmethod
    def code(expression="session.day_return_pct()"):
        return f'''strategy "SessionDayReturnPct" {{
    timeframe = "1m"
    day_return_pct = {expression}
    entry_cond = false
    on(entry_cond) {{ order.buy(type = "MARKET") }}
}}'''

    def test_registered_as_standard_session_feature(self):
        spec = FUNCTION_SPECS["session.day_return_pct"]
        self.assertEqual(spec.category, "session")
        self.assertEqual(spec.minimum, 0)
        self.assertEqual(spec.maximum, 0)
        self.assertEqual(spec.returns, "series<number>")
        self.assertIn("session.day_return_pct", FEATURE_CASES)

    def test_returns_percent_change_from_first_open_of_each_session(self):
        compiled = DSLRuntime.compile(self.code(), self.market())
        expected = np.array([0.0, 3.0, -3.0, 0.0, 5.0, -5.0])
        np.testing.assert_allclose(compiled.values["day_return_pct"], expected, atol=1e-12)

    def test_session_boundary_resets_reference_open(self):
        compiled = DSLRuntime.compile(self.code(), self.market())
        values = compiled.values["day_return_pct"]
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[3], 0.0)

    def test_bad_arity_fails_closed(self):
        with self.assertRaisesRegex(DSLRuntimeError, "인수 개수 오류"):
            DSLRuntime.compile(self.code("session.day_return_pct(1)"), self.market())


if __name__ == "__main__":
    unittest.main()
