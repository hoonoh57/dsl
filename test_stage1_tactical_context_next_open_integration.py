import ast
from pathlib import Path
import unittest

from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)
from core.tactical_context_attribution import ContextDeploymentPolicy, ContextSliceRule
from core.tactical_context_backtest_integration import ValidatedContextBacktestIntegration
from core.tactical_context_deployment_evidence import ValidatedContextDeploymentPolicyEvidence
from core.tactical_context_next_open_integration import (
    EXECUTION_AUTHORITY,
    GATE_AUTHORITY,
    INTEGRATION_POLICY,
    ValidatedContextNextOpenIntegration,
)
from core.tactical_discovery import TacticCandidate


FEATURE_ID = "group.semiconductor_favorable_breadth_rate"
TIMES = (
    "20260828090000",
    "20260828090500",
    "20260828091000",
    "20260828091500",
    "20260828092000",
)
DSL = '''strategy "CtxInt3" {
    timeframe = "5m"
    long_entry = close > open
    long_exit = close < open
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''
DEFERRED_DSL = '''strategy "CtxInt3Deferred" {
    timeframe = "5m"
    long_entry = close > open
    long_exit = close < open
    on(long_entry) { order.buy(type = "LIMIT", limit = close) }
    on(long_exit) { order.close_long() }
}'''
CANDIDATE = TacticCandidate(candidate_id="CTXINT3_CANDIDATE", dsl_code=DSL)
CANDIDATE.validate()
DEFERRED_CANDIDATE = TacticCandidate(candidate_id="CTXINT3_DEFERRED", dsl_code=DEFERRED_DSL)
DEFERRED_CANDIDATE.validate()
MANIFEST = ParentFeatureManifest(
    provider_id="fixture_group_ctxint3",
    provider_version="v1",
    layer="GROUP",
    context_id="SEMICONDUCTOR_GROUP",
    max_staleness_seconds=0,
    features=(ParentFeatureSpec(FEATURE_ID, "favorable_breadth_rate", "NUMBER"),),
    metadata={"publication_state": "VALIDATED_INPUT_FIXTURE", "operational_authority": False},
)
MANIFEST.validate()
REGISTRY = ParentFeatureRegistry(manifests=(MANIFEST,))
REGISTRY.validate()


def market(*, symbol="005930", times=TIMES):
    size = len(times)
    return {
        "time": list(times),
        "open": [100.0, 100.0, 102.0, 99.0, 99.0][:size],
        "high": [101.0, 102.0, 103.0, 100.0, 100.0][:size],
        "low": [99.0, 99.0, 99.0, 98.0, 98.0][:size],
        "close": [100.0, 101.0, 100.0, 99.0, 99.0][:size],
        "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0][:size],
        "_meta": {
            "source": "fixture://ctxint3/market",
            "timeframe": "5m",
            "instrument": symbol,
        },
    }


def frame(*, breadths=(0.8, 0.8, 0.2, 0.8, 0.8), symbol="005930"):
    assemblies = []
    for target_time, breadth in zip(TIMES, breadths):
        result = ParentFeatureProviderResult(
            manifest=MANIFEST,
            as_of=target_time,
            knowledge_cutoff=target_time,
            source="fixture://ctxint3/group",
            features={"favorable_breadth_rate": float(breadth)},
            metadata={"fixture": "CTXINT3"},
        )
        assemblies.append(
            ParentContextAssembler.assemble(
                as_of=target_time,
                knowledge_cutoff=target_time,
                results=(result,),
                mode="DEPLOYMENT",
                metadata={"fixture": "CTXINT3"},
            )
        )
    return ParentContextFrame.create(
        frame_id="CTXINT3_FRAME",
        target_symbol=symbol,
        registry=REGISTRY,
        assemblies=tuple(assemblies),
        mode="DEPLOYMENT",
        metadata={"fixture": "CTXINT3"},
    )


def policy_evidence(*, tactic_id=None):
    tactic = tactic_id or CANDIDATE.candidate_hash
    rule = ContextSliceRule(
        slice_id="GROUP_BREADTH_GTE_060",
        layer="GROUP",
        context_id="SEMICONDUCTOR_GROUP",
        feature_key="favorable_breadth_rate",
        operator="GTE",
        value=0.60,
        metadata={"source": "CTXVAL1_VALIDATED_FIXTURE"},
    )
    policy = ContextDeploymentPolicy(
        policy_id="SEMICONDUCTOR_BREADTH_POLICY",
        policy_version="v1",
        tactic_id=tactic,
        rule=rule,
        attribution_hash="train-attribution-hash",
        evidence_status="VALIDATED",
        validation_evidence_hash="ctxval1-validation-evidence-hash",
        priority_if_allowed=1.0,
    )
    evidence = ValidatedContextDeploymentPolicyEvidence(
        policy=policy,
        feature_id=FEATURE_ID,
        required_manifest_hash=MANIFEST.manifest_hash,
        validation_arena_hash="ctxval1-arena-hash",
        validation_evidence_hash="ctxval1-validation-evidence-hash",
        validation_contract_hash="ctxval1-contract-hash",
        partition_attribution_hashes=(
            ("TRAIN_GROUP", "train-attribution-hash"),
            ("VALIDATION_GROUP", "validation-attribution-hash"),
            ("OOS_GROUP", "oos-attribution-hash"),
            ("HARSH_GROUP", "harsh-attribution-hash"),
        ),
    )
    evidence.validate()
    return evidence


def run_ctxint3(*, breadths=(0.8, 0.8, 0.2, 0.8, 0.8), guards=(True, True, True, True, True), **overrides):
    arguments = {
        "candidate": CANDIDATE,
        "policy_evidence": policy_evidence(),
        "frame": frame(breadths=breadths),
        "registry": REGISTRY,
        "market": market(),
        "tactic_trigger": (False, True, False, False, False),
        "local_hard_guard_pass": guards,
        "settings": {"signal_mode": "next_open"},
    }
    arguments.update(overrides)
    return ValidatedContextNextOpenIntegration.run(**arguments)


class TacticalContextNextOpenIntegrationTests(unittest.TestCase):
    def test_prior_completed_signal_bar_permission_is_used_at_next_open(self):
        integrated = run_ctxint3(breadths=(0.8, 0.8, 0.2, 0.8, 0.8))
        trades = integrated["backtest"]["trades"]
        entries = [row for row in trades if row["kind"] == "ENTRY"]
        exits = [row for row in trades if row["kind"] == "EXIT"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(exits), 1)
        self.assertEqual(str(entries[0]["signal_time"]), TIMES[1])
        self.assertEqual(str(entries[0]["time"]), TIMES[2])
        self.assertEqual(str(exits[0]["signal_time"]), TIMES[2])
        self.assertEqual(str(exits[0]["time"]), TIMES[3])
        self.assertTrue(integrated["entry_gate"][2])
        self.assertEqual(integrated["gate_source_times"][2], TIMES[1])
        self.assertFalse(integrated["can_use_fill_bar_context_for_next_open"])

    def test_fill_bar_context_cannot_rescue_a_blocked_signal_bar(self):
        integrated = run_ctxint3(breadths=(0.8, 0.2, 0.8, 0.8, 0.8))
        self.assertEqual(integrated["backtest"]["metrics_numeric"]["trade_count"], 0)
        self.assertFalse(integrated["entry_gate"][2])
        self.assertEqual(integrated["gate_source_times"][2], TIMES[1])
        self.assertGreater(
            integrated["backtest"]["diagnostics"]["rejections"]["higher_layer_gate_blocked"],
            0,
        )

    def test_failed_signal_bar_local_guard_cannot_be_bypassed(self):
        integrated = run_ctxint3(
            breadths=(0.8, 0.8, 0.8, 0.8, 0.8),
            guards=(True, False, True, True, True),
        )
        self.assertEqual(integrated["backtest"]["metrics_numeric"]["trade_count"], 0)
        self.assertFalse(integrated["entry_gate"][2])
        self.assertFalse(integrated["can_bypass_local_hard_guard"])

    def test_first_bar_has_no_prior_authority_and_identity_is_deterministic(self):
        first = run_ctxint3()
        second = run_ctxint3()
        self.assertFalse(first["entry_gate"][0])
        self.assertIsNone(first["gate_source_times"][0])
        self.assertEqual(first["gate_hash"], second["gate_hash"])
        self.assertEqual(first["integration_policy"], INTEGRATION_POLICY)
        self.assertEqual(first["gate_authority"], GATE_AUTHORITY)
        self.assertEqual(first["execution_authority"], EXECUTION_AUTHORITY)
        self.assertFalse(first["broker_order_authority"])

    def test_candidate_symbol_timeline_and_signal_mode_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "candidate_hash"):
            run_ctxint3(policy_evidence=policy_evidence(tactic_id="other-candidate"))
        with self.assertRaisesRegex(ValueError, "instrument"):
            run_ctxint3(market=market(symbol="000660"))
        with self.assertRaisesRegex(ValueError, "timeline"):
            run_ctxint3(market=market(times=TIMES[:-1]))
        with self.assertRaisesRegex(ValueError, "next_open"):
            run_ctxint3(settings={"signal_mode": "bar_close"})

    def test_deferred_entry_orders_fail_closed_in_ctxint2_and_ctxint3(self):
        with self.assertRaisesRegex(ValueError, "MARKET"):
            ValidatedContextNextOpenIntegration.run(
                candidate=DEFERRED_CANDIDATE,
                policy_evidence=policy_evidence(),
                frame=frame(),
                registry=REGISTRY,
                market=market(),
                tactic_trigger=(False, True, False, False, False),
                local_hard_guard_pass=(True, True, True, True, True),
                settings={"signal_mode": "next_open"},
            )
        with self.assertRaisesRegex(ValueError, "MARKET"):
            ValidatedContextBacktestIntegration.run(
                candidate=DEFERRED_CANDIDATE,
                policy_evidence=policy_evidence(),
                frame=frame(),
                registry=REGISTRY,
                market=market(),
                tactic_trigger=(False, True, False, False, False),
                local_hard_guard_pass=(True, True, True, True, True),
                settings={"signal_mode": "bar_close"},
            )

    def test_next_open_module_uses_backtest_seam_without_direct_broker_runtime_or_provider_calls(self):
        source = Path("core/tactical_context_next_open_integration.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.add(node.module or "")
        self.assertIn("core.backtest", imported_modules)
        self.assertNotIn("core.broker", imported_modules)
        self.assertNotIn("core.dsl_runtime", imported_modules)
        self.assertNotIn("core.market_parent_feature_provider", imported_modules)
        self.assertNotIn("core.sector_parent_feature_provider", imported_modules)
        self.assertNotIn("core.group_evidence_parent_feature_provider", imported_modules)
        self.assertNotIn("provider.build(", source)
        self.assertNotIn("broker.submit(", source)


if __name__ == "__main__":
    unittest.main()
