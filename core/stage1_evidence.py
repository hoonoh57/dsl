"""Structured Stage 1 evidence derived from one deterministic backtest result."""
from __future__ import annotations
from collections import Counter
from typing import Any, Dict, Optional

from core.stage1_order_evidence import strategy_market_order_lifecycle


class EvidenceBuilder:
    @staticmethod
    def _execution_cost(trade: dict, settings: dict) -> dict:
        quantity = float(trade.get("quantity", 0.0) or 0.0)
        entry = float(trade.get("entry_price", 0.0) or 0.0)
        exit_ = float(trade.get("exit_price", 0.0) or 0.0)
        direction = str(trade.get("direction", "LONG"))
        commission_rate = float(settings.get("commission_pct", 0.0) or 0.0) / 100.0
        tax_rate = float(settings.get("sell_tax_pct", 0.0) or 0.0) / 100.0
        slippage_rate = float(settings.get("slippage_pct", 0.0) or 0.0) / 100.0

        entry_notional = quantity * entry
        exit_notional = quantity * exit_
        entry_commission = entry_notional * commission_rate
        exit_commission = exit_notional * commission_rate
        entry_is_sell = direction == "SHORT"
        exit_is_sell = direction == "LONG"
        entry_tax = entry_notional * tax_rate if entry_is_sell else 0.0
        exit_tax = exit_notional * tax_rate if exit_is_sell else 0.0

        def slippage_cost(fill: float, is_buy: bool) -> float:
            if fill <= 0 or quantity <= 0 or slippage_rate <= 0:
                return 0.0
            if is_buy:
                reference = fill / (1.0 + slippage_rate)
                return max(0.0, (fill - reference) * quantity)
            if slippage_rate >= 1:
                return 0.0
            reference = fill / (1.0 - slippage_rate)
            return max(0.0, (reference - fill) * quantity)

        entry_slippage = slippage_cost(entry, is_buy=direction == "LONG")
        exit_slippage = slippage_cost(exit_, is_buy=direction == "SHORT")
        commission = entry_commission + exit_commission
        tax = entry_tax + exit_tax
        slippage = entry_slippage + exit_slippage
        recorded_fee = float(trade.get("entry_fee", 0.0) or 0.0) + float(trade.get("exit_fee", 0.0) or 0.0)
        return {
            "commission": commission,
            "tax": tax,
            "slippage": slippage,
            "recorded_fee_tax": recorded_fee,
            "total_execution_cost": commission + tax + slippage,
        }

    @staticmethod
    def build(experiment: Dict[str, Any], search_summary: Optional[Dict[str, Any]] = None) -> dict:
        result = experiment.get("result", {})
        metrics = dict(result.get("metrics_numeric", {}))
        diagnostics = dict(result.get("diagnostics", {}))
        settings = dict(result.get("settings", experiment.get("execution", {})) or {})
        closed = list(result.get("closed_trades", []))
        executions = list(result.get("trades", []))
        bars = int(diagnostics.get("bars", len(result.get("candles", []))) or 0)
        holding_bars = sum(max(0, int(item.get("holding_bars", 0) or 0)) for item in closed)
        exposure = min(100.0, holding_bars / bars * 100.0) if bars else 0.0
        exit_reasons = Counter(str(item.get("exit_reason", "UNKNOWN")) for item in closed)
        entry_reasons = Counter(str(item.get("entry_reason", "UNKNOWN")) for item in closed)
        net_pnls = [float(item.get("net_pnl", 0.0) or 0.0) for item in closed]
        gross_pnls = [float(item.get("gross_pnl", 0.0) or 0.0) for item in closed]
        returns = [float(item.get("return_pct", 0.0) or 0.0) for item in closed]
        entry_count = sum(1 for row in executions if row.get("kind") == "ENTRY")
        exit_count = sum(1 for row in executions if row.get("kind") == "EXIT")
        trade_evidence = []
        costs = []
        for trade in closed:
            cost = EvidenceBuilder._execution_cost(trade, settings)
            costs.append(cost)
            realized = float(trade.get("return_pct", 0.0) or 0.0)
            mfe = float(trade.get("mfe_pct", 0.0) or 0.0)
            trade_evidence.append({
                "trade_id": trade.get("trade_id"),
                "direction": trade.get("direction"),
                "signal_time": trade.get("signal_time"),
                "order_time": trade.get("signal_time"),
                "fill_time": trade.get("entry_time"),
                "fill_price": trade.get("entry_price"),
                "exit_signal_time": trade.get("exit_signal_time"),
                "exit_order_time": trade.get("exit_signal_time"),
                "exit_fill_time": trade.get("exit_time"),
                "exit_price": trade.get("exit_price"),
                "entry_reason": trade.get("entry_reason"),
                "exit_reason": trade.get("exit_reason"),
                "mfe_pct": mfe,
                "mae_pct": trade.get("mae_pct", 0.0),
                "return_pct": realized,
                "mfe_giveback_pct": mfe - realized,
                "gross_pnl": trade.get("gross_pnl", 0.0),
                "net_pnl": trade.get("net_pnl", 0.0),
                "holding_bars": trade.get("holding_bars", 0),
                "execution_cost": cost,
            })
        signal_counts = diagnostics.get("signal_counts", {})
        commission = sum(item["commission"] for item in costs)
        tax = sum(item["tax"] for item in costs)
        slippage = sum(item["slippage"] for item in costs)
        worst = sorted(trade_evidence, key=lambda item: float(item.get("net_pnl", 0.0)))[:5]
        givebacks = sorted(trade_evidence, key=lambda item: float(item.get("mfe_giveback_pct", 0.0)), reverse=True)[:5]
        market_lifecycle = strategy_market_order_lifecycle(executions)
        pending_lifecycle = list(diagnostics.get("broker_history", []))
        return {
            "schema": "stage1_evidence/v3",
            "experiment_id": experiment.get("id"),
            "data": experiment.get("provenance", {}),
            "execution_settings": settings,
            "account": {
                **metrics,
                "exposure_pct_approx": exposure,
                "gross_closed_pnl": sum(gross_pnls),
                "net_closed_pnl": sum(net_pnls),
                "commission_cost": commission,
                "tax_cost": tax,
                "slippage_cost": slippage,
                "execution_cost_total": commission + tax + slippage,
                "closed_winners": sum(1 for value in net_pnls if value > 0),
                "closed_losers": sum(1 for value in net_pnls if value < 0),
            },
            "signal_funnel": {
                "boolean_condition_counts": signal_counts,
                "actual_entries": entry_count,
                "actual_exits": exit_count,
                "rejections": diagnostics.get("rejections", {}),
                "entry_reason_distribution": dict(entry_reasons),
                "exit_reason_distribution": dict(exit_reasons),
            },
            "order_lifecycle": {
                "strategy_market": market_lifecycle,
                "pending_limit_stop": pending_lifecycle,
            },
            "trade_summary": {
                "count": len(closed),
                "average_return_pct": sum(returns) / len(returns) if returns else 0.0,
                "best_return_pct": max(returns, default=0.0),
                "worst_return_pct": min(returns, default=0.0),
                "average_mfe_pct": diagnostics.get("average_mfe_pct", 0.0),
                "average_mae_pct": diagnostics.get("average_mae_pct", 0.0),
                "average_realized_return_pct": diagnostics.get("average_realized_return_pct", 0.0),
                "mfe_giveback_pct": diagnostics.get("mfe_giveback_pct", 0.0),
                "worst_trades": worst,
                "largest_mfe_givebacks": givebacks,
            },
            "trades": trade_evidence,
            "search": search_summary or {},
            "analysis": experiment.get("analysis", {}),
            "chart": {
                "candles": len(result.get("candles", [])),
                "indicator_series": [item.get("name") for item in result.get("indicators", [])],
                "marker_count": len(result.get("markers", [])),
            },
            "limitations": {
                "largest_missed_moves": "not_reported_without_a_separate_causal_definition",
                "exposure": "holding-bar approximation for current single-position Stage 1 engine",
                "market_order_lifecycle": "replayed from actual strategy-signal executions through the same deterministic BrokerEmulator for audit evidence",
            },
        }
