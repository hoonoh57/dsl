"""Structured Stage 1 evidence derived from one deterministic backtest result."""
from __future__ import annotations
from collections import Counter
from typing import Any, Dict, Optional


class EvidenceBuilder:
    @staticmethod
    def build(experiment: Dict[str, Any], search_summary: Optional[Dict[str, Any]] = None) -> dict:
        result = experiment.get("result", {})
        metrics = dict(result.get("metrics_numeric", {}))
        diagnostics = dict(result.get("diagnostics", {}))
        closed = list(result.get("closed_trades", []))
        executions = list(result.get("trades", []))
        bars = int(diagnostics.get("bars", len(result.get("candles", []))) or 0)
        holding_bars = sum(max(0, int(item.get("holding_bars", 0) or 0)) for item in closed)
        exposure = min(100.0, holding_bars / bars * 100.0) if bars else 0.0
        exit_reasons = Counter(str(item.get("exit_reason", "UNKNOWN")) for item in closed)
        entry_reasons = Counter(str(item.get("entry_reason", "UNKNOWN")) for item in closed)
        net_pnls = [float(item.get("net_pnl", 0.0) or 0.0) for item in closed]
        returns = [float(item.get("return_pct", 0.0) or 0.0) for item in closed]
        entry_count = sum(1 for row in executions if row.get("kind") == "ENTRY")
        exit_count = sum(1 for row in executions if row.get("kind") == "EXIT")
        trade_evidence = []
        for trade in closed:
            trade_evidence.append({
                "trade_id": trade.get("trade_id"),
                "direction": trade.get("direction"),
                "signal_time": trade.get("signal_time"),
                "order_time": trade.get("entry_time"),
                "fill_time": trade.get("entry_time"),
                "fill_price": trade.get("entry_price"),
                "exit_signal_time": trade.get("exit_signal_time"),
                "exit_time": trade.get("exit_time"),
                "exit_price": trade.get("exit_price"),
                "entry_reason": trade.get("entry_reason"),
                "exit_reason": trade.get("exit_reason"),
                "mfe_pct": trade.get("mfe_pct", 0.0),
                "mae_pct": trade.get("mae_pct", 0.0),
                "return_pct": trade.get("return_pct", 0.0),
                "net_pnl": trade.get("net_pnl", 0.0),
                "holding_bars": trade.get("holding_bars", 0),
                "execution_cost": float(trade.get("entry_fee", 0.0) or 0.0) + float(trade.get("exit_fee", 0.0) or 0.0),
            })
        signal_counts = diagnostics.get("signal_counts", {})
        return {
            "schema": "stage1_evidence/v1",
            "experiment_id": experiment.get("id"),
            "data": experiment.get("provenance", {}),
            "account": {
                **metrics,
                "exposure_pct_approx": exposure,
                "net_closed_pnl": sum(net_pnls),
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
            "trade_summary": {
                "count": len(closed),
                "average_return_pct": sum(returns) / len(returns) if returns else 0.0,
                "best_return_pct": max(returns, default=0.0),
                "worst_return_pct": min(returns, default=0.0),
                "average_mfe_pct": diagnostics.get("average_mfe_pct", 0.0),
                "average_mae_pct": diagnostics.get("average_mae_pct", 0.0),
                "average_realized_return_pct": diagnostics.get("average_realized_return_pct", 0.0),
                "mfe_giveback_pct": diagnostics.get("mfe_giveback_pct", 0.0),
            },
            "trades": trade_evidence,
            "search": search_summary or {},
            "analysis": experiment.get("analysis", {}),
            "chart": {
                "candles": len(result.get("candles", [])),
                "indicator_series": [item.get("name") for item in result.get("indicators", [])],
                "marker_count": len(result.get("markers", [])),
            },
        }
