import unittest
from pathlib import Path

from core.group_evidence_parent_feature_provider import (
    CALCULATION_POLICY,
    PUBLICATION_STATE,
    GroupEvidenceParentFeatureProvider,
    ImmutableGroupEvidenceTimeline,
)
from core.multi_symbol_group_evidence import (
    GroupEvidencePolicy,
    GroupSnapshotPoint,
    MultiSymbolGroupEvidenceAnalyzer,
)
from core.multi_symbol_snapshot import InstrumentSignalSnapshot, SnapshotUniverse
from core.parent_context_dependency_orchestrator import (
    DependencyParentContextFrameBuilder,
    ParentProviderNode,
)
from core.parent_context_frame import ParentContextBinder
from core.parent_feature_provider import (
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureSpec,
)


TIMES = (
    "20260827100500",
    "20260827101000",
    "20260827101500",
    "20260827102000",
)
SYMBOLS = ("A", "B", "C")
SOURCE_AUTHORITY = "FIXTURE_STATIC_GROUP"


def snapshot(symbol, as_of, value, *, trigger=True):
    return InstrumentSignalSnapshot(
        symbol=symbol,
        as_of=as_of,
        knowledge_cutoff=as_of,
        candidate_hash=f"candidate-{symbol}",
        family_id="JMA_TREND_CROSS_RESUME_V1",
        generation_hash="generation-trusted",
        tactic_trigger=trigger,
        hard_guards_pass=True,
        locally_admissible=True,
        comparison_metrics={"setup_quality": value},
        source="fixture://msa3/signal",
        evidence_hash=f"evidence-{symbol}-{as_of}",
    )


def point(as_of, values, *, triggers=None):
    triggers = triggers or {}
    return GroupSnapshotPoint(
        universe=SnapshotUniverse(
            universe_id="SEMICONDUCTOR_GROUP",
            symbols=SYMBOLS,
            as_of=as_of,
            knowledge_cutoff=as_of,
            source_authority=SOURCE_AUTHORITY,
        ),
        snapshots=tuple(
            snapshot(
                symbol,
                as_of,
                values[symbol],
                trigger=triggers.get(symbol, True),
            )
            for symbol in SYMBOLS
        ),
    )


def evidence_fixture():
    policy = GroupEvidencePolicy(
        policy_id="SEMICONDUCTOR_GROUP_SETUP",
        policy_version="v1",
        metric_id="setup_quality",
        direction="MAX",
        favorable_threshold=0.5,
        leader_count=1,
        lookback_points=3,
        max_symbols=8,
        max_points=8,
    )
    p1 = point(TIMES[0], {"A": 0.8, "B": 0.6, "C": 0.2})
    p2 = point(TIMES[1], {"A": 0.9, "B": 0.7, "C": 0.1})
    p3 = point(TIMES[2], {"A": 0.8, "B": 0.95, "C": 0.4})
    p4 = point(
        TIMES[3],
        {"A": 0.85, "B": 0.7, "C": 0.3},
        triggers={"B": False, "C": False},
    )
    e1010 = MultiSymbolGroupEvidenceAnalyzer.analyze(points=(p1, p2), policy=policy)
    e1015 = MultiSymbolGroupEvidenceAnalyzer.analyze(points=(p1, p2, p3), policy=policy)
    e1020 = MultiSymbolGroupEvidenceAnalyzer.analyze(points=(p1, p2, p3, p4), policy=policy)
    return policy, (e1010, e1015, e1020)


def sector_manifest(provider_id="fixture_sector", *, layer="SECTOR"):
    prefix = layer.lower()
    return ParentFeatureManifest(
        provider_id=provider_id,
        provider_version="v1",
        layer=layer,
        context_id=f"{layer}_FIXTURE",
        max_staleness_seconds=0,
        features=(ParentFeatureSpec(f"{prefix}.fixture_value", "value", "NUMBER"),),
    )


def sector_result(as_of, *, provider_id="fixture_sector", layer="SECTOR"):
    manifest = sector_manifest(provider_id=provider_id, layer=layer)
    return ParentFeatureProviderResult(
        manifest=manifest,
        as_of=as_of,
        knowledge_cutoff=as_of,
        source="fixture://sector",
        features={"value": 1.0},
    )


