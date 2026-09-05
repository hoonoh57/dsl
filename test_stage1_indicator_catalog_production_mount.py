from __future__ import annotations

import unittest


class IndicatorCatalogProductionMountTests(unittest.TestCase):
    def test_main_app_mounts_read_only_indicator_catalog(self):
        from main import app

        paths = app.openapi().get("paths", {})
        self.assertIn("/api/indicator-catalog", paths)
        self.assertEqual(set(paths["/api/indicator-catalog"]), {"get"})
        self.assertIn("/api/indicator-catalog/{indicator_id}", paths)
        self.assertEqual(set(paths["/api/indicator-catalog/{indicator_id}"]), {"get"})

    def test_production_mount_reuses_indicator_catalog_router(self):
        import main
        from addons.indicator_catalog.http_bridge import router

        mounted_paths = set(main.app.openapi().get("paths", {}))
        adapter_paths = {route.path for route in router.routes if getattr(route, "path", None)}
        self.assertTrue(adapter_paths)
        self.assertTrue(adapter_paths.issubset(mounted_paths))


if __name__ == "__main__":
    unittest.main()
