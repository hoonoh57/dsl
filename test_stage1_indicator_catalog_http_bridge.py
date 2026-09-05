from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from addons.indicator_catalog import http_bridge


class IndicatorCatalogHttpBridgeTests(unittest.TestCase):
    def test_routes_are_read_only_and_bounded(self):
        methods_by_path = {
            route.path: set(route.methods or set())
            for route in http_bridge.router.routes
            if getattr(route, "path", None)
        }
        self.assertEqual(
            methods_by_path,
            {
                "/api/indicator-catalog": {"GET"},
                "/api/indicator-catalog/{indicator_id}": {"GET"},
            },
        )

    def test_catalog_endpoint_delegates_to_authoritative_core_catalog(self):
        expected = {"schema": "test", "indicators": []}
        with patch.object(http_bridge, "indicator_catalog_payload", return_value=expected) as catalog:
            self.assertIs(http_bridge.read_indicator_catalog(), expected)
        catalog.assert_called_once_with()

    def test_indicator_endpoint_projects_authoritative_spec(self):
        class StubSpec:
            def public_dict(self):
                return {"id": "jma"}

        with patch.object(http_bridge, "get_indicator_spec", return_value=StubSpec()) as getter:
            self.assertEqual(http_bridge.read_indicator("JMA"), {"id": "jma"})
        getter.assert_called_once_with("JMA")

    def test_unknown_indicator_is_http_404(self):
        with patch.object(http_bridge, "get_indicator_spec", side_effect=KeyError("missing")):
            with self.assertRaises(HTTPException) as ctx:
                http_bridge.read_indicator("missing")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_bridge_has_no_parallel_semantic_or_persistence_authority(self):
        source = inspect.getsource(http_bridge)
        forbidden = (
            "CoreTALib",
            "BacktestEngine",
            "core.db",
            "sqlite",
            "pymysql",
            "MultiTimeframeContext",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