def group_provider(timeline=None, *, policy=None, policy_hash=None):
    policy, evidence = evidence_fixture() if policy is None else (policy, None)
    if timeline is None:
        if evidence is None:
            _, evidence = evidence_fixture()
        timeline = ImmutableGroupEvidenceTimeline(tuple(evidence))
    return GroupEvidenceParentFeatureProvider(
        timeline,
        group_namespace="semiconductor",
        universe_id="SEMICONDUCTOR_GROUP",
        evidence_source_authority=SOURCE_AUTHORITY,
        msa2_policy_hash=policy_hash or policy.policy_hash,
        metric_id="setup_quality",
        sector_dependency_provider_id="fixture_sector",
    )


class FixtureMarketProvider:
    def __init__(self):
        self._manifest = ParentFeatureManifest(
            provider_id="fixture_market",
            provider_version="v1",
            layer="MARKET",
            context_id="MARKET_FIXTURE",
            max_staleness_seconds=0,
            features=(ParentFeatureSpec("market.fixture_value", "value", "NUMBER"),),
        )

    @property
    def manifest(self):
        return self._manifest

    def build(self, *, as_of, knowledge_cutoff, dependencies=None):
        if as_of != knowledge_cutoff or dependencies:
            raise ValueError("fixture MARKET exact root only")
        return ParentFeatureProviderResult(
            manifest=self.manifest,
            as_of=as_of,
            knowledge_cutoff=knowledge_cutoff,
            source="fixture://market",
            features={"value": 1.0},
        )


class FixtureSectorProvider:
    def __init__(self):
        self._manifest = sector_manifest()

    @property
    def manifest(self):
        return self._manifest

    def build(self, *, as_of, knowledge_cutoff, dependencies=None):
        if as_of != knowledge_cutoff or not dependencies or set(dependencies) != {"fixture_market"}:
            raise ValueError("fixture SECTOR requires exact MARKET")
        market = dependencies["fixture_market"]
        return ParentFeatureProviderResult(
            manifest=self.manifest,
            as_of=as_of,
            knowledge_cutoff=knowledge_cutoff,
            source="fixture://sector",
            features={"value": 2.0},
            dependency_result_hashes=(market.result_hash,),
        )


