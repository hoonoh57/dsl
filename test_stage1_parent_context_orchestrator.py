import copy
import unittest
from datetime import datetime, timedelta

from core.backtest import BacktestEngine
from core.market_parent_feature_provider import (
    KrxBenchmarkMarketParentFeatureProvider,
    MarketParentFeatureConfig,
)
from core.parent_context_orchestrator import (
    BUILD_POLICY,
    RootParentContextFrameBuilder,
)
from core.parent_feature_provider import ParentFeatureProviderResult


def benchmark_rows(count=60, *, step=0.30):
    start = datetime(2026, 8, 27, 9, 0, 0)
    rows = []
    for index in range(count):
        timestamp = (start + timedelta(minutes=5 * index)).strftime("%Y%m%d%H%M%S")
        close = 100.0 + index * step + (0.04 if index % 4 == 0 else -0.01)
        rows.append(
            {
                "time": timestamp,
                "open": close - 0.10,
                "high": close + 0.40,
                "low": close - 0.35,
                "close": close,
                "volume": 1000.0 + index * 13.0,
            }
        )
    return rows


class FixtureSessionMarketProvider:
    def __init__(self, rows, *, instrument, source):
        self.rows = copy.deepcopy(rows)
        self.instrument = instrument
        self.source = source
        self.calls = []

    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        self.calls.append(
            {
                "symbol": symbol,
                "session_date": session_date,
                "timeframe": timeframe,
                "required_bars": required_bars,
                "end_time": end_time,
            }
        )
        cutoff = session_date + end_time
        selected = [row for row in self.rows if row["time"] <= cutoff][-required_bars:]
        market = {
            key: [row[key] for row in selected]
            for key in ("time", "open", "high", "low", "close", "volume")
        }
        market["_meta"] = {
            "source": self.source,
            "instrument": self.instrument,
            "timeframe": timeframe,
        }
        return market


def config():
    return MarketParentFeatureConfig(
        timeframe="5m",
        short_return_bars=2,
        long_return_bars=6,
        sma_period=8,
        slope_bars=3,
        atr_period=6,
        volume_period=8,
    )


def provider(source, *, instrument="KOSPI", namespace="kospi"):
    return KrxBenchmarkMarketParentFeatureProvider(
        source,
        benchmark_symbol=instrument,
        feature_namespace=namespace,
        source_authority=f"FIXTURE_{instrument}",
        config=config(),
    )


def target_market(*, duplicate=False, instrument="005930", include_instrument=True):
    source_rows = benchmark_rows()
    chosen = source_rows[30:35]
    times = [row["time"] for row in chosen]
    if duplicate:
        times[3] = times[2]
    close = [70000.0 + index * 100.0 for index in range(len(times))]
    market = {
        "time": times,
        "open": [item - 50.0 for item in close],
        "high": [item + 150.0 for item in close],
        "low": [item - 150.0 for item in close],
        "close": close,
        "volume": [10000.0 + index * 500.0 for index in range(len(times))],
        "_meta": {
            "source": "fixture://target/005930",
            "timeframe": "5m",
        },
    }
    if include_instrument:
        market["_meta"]["instrument"] = instrument
    return market


class DependencySmugglingProvider:
    def __init__(self, base):
        self.base = base

    @property
    def manifest(self):
        return self.base.manifest

    def build(self, *, as_of, knowledge_cutoff, dependencies=None):
        result = self.base.build(
            as_of=as_of,
            knowledge_cutoff=knowledge_cutoff,
            dependencies=dependencies,
        )
        return ParentFeatureProviderResult(
            manifest=result.manifest,
            as_of=result.as_of,
            knowledge_cutoff=result.knowledge_cutoff,
            source=result.source,
            features=result.features,
            dependency_result_hashes=("unexpected-parent-hash",),
            metadata=result.metadata,
        )


