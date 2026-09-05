from __future__ import annotations

import unittest


class StrategyWorkspaceProductionMountTests(unittest.TestCase):
    def test_main_app_mounts_strategy_workspace_router(self):
        from main import app

        paths = app.openapi().get("paths", {})
        self.assertIn("/api/strategy-workspace/strategies", paths)
        self.assertIn("get", paths["/api/strategy-workspace/strategies"])
        self.assertIn("/api/strategy-workspace/draft", paths)
        self.assertIn("post", paths["/api/strategy-workspace/draft"])
        self.assertIn("/api/strategy-workspace/strategies/{strategy_id}", paths)
        self.assertIn("delete", paths["/api/strategy-workspace/strategies/{strategy_id}"])
        self.assertIn("/api/strategy-workspace/validate-commit", paths)
        self.assertIn("post", paths["/api/strategy-workspace/validate-commit"])

    def test_production_mount_reuses_strategy_workspace_router(self):
        import main
        from addons.strategy_manager.http_bridge import router

        mounted_paths = set(main.app.openapi().get("paths", {}))
        adapter_paths = {route.path for route in router.routes if getattr(route, "path", None)}
        self.assertTrue(adapter_paths)
        self.assertTrue(adapter_paths.issubset(mounted_paths))


if __name__ == "__main__":
    unittest.main()
