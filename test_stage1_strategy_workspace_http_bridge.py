from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from addons.strategy_manager import http_bridge
from addons.strategy_manager.http_bridge import StrategyWorkspaceRequest


class StrategyWorkspaceHttpBridgeTests(unittest.TestCase):
    def test_routes_are_bounded_to_strategy_workspace_contract(self):
        routes = {(route.path, tuple(sorted(route.methods or []))) for route in http_bridge.router.routes}
        self.assertIn(("/api/strategy-workspace/strategies", ("GET",)), routes)
        self.assertIn(("/api/strategy-workspace/draft", ("POST",)), routes)
        self.assertIn(("/api/strategy-workspace/strategies/{strategy_id}", ("DELETE",)), routes)
        self.assertIn(("/api/strategy-workspace/validate-commit", ("POST",)), routes)

    def test_save_draft_delegates_exact_values_to_workspace(self):
        request = StrategyWorkspaceRequest(
            strategy_id=7,
            name="A",
            description="desc",
            dsl_code='strategy "A" { long_entry = false }',
        )
        expected = {"id": 7, "name": "A"}
        with patch.object(http_bridge.StrategyWorkspace, "save_draft", return_value=expected) as save:
            self.assertEqual(http_bridge.save_draft(request), expected)
        save.assert_called_once_with(
            strategy_id=7,
            name="A",
            description="desc",
            dsl_code='strategy "A" { long_entry = false }',
        )

    def test_validate_commit_delegates_to_authoritative_workspace(self):
        request = StrategyWorkspaceRequest(
            strategy_id=None,
            name="B",
            description="",
            dsl_code='strategy "B" { long_entry = false }',
        )
        expected = {"strategy": {"id": 9}, "validation": {"valid": True}}
        with patch.object(http_bridge.StrategyWorkspace, "validate_and_commit", return_value=expected) as validate:
            self.assertEqual(http_bridge.validate_and_commit(request), expected)
        validate.assert_called_once_with(
            strategy_id=None,
            name="B",
            description="",
            dsl_code='strategy "B" { long_entry = false }',
        )

    def test_delete_delegates_only_to_workspace(self):
        with patch.object(http_bridge.StrategyWorkspace, "delete_strategy") as delete:
            self.assertEqual(http_bridge.delete_strategy(11), {"deleted": 11})
        delete.assert_called_once_with(11)

    def test_domain_errors_fail_closed_as_http_errors(self):
        request = StrategyWorkspaceRequest(name="", description="", dsl_code="")
        with patch.object(http_bridge.StrategyWorkspace, "save_draft", side_effect=ValueError("invalid draft")):
            with self.assertRaises(HTTPException) as caught:
                http_bridge.save_draft(request)
        self.assertEqual(caught.exception.status_code, 422)
        self.assertIn("invalid draft", str(caught.exception.detail))

    def test_http_adapter_has_no_parallel_db_or_backtest_authority(self):
        source = inspect.getsource(http_bridge)
        self.assertNotIn("from core import db", source)
        self.assertNotIn("from core.backtest import BacktestEngine", source)
        self.assertNotIn("sqlite3", source)
        self.assertIn("StrategyWorkspace", source)


if __name__ == "__main__":
    unittest.main()
