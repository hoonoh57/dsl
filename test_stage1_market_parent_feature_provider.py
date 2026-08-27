import copy
import unittest
from datetime import datetime, timedelta

from core.market_parent_feature_provider import (
    CALCULATION_POLICY,
    KrxBenchmarkMarketParentFeatureProvider,
    MarketParentFeatureConfig,
)
from core.parent_context_frame import ParentContextBinder, ParentContextFrame
from core.parent_feature_provider import ParentContextAssembler, ParentFeatureRegistry


def bars(count=42):
    start = datetime(2026, 8, 27, 9, 0, 0)
    rows = []
    for index in range(count):
        timestamp = (start + timedelta(minutes=5 * index)).strftime("%Y%m%d%H%M%S")
        close = 100.0 + index * 0.35 + (0.08 if index % 3 == 0 else -0.03)
        rows.append(
            {
                "time": timestamp,
                "open": close - 0.10,
                "high": close + 0.45,
                "low": close - 0.40,
                "close": close,
                "volume": 1000.0 + index * 17.0,
            }
        )
    return rows


class FixtureSessionMarketProvider:
    def __init__(self, rows, *, source="fixture://krx/kospi", instrument="KOSPI", timeframe="5m", mode="normal"):
        self.rows = copy.deepcopy(rows)
        self.source = source
        self.instrument = instrument
        self.timeframe = timeframe
        self.mode = mode
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
        selected = [row for row in self.rows if row["time"] <= cutoff]
        selected = selected[-required_bars:]
        if self.mode == "future" and self.rows:
            future = next((row for row in self.rows if row["time"] > cutoff), None)
            if future is not None:
                selected = selected[1:] + [future]
        elif self.mode == "stale" and len(selected) > 1:
            selected = selected[:-1]
        market = {key: [row[key] for row in selected] for key in ("time", "open", "high", "low", "close", "volume")}
        market["_meta"] = {
            "source": self.source,
            "instrument": self.instrument,
            "timeframe": self.timeframe,
        }
        return market


def provider(source, *, config=None, namespace="kospi", instrument="KOSPI"):
    return KrxBenchmarkMarketParentFeatureProvider(
        source,
        benchmark_symbol=instrument,
        feature_namespace=namespace,
        source_authority="KRX_INDEX_FIXTURE",
        config=config,
    )