class ParentContextOrchestratorTests(unittest.TestCase):
    def test_precomputes_every_exact_target_bar_and_runs_through_backtest(self):
        benchmark_source = FixtureSessionMarketProvider(
            benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi"
        )
        market_provider = provider(benchmark_source)
        market = target_market()
        bundle = RootParentContextFrameBuilder.build(
            frame_id="PCTX2C_KOSPI_005930",
            target_market=market,
            providers=(market_provider,),
            mode="DEPLOYMENT",
        )

        self.assertEqual(bundle.frame.target_symbol, "005930")
        self.assertEqual(bundle.target_times, tuple(market["time"]))
        self.assertEqual(
            tuple(point.target_time for point in bundle.frame.points),
            tuple(market["time"]),
        )
        self.assertEqual(len(benchmark_source.calls), len(market["time"]))
        self.assertEqual(
            [call["end_time"] for call in benchmark_source.calls],
            [stamp[8:14] for stamp in market["time"]],
        )
        self.assertEqual(bundle.public_dict()["policy"], BUILD_POLICY)

        dsl = '''strategy "OrchestratedCtx" {
            timeframe = "5m"
            long_entry = ctx.market.kospi_regime_state == "UPTREND" and ctx.market.kospi_return_short_pct > 0
            long_exit = false
            on(long_entry) { order.buy(type = "MARKET") }
        }'''
        result = BacktestEngine.run(
            dsl,
            market=market,
            parent_context_frame=bundle.frame,
            parent_feature_registry=bundle.registry,
        )
        self.assertEqual(result["metrics_numeric"]["trade_count"], 1)
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")
        self.assertEqual(
            result["diagnostics"]["parent_context"]["frame_hash"],
            bundle.frame.frame_hash,
        )

    def test_provider_order_does_not_change_registry_frame_or_build_identity(self):
        rows_a = benchmark_rows(step=0.30)
        rows_b = benchmark_rows(step=0.18)
        first = provider(
            FixtureSessionMarketProvider(rows_a, instrument="KOSPI", source="fixture://benchmark/kospi"),
            instrument="KOSPI",
            namespace="kospi",
        )
        second = provider(
            FixtureSessionMarketProvider(rows_b, instrument="KOSDAQ", source="fixture://benchmark/kosdaq"),
            instrument="KOSDAQ",
            namespace="kosdaq",
        )
        market = target_market()
        a = RootParentContextFrameBuilder.build(
            frame_id="ORDER_INVARIANT",
            target_market=market,
            providers=(first, second),
            mode="OBSERVED",
        )

        first_b = provider(
            FixtureSessionMarketProvider(rows_a, instrument="KOSPI", source="fixture://benchmark/kospi"),
            instrument="KOSPI",
            namespace="kospi",
        )
        second_b = provider(
            FixtureSessionMarketProvider(rows_b, instrument="KOSDAQ", source="fixture://benchmark/kosdaq"),
            instrument="KOSDAQ",
            namespace="kosdaq",
        )
        b = RootParentContextFrameBuilder.build(
            frame_id="ORDER_INVARIANT",
            target_market=market,
            providers=(second_b, first_b),
            mode="OBSERVED",
        )
        self.assertEqual(a.registry.registry_hash, b.registry.registry_hash)
        self.assertEqual(a.frame.frame_hash, b.frame.frame_hash)
        self.assertEqual(a.build_hash, b.build_hash)
        self.assertEqual(a.provider_ids, tuple(sorted(a.provider_ids)))

    def test_observed_build_remains_evidence_only_for_backtest_execution(self):
        source = FixtureSessionMarketProvider(
            benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi"
        )
        bundle = RootParentContextFrameBuilder.build(
            frame_id="OBSERVED_ONLY",
            target_market=target_market(),
            providers=(provider(source),),
            mode="OBSERVED",
        )
        self.assertEqual(bundle.frame.mode, "OBSERVED")
        dsl = '''strategy "ObservedRejected" {
            timeframe = "5m"
            long_entry = ctx.market.kospi_return_short_pct > 0
            long_exit = false
        }'''
        with self.assertRaisesRegex(ValueError, "DEPLOYMENT"):
            BacktestEngine.run(
                dsl,
                market=target_market(),
                parent_context_frame=bundle.frame,
                parent_feature_registry=bundle.registry,
            )

    def test_target_timeline_identity_is_fail_closed(self):
        source = FixtureSessionMarketProvider(
            benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi"
        )
        market_provider = provider(source)
        with self.assertRaisesRegex(ValueError, "중복"):
            RootParentContextFrameBuilder.build(
                frame_id="DUPLICATE",
                target_market=target_market(duplicate=True),
                providers=(market_provider,),
            )
        with self.assertRaisesRegex(ValueError, "instrument"):
            RootParentContextFrameBuilder.build(
                frame_id="NO_INSTRUMENT",
                target_market=target_market(include_instrument=False),
                providers=(market_provider,),
            )
        malformed = target_market()
        malformed["time"][0] = "20260827"
        with self.assertRaisesRegex(ValueError, "YYYYMMDDHHMMSS"):
            RootParentContextFrameBuilder.build(
                frame_id="BAD_TIME",
                target_market=malformed,
                providers=(market_provider,),
            )

    def test_duplicate_provider_identity_is_rejected(self):
        first = provider(
            FixtureSessionMarketProvider(
                benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi/a"
            )
        )
        second = provider(
            FixtureSessionMarketProvider(
                benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi/b"
            )
        )
        with self.assertRaisesRegex(ValueError, "중복"):
            RootParentContextFrameBuilder.build(
                frame_id="DUP_PROVIDER",
                target_market=target_market(),
                providers=(first, second),
            )

    def test_root_only_boundary_rejects_dependency_smuggling(self):
        base = provider(
            FixtureSessionMarketProvider(
                benchmark_rows(), instrument="KOSPI", source="fixture://benchmark/kospi"
            )
        )
        with self.assertRaisesRegex(ValueError, "dependencies"):
            RootParentContextFrameBuilder.build(
                frame_id="ROOT_ONLY",
                target_market=target_market(),
                providers=(DependencySmugglingProvider(base),),
                mode="OBSERVED",
            )


if __name__ == "__main__":
    unittest.main()
