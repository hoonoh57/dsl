from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from addons.indicator_preview import http_bridge


class IndicatorPreviewHttpBridgeTests(unittest.TestCase):
    def request(self):
        return http_bridge.IndicatorPreviewRequest(
            indicator_id="jma",
            parameters={"length": 7, "phase": 0, "power": 2},
            timeframe="5m",
            bars=[
                {"time": 1, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
                {"time": 2, "open": 1.5, "high": 2.5, "low": 1, "close": 2, "volume": 120},
            ],
        )

    def test_route_is_single_post_boundary(self):
        methods_by_path = {
            route.path: set(route.methods or set())
            for route in http_bridge.router.routes
            if getattr(route, "path", None)
        }
        self.assertEqual(methods_by_path, {"/api/indicator-preview": {"POST"}})

    def test_preview_delegates_exact_transport_values_to_authoritative_evaluator(self):
        request = self.request()
        expected = {"schema": "preview", "points": []}
        with patch.object(http_bridge, "evaluate_indicator", return_value=expected) as evaluator:
            self.assertIs(http_bridge.preview_indicator(request), expected)
        evaluator.assert_called_once_with(
            "jma",
            parameters={"length": 7, "phase": 0, "power": 2},
            timeframe="5m",
            bars=request.bars,
        )

    def test_unknown_indicator_and_contract_errors_fail_closed(self):
        request = self.request()
        with patch.object(http_bridge, "evaluate_indicator", side_effect=KeyError("missing")):
            with self.assertRaises(HTTPException) as ctx:
                http_bridge.preview_indicator(request)
        self.assertEqual(ctx.exception.status_code, 404)

        with patch.object(http_bridge, "evaluate_indicator", side_effect=ValueError("bad bars")):
            with self.assertRaises(HTTPException) as ctx:
                http_bridge.preview_indicator(request)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "bad bars")

    def test_bridge_has_no_semantic_persistence_broker_or_chart_authority(self):
        source = inspect.getsource(http_bridge)
        forbidden = (
            "CoreTALib",
            "BacktestEngine",
            "Kiwoom",
            "core.db",
            "sqlite",
            "pymysql",
            "ChartDirector",
            "LightweightCharts",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
