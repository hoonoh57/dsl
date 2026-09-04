"""Run the first real-data DSL strategy baseline on trusted REALDATA1 causal rows.

This is an edge/research runner only. It reuses the already trusted REALDATA1
causal derivation and the existing BacktestEngine. It does not add provider,
file, strategy, or execution authority to Core.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.backtest import BacktestEngine, StrategySettings  # noqa: E402
from tools.derive_realdata1_causal_dataset import (  # noqa: E402
    CAUSAL_COLUMNS,
    derive_realdata1_bytes,
)

DEFAULT_SOURCE_PATH = Path(tempfile.gettempdir()) / "dsl-realdata1-sk_hynix_price.csv"
DEFAULT_STRATEGY_PATH = ROOT / "examples" / "jma_cross.dsl"
EXPECTED_DERIVED_MANIFEST_HASH = "58acf49d4031938fd0099d99f7a105f8bbec3664a6478604d71daf2dbf370ae6"
EXPECTED_ROW_BUNDLE_HASH = "1428a6343635524723b828f6447b04d9d9ab9a3fe42b58e0776144f4fcd4bec2"
EXPECTED_RECORD_COUNT = 482
SYMBOL = "000660.KS"
TIMEFRAME = "1d"


def market_from_causal_bytes(causal_bytes: bytes, *, manifest_hash: str) -> dict[str, Any]:
    text = bytes(causal_bytes).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != tuple(CAUSAL_COLUMNS):
        raise ValueError(
            "REALSTRAT1 causal CSV columns changed. "
            f"expected={CAUSAL_COLUMNS} actual={tuple(reader.fieldnames or ())}"
        )
    rows = tuple(reader)
    if not rows:
        raise ValueError("REALSTRAT1 causal market has no rows.")

    def floats(name: str) -> list[float]:
        return [float(str(row[name]).strip()) for row in rows]

    market = {
        "time": [str(row["date"]).strip() for row in rows],
        "open": floats("open"),
        "high": floats("high"),
        "low": floats("low"),
        "close": floats("close"),
        "volume": floats("volume"),
        "_meta": {
            "source": "REALDATA1_CAUSAL_DERIVED",
            "symbol": SYMBOL,
            "timeframe": TIMEFRAME,
            "dataset_manifest_hash": manifest_hash,
        },
    }
    return market


def build_settings(args: argparse.Namespace) -> dict[str, Any]:
    settings = StrategySettings(
        total_capital=float(args.total_capital),
        allocation_pct=float(args.allocation_pct),
        signal_mode=str(args.signal_mode),
        stop_loss_pct=float(args.stop_loss_pct),
        take_profit_pct=float(args.take_profit_pct),
        commission_pct=float(args.commission_pct),
        sell_tax_pct=float(args.sell_tax_pct),
        slippage_pct=float(args.slippage_pct),
    )
    settings.validate()
    return asdict(settings)


def run_realdata1_strategy1(
    *,
    source_path: Path,
    strategy_path: Path,
    settings: dict[str, Any],
) -> dict[str, Any]:
    if not source_path.is_file():
        raise FileNotFoundError(f"REALDATA1 source file not found: {source_path}")
    if not strategy_path.is_file():
        raise FileNotFoundError(f"Strategy DSL file not found: {strategy_path}")

    derived_bytes, manifest, bundle, quarantined = derive_realdata1_bytes(source_path.read_bytes())
    if manifest["dataset_manifest_hash"] != EXPECTED_DERIVED_MANIFEST_HASH:
        raise ValueError("REALSTRAT1 derived LFREAL2 manifest identity changed.")
    if bundle["row_bundle_hash"] != EXPECTED_ROW_BUNDLE_HASH:
        raise ValueError("REALSTRAT1 LFREAL3 row bundle identity changed.")
    if int(bundle["record_count"]) != EXPECTED_RECORD_COUNT:
        raise ValueError("REALSTRAT1 trusted causal record count changed.")

    market = market_from_causal_bytes(
        derived_bytes,
        manifest_hash=str(manifest["dataset_manifest_hash"]),
    )
    strategy_code = strategy_path.read_text(encoding="utf-8")
    result = BacktestEngine.run(
        strategy_code,
        settings=settings,
        market=market,
        data_timeframe=TIMEFRAME,
    )
    metrics = dict(result.get("metrics_numeric") or {})
    report = {
        "schema": "realdata1_strategy1_backtest/v1",
        "strategy_path": str(strategy_path),
        "strategy_name": "JMA_7_50_Cross",
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "record_count": int(bundle["record_count"]),
        "quarantined_rows": len(quarantined),
        "dataset_manifest_hash": str(manifest["dataset_manifest_hash"]),
        "row_bundle_hash": str(bundle["row_bundle_hash"]),
        "settings": settings,
        "metrics_numeric": metrics,
        "closed_trade_count": len(result.get("closed_trades") or []),
        "execution_count": len(result.get("trades") or []),
        "execution_authority": str((result.get("diagnostics") or {}).get("execution_authority") or ""),
        "market_data_authenticity_verified": False,
        "real_data_claim": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backtest the first real-data DSL strategy baseline on trusted REALDATA1 causal rows."
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--strategy-path", type=Path, default=DEFAULT_STRATEGY_PATH)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--signal-mode", choices=("bar_close", "next_open"), default="next_open")
    parser.add_argument("--total-capital", type=float, default=10_000_000.0)
    parser.add_argument("--allocation-pct", type=float, default=100.0)
    parser.add_argument("--stop-loss-pct", type=float, default=0.0)
    parser.add_argument("--take-profit-pct", type=float, default=0.0)
    parser.add_argument("--commission-pct", type=float, default=0.015)
    parser.add_argument("--sell-tax-pct", type=float, default=0.18)
    parser.add_argument("--slippage-pct", type=float, default=0.0)
    args = parser.parse_args()

    settings = build_settings(args)
    report = run_realdata1_strategy1(
        source_path=args.source_path,
        strategy_path=args.strategy_path,
        settings=settings,
    )
    if args.report_path is not None:
        if not args.report_path.parent.is_dir():
            raise FileNotFoundError(f"Report parent directory not found: {args.report_path.parent}")
        args.report_path.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    metrics = report["metrics_numeric"]
    print(
        "[PASS] REALSTRAT1 REALDATA1 backtest completed; "
        f"rows={report['record_count']}; "
        f"closed_trades={report['closed_trade_count']}; "
        f"return_pct={metrics.get('total_return_pct')}; "
        f"final_equity={metrics.get('final_equity')}; "
        f"max_drawdown_pct={metrics.get('max_drawdown_pct')}; "
        f"total_cost={metrics.get('total_cost')}; "
        f"authority={report['execution_authority']}"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