class GroupEvidenceParentFeatureProviderTests(unittest.TestCase):
    def test_manifest_is_small_descriptive_research_only_and_hides_peer_identity(self):
        provider = group_provider()
        manifest = provider.manifest.public_dict()
        feature_ids = [item["feature_id"] for item in manifest["features"]]

        self.assertEqual(manifest["layer"], "GROUP")
        self.assertEqual(manifest["metadata"]["publication_state"], PUBLICATION_STATE)
        self.assertFalse(manifest["metadata"]["operational_authority"])
        self.assertFalse(manifest["metadata"]["publishes_peer_symbol_identities"])
        self.assertEqual(manifest["metadata"]["calculation_policy"], CALCULATION_POLICY)
        self.assertEqual(len(feature_ids), 5)
        self.assertTrue(all(item.startswith("group.semiconductor_") for item in feature_ids))
        joined = " ".join(feature_ids).lower()
        for forbidden in ("symbol", "allowed", "blocked", "allocation", "slot", "order", "gate"):
            self.assertNotIn(forbidden, joined)

    def test_exact_msa2_evidence_publishes_aggregate_features_with_sector_hash(self):
        provider = group_provider()
        parent = sector_result(TIMES[2])
        result = provider.build(
            as_of=TIMES[2],
            knowledge_cutoff=TIMES[2],
            dependencies={"fixture_sector": parent},
        )

        self.assertEqual(result.manifest.layer, "GROUP")
        self.assertEqual(result.dependency_result_hashes, (parent.result_hash,))
        self.assertEqual(result.metadata["publication_state"], PUBLICATION_STATE)
        self.assertFalse(result.metadata["operational_authority"])
        self.assertIn("comparison_eligible_rate", result.features)
        self.assertIn("favorable_breadth_rate", result.features)
        self.assertIn("leader_persistence_rate", result.features)
        self.assertIn("leader_follower_spread", result.features)
        self.assertIn("follower_favorable_rate", result.features)
        self.assertNotIn("leader_symbols", result.features)

    def test_follower_collapse_preserves_optional_absence_instead_of_zero(self):
        provider = group_provider()
        parent = sector_result(TIMES[3])
        result = provider.build(
            as_of=TIMES[3],
            knowledge_cutoff=TIMES[3],
            dependencies={"fixture_sector": parent},
        )

        self.assertNotIn("leader_follower_spread", result.features)
        self.assertNotIn("follower_favorable_rate", result.features)
        optional = {
            item.feature_key: item
            for item in result.manifest.features
            if not item.required
        }
        self.assertEqual(optional["leader_follower_spread"].missing_policy, "OPTIONAL_ABSENT")
        self.assertEqual(optional["follower_favorable_rate"].missing_policy, "OPTIONAL_ABSENT")

    def test_exact_time_policy_universe_and_dependency_mismatches_fail_closed(self):
        policy, evidence = evidence_fixture()
        timeline = ImmutableGroupEvidenceTimeline(tuple(evidence))
        provider = group_provider(timeline=timeline, policy=policy)

        with self.assertRaisesRegex(ValueError, "exact target"):
            provider.build(
                as_of="20260827101200",
                knowledge_cutoff="20260827101200",
                dependencies={"fixture_sector": sector_result("20260827101200")},
            )

        wrong_policy = group_provider(timeline=timeline, policy=policy, policy_hash="wrong-policy")
        with self.assertRaisesRegex(ValueError, "policy_hash"):
            wrong_policy.build(
                as_of=TIMES[2],
                knowledge_cutoff=TIMES[2],
                dependencies={"fixture_sector": sector_result(TIMES[2])},
            )

        with self.assertRaisesRegex(ValueError, "SECTOR dependency"):
            provider.build(
                as_of=TIMES[2],
                knowledge_cutoff=TIMES[2],
                dependencies={
                    "fixture_sector": sector_result(TIMES[2]),
                    "extra": sector_result(TIMES[2], provider_id="extra"),
                },
            )

        with self.assertRaisesRegex(ValueError, "layer"):
            provider.build(
                as_of=TIMES[2],
                knowledge_cutoff=TIMES[2],
                dependencies={"fixture_sector": sector_result(TIMES[2], layer="MARKET")},
            )

    def test_tampered_msa2_payload_is_rejected_by_result_hash_validation(self):
        _, evidence = evidence_fixture()
        tampered = dict(evidence[1])
        tampered_latest = dict(tampered["latest"])
        tampered_latest["favorable_breadth_rate"] = 0.123
        tampered["latest"] = tampered_latest
        timeline = ImmutableGroupEvidenceTimeline((evidence[0], tampered))
        with self.assertRaisesRegex(ValueError, "result_hash"):
            timeline.validate()

    def test_pctx2d_observed_dag_publishes_registered_group_feature_exactly(self):
        policy, evidence = evidence_fixture()
        timeline = ImmutableGroupEvidenceTimeline((evidence[0], evidence[1]))
        group = group_provider(timeline=timeline, policy=policy)
        market = FixtureMarketProvider()
        sector = FixtureSectorProvider()
        target_market = {
            "time": [TIMES[1], TIMES[2]],
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [1000.0, 1100.0],
            "_meta": {
                "instrument": "TARGET",
                "timeframe": "5m",
                "source": "fixture://target",
            },
        }
        bundle = DependencyParentContextFrameBuilder.build(
            frame_id="msa3-observed",
            target_market=target_market,
            nodes=(
                ParentProviderNode(market),
                ParentProviderNode(sector, depends_on=("fixture_market",)),
                ParentProviderNode(group, depends_on=("fixture_sector",)),
            ),
            mode="OBSERVED",
        )

        feature_id = "group.semiconductor_favorable_breadth_rate"
        resolved = bundle.registry.resolve(feature_id)
        self.assertEqual(resolved["manifest"]["layer"], "GROUP")
        binding = ParentContextBinder.bind(
            frame=bundle.frame,
            registry=bundle.registry,
            target_time=TIMES[2],
            feature_ids=(feature_id, "group.semiconductor_leader_follower_spread"),
        )
        values = {item.feature_id: item for item in binding.values}
        self.assertTrue(values[feature_id].present)
        self.assertTrue(values["group.semiconductor_leader_follower_spread"].present)
        self.assertEqual(bundle.mode, "OBSERVED")

    def test_provider_module_does_not_call_analysis_execution_or_peer_runtime(self):
        source = Path("core/group_evidence_parent_feature_provider.py").read_text(encoding="utf-8")
        for forbidden in (
            "MultiSymbolGroupEvidenceAnalyzer",
            "MultiSymbolSnapshotAnalyzer",
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "provider.load_session",
            "allowed_symbols",
            "blocked_symbols",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
