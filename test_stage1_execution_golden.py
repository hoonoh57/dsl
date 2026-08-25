import unittest

from core.backtest import BacktestEngine


LONG_DSL = '''strategy "GoldenLong" {
    timeframe = "1d"
    enter = close > close[1]
    leave = close < close[1]
    on(enter) { order.buy(type = "MARKET") }
    on(leave) { order.close_long() }
}'''


def long_market():
    return {
        "time": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "open": [100.0, 105.0, 95.0, 90.0],
        "high": [101.0, 111.0, 97.0, 92.0],
        "low": [99.0, 104.0, 89.0, 88.0],
        "close": [100.0, 110.0, 90.0, 91.0],
        "volume": [1000.0] * 4,
    }


class Stage1ExecutionGoldenTest(unittest.TestCase):
    def test_bar_close_market_orders_are_authoritative_broker_lifecycle(self):
        result = BacktestEngine.run(
            LONG_DSL,
            market=long_market(),
            settings={"signal_mode": "bar_close", "allocation_pct": 50.0,
                      "commission_pct": 0.1, "sell_tax_pct": 0.2, "slippage_pct": 0.0},
        )
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")
        executions = result["trades"]
        self.assertEqual([row["kind"] for row in executions], ["ENTRY", "EXIT"])
        history = result["diagnostics"]["broker_history"]
        by_order = {}
        for row in history:
            by_order.setdefault(row["order_id"], []).append(row)
        self.assertEqual(set(by_order), {row["order_id"] for row in executions})
        for execution in executions:
            rows = by_order[execution["order_id"]]
            self.assertEqual([row["status"] for row in rows], ["CREATED", "ACCEPTED", "FILLED"])
            self.assertEqual(rows[0]["event"], execution["signal_time"])
            self.assertEqual(rows[-1]["event"], execution["time"])
            self.assertAlmostEqual(rows[-1]["fill_price"], execution["price"], places=12)
            self.assertAlmostEqual(rows[-1]["quantity"], execution["quantity"], places=12)

    def test_long_accounting_reconciles_exactly_with_cost_model(self):
        result = BacktestEngine.run(
            LONG_DSL,
            market=long_market(),
            initial_capital=100_000.0,
            settings={"signal_mode": "bar_close", "allocation_pct": 50.0,
                      "commission_pct": 0.1, "sell_tax_pct": 0.2, "slippage_pct": 0.0},
        )
        trade = result["closed_trades"][0]
        qty = 50_000.0 / 110.0
        entry_fee = qty * 110.0 * 0.001
        exit_fee = qty * 90.0 * 0.003
        gross = qty * (90.0 - 110.0)
        expected_net = gross - entry_fee - exit_fee
        expected_final = 100_000.0 + expected_net
        self.assertAlmostEqual(trade["quantity"], qty, places=10)
        self.assertAlmostEqual(trade["entry_fee"], entry_fee, places=10)
        self.assertAlmostEqual(trade["exit_fee"], exit_fee, places=10)
        self.assertAlmostEqual(trade["gross_pnl"], gross, places=10)
        self.assertAlmostEqual(trade["net_pnl"], expected_net, places=10)
        self.assertAlmostEqual(result["metrics_numeric"]["final_equity"], expected_final, places=8)
        self.assertAlmostEqual(
            result["metrics_numeric"]["final_equity"] - result["metrics_numeric"]["initial_capital"],
            sum(item["net_pnl"] for item in result["closed_trades"]),
            places=8,
        )
        self.assertAlmostEqual(result["metrics_numeric"]["total_cost"], entry_fee + exit_fee, places=8)

    def test_next_open_lifecycle_preserves_signal_and_fill_times(self):
        result = BacktestEngine.run(
            LONG_DSL,
            market=long_market(),
            settings={"signal_mode": "next_open", "allocation_pct": 50.0,
                      "commission_pct": 0.0, "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        )
        executions = result["trades"]
        self.assertEqual(executions[0]["signal_time"], "2026-01-02")
        self.assertEqual(executions[0]["time"], "2026-01-03")
        self.assertEqual(executions[0]["price"], 95.0)
        history = result["diagnostics"]["strategy_market_order_history"]
        entry_rows = [row for row in history if row["order_id"] == executions[0]["order_id"]]
        self.assertEqual(entry_rows[0]["event"], "2026-01-02")
        self.assertEqual(entry_rows[-1]["event"], "2026-01-03")

    def test_risk_exit_uses_same_broker_authority(self):
        dsl = '''strategy "RiskExit" {
            timeframe = "1d"
            enter = close > close[1]
            on(enter) { order.buy(type = "MARKET") }
        }'''
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [100.0, 105.0, 110.0],
            "high": [101.0, 112.0, 111.0],
            "low": [99.0, 104.0, 90.0],
            "close": [100.0, 110.0, 95.0],
            "volume": [1000.0] * 3,
        }
        result = BacktestEngine.run(
            dsl,
            market=market,
            settings={"allocation_pct": 50.0, "stop_loss_pct": 5.0,
                      "commission_pct": 0.0, "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        )
        exit_execution = [row for row in result["trades"] if row["kind"] == "EXIT"][0]
        self.assertEqual(exit_execution["reason"], "STOP_LOSS")
        self.assertEqual(exit_execution["origin"], "RISK_EXIT")
        rows = [row for row in result["diagnostics"]["risk_exit_order_history"]
                if row["order_id"] == exit_execution["order_id"]]
        self.assertEqual([row["status"] for row in rows], ["CREATED", "ACCEPTED", "FILLED"])
        self.assertAlmostEqual(rows[-1]["fill_price"], exit_execution["price"], places=12)

    def test_pending_limit_fill_records_actual_execution_quantity_and_original_signal_time(self):
        dsl = '''strategy "Pending" {
            timeframe = "1d"
            signal = close > 0
            on(signal) { order.buy(type = "LIMIT", limit = 95, tif = "GTC") }
        }'''
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [100.0, 98.0, 97.0],
            "high": [101.0, 99.0, 98.0],
            "low": [99.0, 94.0, 96.0],
            "close": [100.0, 96.0, 97.0],
            "volume": [1000.0] * 3,
        }
        result = BacktestEngine.run(
            dsl,
            market=market,
            settings={"allocation_pct": 50.0, "commission_pct": 0.0,
                      "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        )
        entry = [row for row in result["trades"] if row["kind"] == "ENTRY"][0]
        rows = [row for row in result["diagnostics"]["pending_order_history"]
                if row["order_id"] == entry["order_id"]]
        self.assertEqual([row["status"] for row in rows], ["CREATED", "ACCEPTED", "FILLED"])
        self.assertEqual(entry["signal_time"], "2026-01-01")
        self.assertEqual(entry["time"], "2026-01-02")
        self.assertEqual(rows[0]["signal_time"], "2026-01-01")
        self.assertEqual(rows[-1]["event"], "2026-01-02")
        self.assertAlmostEqual(rows[-1]["quantity"], entry["quantity"], places=12)
        self.assertAlmostEqual(rows[-1]["fill_price"], entry["price"], places=12)


if __name__ == "__main__":
    unittest.main()
