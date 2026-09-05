import json
import unittest
from pathlib import Path
from unittest.mock import patch

from addons.strategy_manager.workspace import StrategyWorkspace, VALIDATION_SCHEMA


VALID_DSL = '''strategy "Example" {
    timeframe = "1d"
    enter = close > close[1]
    on(enter) { order.buy(type = "MARKET") }
}'''


class WysiwygStrategyWorkspaceTests(unittest.TestCase):
    def test_loaded_strategy_is_unvalidated_without_exact_matching_version(self):
        rows = [{"id": 7, "name": "Example", "description": "", "dsl_code": VALID_DSL}]
        with patch("addons.strategy_manager.workspace.db.get_all_strategies", return_value=rows), \
             patch("addons.strategy_manager.workspace.db.get_artifact_versions", return_value=[]):
            strategy = StrategyWorkspace.list_strategies()[0]
        self.assertFalse(strategy["current_validation"]["valid"])
        self.assertIsNone(strategy["current_validation"]["version"])

    def test_exact_validated_artifact_version_recovers_across_sessions(self):
        rows = [{"id": 7, "name": "Example", "description": "", "dsl_code": VALID_DSL}]
        import hashlib
        digest = hashlib.sha256(VALID_DSL.encode("utf-8")).hexdigest()
        versions = [{
            "version": 3,
            "dsl_code": VALID_DSL,
            "validation_json": json.dumps({
                "schema": VALIDATION_SCHEMA,
                "valid": True,
                "dsl_sha256": digest,
            }),
        }]
        with patch("addons.strategy_manager.workspace.db.get_all_strategies", return_value=rows), \
             patch("addons.strategy_manager.workspace.db.get_artifact_versions", return_value=versions):
            state = StrategyWorkspace.list_strategies()[0]["current_validation"]
        self.assertTrue(state["valid"])
        self.assertEqual(state["version"], 3)
        self.assertEqual(state["dsl_sha256"], digest)

    def test_changed_draft_invalidates_previous_validation_without_deleting_history(self):
        old = VALID_DSL
        changed = VALID_DSL.replace("close > close[1]", "close >= close[1]")
        import hashlib
        old_digest = hashlib.sha256(old.encode("utf-8")).hexdigest()
        rows = [{"id": 7, "name": "Example", "description": "", "dsl_code": changed}]
        versions = [{
            "version": 2,
            "dsl_code": old,
            "validation_json": json.dumps({
                "schema": VALIDATION_SCHEMA,
                "valid": True,
                "dsl_sha256": old_digest,
            }),
        }]
        with patch("addons.strategy_manager.workspace.db.get_all_strategies", return_value=rows), \
             patch("addons.strategy_manager.workspace.db.get_artifact_versions", return_value=versions):
            state = StrategyWorkspace.list_strategies()[0]["current_validation"]
        self.assertFalse(state["valid"])
        self.assertEqual(len(versions), 1)

    def test_draft_crud_delegates_create_update_delete_to_core_db_only(self):
        created = {"id": 11, "name": "Draft", "description": "d", "dsl_code": "incomplete"}
        with patch("addons.strategy_manager.workspace.db.insert_strategy", return_value=11) as insert, \
             patch.object(StrategyWorkspace, "get_strategy", return_value=created):
            result = StrategyWorkspace.save_draft(
                strategy_id=None, name="Draft", description="d", dsl_code="incomplete"
            )
        insert.assert_called_once_with("Draft", "d", "incomplete", "DSL", "incomplete")
        self.assertEqual(result["id"], 11)

        with patch("addons.strategy_manager.workspace.db.update_strategy") as update, \
             patch.object(StrategyWorkspace, "get_strategy", return_value=created):
            StrategyWorkspace.save_draft(
                strategy_id=11, name="Draft", description="d", dsl_code="incomplete"
            )
        update.assert_called_once_with(11, "Draft", "d", "incomplete", "DSL", "incomplete")

        with patch("addons.strategy_manager.workspace.db.delete_strategy") as delete:
            StrategyWorkspace.delete_strategy(11)
        delete.assert_called_once_with(11)

    def test_validation_uses_existing_backtest_engine_then_versions_exact_dsl(self):
        preview = {
            "strategy": {"name": "Example", "timeframe": "1d"},
            "indicators": [],
            "diagnostics": {"bars": 200, "execution_authority": "BrokerEmulator"},
        }
        saved = {
            "id": 19,
            "name": "Example",
            "dsl_code": VALID_DSL,
            "current_validation": {"valid": True, "version": 1},
        }
        categories = [{"id": 4, "name": "전략", "parent_id": None, "artifact_type": "strategy"}]
        with patch("addons.strategy_manager.workspace.BacktestEngine.run", return_value=preview) as run, \
             patch("addons.strategy_manager.workspace.db.get_categories", return_value=categories), \
             patch("addons.strategy_manager.workspace.db.commit_artifact", return_value=19) as commit, \
             patch("addons.strategy_manager.workspace.db.record_validation", return_value=31) as record, \
             patch.object(StrategyWorkspace, "get_strategy", return_value=saved):
            result = StrategyWorkspace.validate_and_commit(
                strategy_id=None,
                name="Example",
                description="desc",
                dsl_code=VALID_DSL,
            )
        run.assert_called_once()
        run_args, run_kwargs = run.call_args
        self.assertEqual(run_args, (VALID_DSL,))
        validation_market = run_kwargs["market"]
        self.assertEqual(validation_market["_meta"]["source"], "strategy_validation_fixture")
        self.assertNotIn("timeframe", validation_market["_meta"])
        commit_kwargs = commit.call_args.kwargs
        self.assertEqual(commit_kwargs["dsl_code"], VALID_DSL)
        self.assertEqual(commit_kwargs["source_code"], VALID_DSL)
        validation = json.loads(commit_kwargs["validation_json"])
        self.assertEqual(validation["schema"], VALIDATION_SCHEMA)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["execution_authority"], "BrokerEmulator")
        record.assert_called_once()
        self.assertEqual(result["validation_event_id"], 31)

    def test_invalid_dsl_never_reaches_commit_authority(self):
        with patch("addons.strategy_manager.workspace.BacktestEngine.run", side_effect=ValueError("bad DSL")), \
             patch("addons.strategy_manager.workspace.db.commit_artifact") as commit:
            with self.assertRaisesRegex(ValueError, "bad DSL"):
                StrategyWorkspace.validate_and_commit(
                    strategy_id=None,
                    name="Broken",
                    description="",
                    dsl_code="strategy broken",
                )
        commit.assert_not_called()

    def test_addon_does_not_own_sqlite_or_parallel_dsl_engine(self):
        source = (Path(__file__).parent / "addons" / "strategy_manager" / "workspace.py").read_text(encoding="utf-8")
        self.assertNotIn("import sqlite3", source)
        self.assertNotIn("StrategyEngine", source)
        self.assertIn("BacktestEngine.run", source)
        self.assertIn("from core import db", source)


if __name__ == "__main__":
    unittest.main()
