from __future__ import annotations

import unittest


def _path_routes(routes):
    return [route for route in routes if isinstance(getattr(route, "path", None), str)]


class StrategyWorkspaceProductionMountTests(unittest.TestCase):
    def test_main_app_mounts_strategy_workspace_router(self):
        from main import app

        by_path = {
            route.path: set(getattr(route, "methods", set()) or set())
            for route in _path_routes(app.routes)
        }
        self.assertIn("/api/strategy-workspace/strategies", by_path)
        self.assertIn("GET", by_path["/api/strategy-workspace/strategies"])
        self.assertIn("/api/strategy-workspace/draft", by_path)
        self.assertIn("POST", by_path["/api/strategy-workspace/draft"])
        self.assertIn("/api/strategy-workspace/strategies/{strategy_id}", by_path)
        self.assertIn("DELETE", by_path["/api/strategy-workspace/strategies/{strategy_id}"])
        self.assertIn("/api/strategy-workspace/validate-commit", by_path)
        self.assertIn("POST", by_path["/api/strategy-workspace/validate-commit"])

    def test_production_mount_reuses_strategy_workspace_router(self):
        import main
        from addons.strategy_manager.http_bridge import router

        mounted_paths = {route.path for route in _path_routes(main.app.routes)}
        adapter_paths = {route.path for route in _path_routes(router.routes)}
        self.assertTrue(adapter_paths)
        self.assertTrue(adapter_paths.issubset(mounted_paths))


if __name__ == "__main__":
    unittest.main()