class MarketParentFeatureProviderTests(unittest.TestCase):
    def setUp(self):
        self.rows = bars()
        self.target = self.rows[32]["time"]

    def test_manifest_is_explicit_typed_and_descriptive_only(self):
        item = provider(FixtureSessionMarketProvider(self.rows))
        public = item.manifest.public_dict()
        self.assertEqual(public["layer"], "MARKET")
        self.assertEqual(public["context_id"], "KOSPI_BENCHMARK")
        self.assertEqual(public["max_staleness_seconds"], 0)
        self.assertEqual(public["metadata"]["calculation_policy"], CALCULATION_POLICY)
        ids = {feature["feature_id"] for feature in public["features"]}
        self.assertEqual(
            ids,
            {
                "market.kospi_return_short_pct",
                "market.kospi_return_long_pct",
                "market.kospi_sma_slope_pct",
                "market.kospi_price_to_sma_pct",
                "market.kospi_atr_pct",
                "market.kospi_volume_ratio",
                "market.kospi_regime_state",
            },
        )
        self.assertFalse(any("allow" in value or "permit" in value or "gate" in value for value in ids))

    def test_same_exact_prefix_produces_same_features_and_result_hash(self):
        first_source = FixtureSessionMarketProvider(self.rows)
        second_rows = copy.deepcopy(self.rows)
        for row in second_rows:
            if row["time"] > self.target:
                row["close"] += 10000.0
                row["open"] += 10000.0
                row["high"] += 10000.0
                row["low"] += 10000.0
                row["volume"] += 999999.0
        second_source = FixtureSessionMarketProvider(second_rows)

        first = provider(first_source).build(as_of=self.target, knowledge_cutoff=self.target)
        second = provider(second_source).build(as_of=self.target, knowledge_cutoff=self.target)
        self.assertEqual(first.features, second.features)
        self.assertEqual(first.metadata["source_prefix_hash"], second.metadata["source_prefix_hash"])
        self.assertEqual(first.result_hash, second.result_hash)
        self.assertEqual(first.metadata["source_end"], self.target)
        self.assertEqual(first.features["regime_state"], "UPTREND")

    def test_changing_causal_prefix_changes_result_identity(self):
        first = provider(FixtureSessionMarketProvider(self.rows)).build(
            as_of=self.target,
            knowledge_cutoff=self.target,
        )
        changed = copy.deepcopy(self.rows)
        changed[31]["close"] += 2.0
        changed[31]["high"] = max(changed[31]["high"], changed[31]["close"] + 0.2)
        changed[31]["open"] = min(changed[31]["open"], changed[31]["close"] - 0.1)
        second = provider(FixtureSessionMarketProvider(changed)).build(
            as_of=self.target,
            knowledge_cutoff=self.target,
        )
        self.assertNotEqual(first.metadata["source_prefix_hash"], second.metadata["source_prefix_hash"])
        self.assertNotEqual(first.result_hash, second.result_hash)

    def test_future_or_stale_source_and_identity_mismatch_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "미래 bar"):
            provider(FixtureSessionMarketProvider(self.rows, mode="future")).build(
                as_of=self.target,
                knowledge_cutoff=self.target,
            )
        with self.assertRaisesRegex(ValueError, "exact as_of"):
            provider(FixtureSessionMarketProvider(self.rows, mode="stale")).build(
                as_of=self.target,
                knowledge_cutoff=self.target,
            )
        with self.assertRaisesRegex(ValueError, "instrument"):
            provider(FixtureSessionMarketProvider(self.rows, instrument="WRONG")).build(
                as_of=self.target,
                knowledge_cutoff=self.target,
            )
        with self.assertRaisesRegex(ValueError, "timeframe"):
            provider(FixtureSessionMarketProvider(self.rows, timeframe="1m")).build(
                as_of=self.target,
                knowledge_cutoff=self.target,
            )
        with self.assertRaisesRegex(ValueError, "source metadata"):
            provider(FixtureSessionMarketProvider(self.rows, source="")).build(
                as_of=self.target,
                knowledge_cutoff=self.target,
            )

    def test_root_provider_requires_exact_cutoff_and_rejects_dependencies(self):
        item = provider(FixtureSessionMarketProvider(self.rows))
        with self.assertRaisesRegex(ValueError, "as_of == knowledge_cutoff"):
            item.build(as_of=self.target, knowledge_cutoff=self.rows[33]["time"])
        with self.assertRaisesRegex(ValueError, "dependencies"):
            item.build(as_of=self.target, knowledge_cutoff=self.target, dependencies={"parent": object()})

    def test_config_and_history_requirements_are_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "short_return_bars"):
            MarketParentFeatureConfig(short_return_bars=12, long_return_bars=12).validate()
        config = MarketParentFeatureConfig(
            short_return_bars=2,
            long_return_bars=5,
            sma_period=8,
            slope_bars=2,
            atr_period=5,
            volume_period=7,
        )
        source = FixtureSessionMarketProvider(self.rows[:6])
        target = self.rows[5]["time"]
        with self.assertRaisesRegex(ValueError, "history"):
            provider(source, config=config).build(as_of=target, knowledge_cutoff=target)

    def test_provider_result_flows_through_pctx1_and_pctx2b_exact_frame(self):
        source = FixtureSessionMarketProvider(self.rows)
        item = provider(source)
        times = (self.rows[31]["time"], self.rows[32]["time"])
        assemblies = []
        for timestamp in times:
            result = item.build(as_of=timestamp, knowledge_cutoff=timestamp)
            assemblies.append(
                ParentContextAssembler.assemble(
                    as_of=timestamp,
                    knowledge_cutoff=timestamp,
                    results=(result,),
                    mode="DEPLOYMENT",
                )
            )
        registry = ParentFeatureRegistry((item.manifest,))
        context_frame = ParentContextFrame.create(
            frame_id="PCTX2A_MARKET_FIXTURE",
            target_symbol="005930",
            registry=registry,
            assemblies=tuple(assemblies),
            mode="DEPLOYMENT",
        )
        bound = ParentContextBinder.bind(
            frame=context_frame,
            registry=registry,
            target_time=times[-1],
            feature_ids=("market.kospi_regime_state", "market.kospi_sma_slope_pct"),
        )
        values = {entry.feature_id: entry.value for entry in bound.values}
        self.assertEqual(values["market.kospi_regime_state"], "UPTREND")
        self.assertGreater(values["market.kospi_sma_slope_pct"], 0.0)
        self.assertEqual(context_frame.resolve_exact(times[-1]).as_of, times[-1])


if __name__ == "__main__":
    unittest.main()
