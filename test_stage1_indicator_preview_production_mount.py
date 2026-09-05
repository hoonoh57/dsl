from __future__ import annotations

import unittest


class IndicatorPreviewProductionMountTests(unittest.TestCase):
    def test_main_app_mounts_indicator_preview_post_route(self):
        from main import app

        paths = app.openapi().get("paths", {})
        self.assertIn("/api/indicator-preview", paths)
        self.assertEqual(set(paths["/api/indicator-preview"]), {"post"})

    def test_production_mount_reuses_indicator_preview_router(self):
        import main
        from addons.indicator_preview.http_bridge import router

        mounted_paths = set(main.app.openapi().get("paths", {}))
        adapter_paths = {route.path for route in router.routes if getattr(route, "path", None)}
        self.assertEqual(adapter_paths, {"/api/indicator-preview"})
        self.assertTrue(adapter_paths.issubset(mounted_paths))


if __name__ == "__main__":
    unittest.main()
