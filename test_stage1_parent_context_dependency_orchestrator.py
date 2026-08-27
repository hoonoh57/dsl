import copy
import unittest
from datetime import datetime, timedelta

from core.backtest import BacktestEngine
from core.market_parent_feature_provider import (
    KrxBenchmarkMarketParentFeatureProvider,
    MarketParentFeatureConfig,
)
from core.parent_context_dependency_orchestrator import (
    BUILD_POLICY,
    DependencyParentContextFrameBuilder,
    ParentProviderNode,
)
from core.parent_feature_provider import ParentFeatureProviderResult
from core.sector_parent_feature_provider import (
    KrxSectorBenchmarkParentFeatureProvider,
    SectorParentFeatureConfig,
)


def rows(count=70, *, base=100.0, step=0.25):
    start = datetime(2026, 8, 27, 9, 0, 0)
    output = []
    for index in range(count):
        stamp = (start + timedelta(minutes=5 * index)).strftime("%Y%m%d%H%M%S")
        close = base + step * index + (0.03 if index % 4 == 0 else -0.01)
        output.append({
            "time": stamp,
            "open": close - 0.10,
            "high": close + 0.35,
            "low": close - 0.30,
            "close": close,
            "volume": 1000.0 + 11.0 * index,
        })
    return output


class FixtureSessionMarketProvider:
    def __init__(self, source_rows, *, instrument, source):
        self.rows = copy.deepcopy(source_rows)
        self.instrument = instrument
        self.source = source
        self.calls = []

    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        self.calls.append((symbol, session_date, timeframe, required_bars, end_time))
        cutoff = session_date + end_time
        selected = [item for item in self.rows if item["time"] <= cutoff][-required_bars:]
        market = {
            key: [item[key] for item in selected]
            for key in ("time", "open", "high", "low", "close", "volume")
        }
        market["_meta"] = {
            "source": self.source,
            "instrument": self.instrument,
            "timeframe": timeframe,
        }
        return market


def market_config():
    return MarketParentFeatureConfig(
        timeframe="5m",
        short_return_bars=2,
        long_return_bars=6,
        sma_period=8,
        slope_bars=3,
        atr_period=6,
        volume_period=8,
    )


def sector_config():
    return SectorParentFeatureConfig(
        timeframe="5m",
        short_return_bars=2,
        long_return_bars=6,
        sma_period=8,
        slope_bars=3,
    )


def market_provider(source):
    return KrxBenchmarkMarketParentFeatureProvider(
        source,
        benchmark_symbol="KOSPI",
        feature_namespace="kospi",
        source_authority="FIXTURE_KOSPI",
        config=market_config(),
    )


def sector_provider(source, parent):
    return KrxSectorBenchmarkParentFeatureProvider(
        source,
        sector_symbol="SECTOR_SEMI",
        sector_namespace="semiconductor",
        source_authority="FIXTURE_SECTOR_SEMI",
        market_dependency_provider_id=parent.manifest.provider_id,
        market_return_feature_id="market.kospi_return_long_pct",
        market_regime_feature_id="market.kospi_regime_state",
        config=sector_config(),
    )


def target_market():
    selected = rows()[35:40]
    close = [70000.0 + 100.0 * index for index in range(len(selected))]
    return {
        "time": [item["time"] for item in selected],
        "open": [item - 50.0 for item in close],
        "high": [item + 150.0 for item in close],
        "low": [item - 150.0 for item in close],
        "close": close,
        "volume": [10000.0 + 300.0 * index for index in range(len(selected))],
        "_meta": {
            "source": "fixture://target/005930",
            "instrument": "005930",
            "timeframe": "5m",
        },
    }


class WrongDependencyHashProvider:
    def __init__(self, base):
        self.base = base

    @property
    def manifest(self):
        return self.base.manifest

    def build(self, *, as_of, knowledge_cutoff, dependencies=None):
        original = self.base.build(
            as_of=as_of,
            knowledge_cutoff=knowledge_cutoff,
            dependencies=dependencies,
        )
        return ParentFeatureProviderResult(
            manifest=original.manifest,
            as_of=original.as_of,
            knowledge_cutoff=original.knowledge_cutoff,
            source=original.source,
            features=original.features,
            dependency_result_hashes=("wrong-dependency-hash",),
            metadata=original.metadata,
        )


