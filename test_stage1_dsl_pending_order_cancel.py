import unittest

from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntimeError


class DslPendingOrderCancelIntegrationTests(unittest.TestCase):
    @staticmethod
    def market():
        return {
            "time": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [101.0, 101.0, 101.0, 101.0],
            "low": [99.0, 95.0, 80.0, 80.0],
            "close": [100.0, 100.0, 100.0, 100.0],
            "volume": [1000.0, 1000.0, 1000.0, 1000.0],
            "_meta": {"source": "fixture", "timeframe": "1d"},
        }

    @staticmethod
    def code():
        return '''
strategy "cancel pending" {
    timeframe = "1d"
    on(date == 20240101) {
        order.buy(type="LIMIT", id="entry-1", limit=90)
    }
    on(date == 20240102) {
        order.cancel(id="entry-1")
    }
}
'''

    def test_bar_close_cancels_before_later_fill(self):
        result = BacktestEngine.run(self.code(), market=self.market(), settings={"signal_mode": "bar_close"})
        history = result["diagnostics"]["pending_order_history"]
        self.assertEqual([row["status"] for row in history], ["CREATED", "ACCEPTED", "CANCELED"])
        self.assertEqual(history[-1]["client_order_id"], "entry-1")
        self.assertEqual(history[-1]["reason"], "DSL cancel")
        self.assertEqual(result["metrics_numeric"]["trade_count"], 0)

    def test_next_open_cancels_before_next_bar_matching(self):
        result = BacktestEngine.run(self.code(), market=self.market(), settings={"signal_mode": "next_open"})
        history = result["diagnostics"]["pending_order_history"]
        self.assertEqual([row["status"] for row in history], ["CREATED", "ACCEPTED", "CANCELED"])
        self.assertEqual(history[-1]["event"], "2024-01-03")
        self.assertEqual(result["metrics_numeric"]["trade_count"], 0)

    def test_cancel_unknown_client_identity_fails_closed(self):
        code = '''
strategy "unknown cancel" {
    timeframe = "1d"
    on(date == 20240101) {
        order.cancel(id="missing")
    }
}
'''
        with self.assertRaises(KeyError):
            BacktestEngine.run(code, market=self.market())

    def test_cancel_requires_nonempty_literal_id(self):
        missing = '''
strategy "missing id" {
    timeframe = "1d"
    on(date == 20240101) {
        order.cancel()
    }
}
'''
        dynamic = '''
strategy "dynamic id" {
    timeframe = "1d"
    on(date == 20240101) {
        order.cancel(id=close)
    }
}
'''
        with self.assertRaises(DSLRuntimeError):
            BacktestEngine.run(missing, market=self.market())
        with self.assertRaises(DSLRuntimeError):
            BacktestEngine.run(dynamic, market=self.market())

    def test_cancel_cannot_mix_with_other_order_command(self):
        code = '''
strategy "mixed cancel" {
    timeframe = "1d"
    on(date == 20240101) {
        order.buy(type="LIMIT", id="entry-1", limit=90)
        order.cancel(id="entry-1")
    }
}
'''
        with self.assertRaises(DSLRuntimeError):
            BacktestEngine.run(code, market=self.market())


if __name__ == "__main__":
    unittest.main()