class ParentContextDependencyOrchestratorTests(unittest.TestCase):
    def providers(self):
        market_source = FixtureSessionMarketProvider(
            rows(step=0.20), instrument="KOSPI", source="fixture://index/kospi"
        )
        sector_source = FixtureSessionMarketProvider(
            rows(base=80.0, step=0.32), instrument="SECTOR_SEMI", source="fixture://sector/semi"
        )
        market = market_provider(market_source)
        sector = sector_provider(sector_source, market)
        return market, sector, market_source, sector_source

    def test_explicit_market_to_sector_dag_precomputes_and_runs_through_backtest(self):
        market, sector, market_source, sector_source = self.providers()
        target = target_market()
        bundle = DependencyParentContextFrameBuilder.build(
            frame_id="PCTX2D_MARKET_SECTOR",
            target_market=target,
            nodes=(
                ParentProviderNode(provider=sector, depends_on=(market.manifest.provider_id,)),
                ParentProviderNode(provider=market),
            ),
            mode="DEPLOYMENT",
        )
        self.assertEqual(bundle.provider_order, (market.manifest.provider_id, sector.manifest.provider_id))
        self.assertEqual(
            bundle.dependency_edges,
            ((market.manifest.provider_id, sector.manifest.provider_id),),
        )
        self.assertEqual(len(market_source.calls), len(target["time"]))
        self.assertEqual(len(sector_source.calls), len(target["time"]))
        self.assertEqual(bundle.public_dict()["policy"], BUILD_POLICY)

        dsl = '''strategy "SectorCtx" {
            timeframe = "5m"
            long_entry = ctx.sector.semiconductor_relative_strength_long_pct > 0 and ctx.sector.semiconductor_market_alignment
            long_exit = false
            on(long_entry) { order.buy(type = "MARKET") }
        }'''
        result = BacktestEngine.run(
            dsl,
            market=target,
            parent_context_frame=bundle.frame,
            parent_feature_registry=bundle.registry,
        )
        self.assertEqual(result["metrics_numeric"]["trade_count"], 1)
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")

    def test_node_input_order_does_not_change_dag_identity(self):
        market_a, sector_a, _, _ = self.providers()
        first = DependencyParentContextFrameBuilder.build(
            frame_id="DAG_ORDER",
            target_market=target_market(),
            nodes=(ParentProviderNode(sector_a, (market_a.manifest.provider_id,)), ParentProviderNode(market_a)),
            mode="OBSERVED",
        )
        market_b, sector_b, _, _ = self.providers()
        second = DependencyParentContextFrameBuilder.build(
            frame_id="DAG_ORDER",
            target_market=target_market(),
            nodes=(ParentProviderNode(market_b), ParentProviderNode(sector_b, (market_b.manifest.provider_id,))),
            mode="OBSERVED",
        )
        self.assertEqual(first.registry.registry_hash, second.registry.registry_hash)
        self.assertEqual(first.frame.frame_hash, second.frame.frame_hash)
        self.assertEqual(first.build_hash, second.build_hash)

    def test_unknown_dependency_and_cycle_fail_closed(self):
        market, sector, _, _ = self.providers()
        with self.assertRaisesRegex(ValueError, "알려지지 않은"):
            DependencyParentContextFrameBuilder.build(
                frame_id="UNKNOWN_DEP",
                target_market=target_market(),
                nodes=(ParentProviderNode(market, ("missing-provider",)),),
            )
        with self.assertRaisesRegex(ValueError, "cycle"):
            DependencyParentContextFrameBuilder.build(
                frame_id="CYCLE",
                target_market=target_market(),
                nodes=(
                    ParentProviderNode(market, (sector.manifest.provider_id,)),
                    ParentProviderNode(sector, (market.manifest.provider_id,)),
                ),
            )

    def test_sector_provider_requires_exact_declared_market_dependency(self):
        market, sector, _, _ = self.providers()
        stamp = target_market()["time"][0]
        with self.assertRaisesRegex(ValueError, "MARKET dependency"):
            sector.build(as_of=stamp, knowledge_cutoff=stamp, dependencies=None)
        parent = market.build(as_of=stamp, knowledge_cutoff=stamp)
        with self.assertRaisesRegex(ValueError, "MARKET dependency"):
            sector.build(
                as_of=stamp,
                knowledge_cutoff=stamp,
                dependencies={"unexpected": parent},
            )

    def test_declared_dependency_hashes_must_match_exact_supplied_results(self):
        market, sector, _, _ = self.providers()
        bad_sector = WrongDependencyHashProvider(sector)
        with self.assertRaisesRegex(ValueError, "dependency_result_hashes"):
            DependencyParentContextFrameBuilder.build(
                frame_id="BAD_HASH",
                target_market=target_market(),
                nodes=(
                    ParentProviderNode(market),
                    ParentProviderNode(bad_sector, (market.manifest.provider_id,)),
                ),
            )

    def test_sector_manifest_is_descriptive_and_contains_no_execution_authority(self):
        market, sector, _, _ = self.providers()
        public_ids = {spec.feature_id for spec in sector.manifest.features}
        self.assertIn("sector.semiconductor_relative_strength_long_pct", public_ids)
        self.assertIn("sector.semiconductor_market_alignment", public_ids)
        joined = " ".join(public_ids).lower()
        for prohibited in ("allow", "permit", "block", "gate", "order", "allocation"):
            self.assertNotIn(prohibited, joined)
        self.assertEqual(sector.manifest.layer, "SECTOR")
        self.assertEqual(sector.market_dependency_provider_id, market.manifest.provider_id)


if __name__ == "__main__":
    unittest.main()
