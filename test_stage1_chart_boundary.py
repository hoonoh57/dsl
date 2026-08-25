from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
STAGE1_HTML = ROOT / "core" / "templates" / "stage1.html"
STAGE1_JS = ROOT / "core" / "static" / "stage1.js"
CHART_DOCUMENT = ROOT / "core" / "stage1_chart_document.py"


class Stage1ChartBoundaryTest(unittest.TestCase):
    def test_stage1_shell_does_not_own_chart_library_rendering(self):
        browser_source = "\n".join([
            STAGE1_HTML.read_text(encoding="utf-8"),
            STAGE1_JS.read_text(encoding="utf-8"),
        ])
        forbidden = (
            "lightweight-charts",
            "LightweightCharts",
            ".createChart(",
            ".addCandlestickSeries(",
            ".addLineSeries(",
            ".addHistogramSeries(",
            ".removeSeries(",
            ".setMarkers(",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, browser_source)

    def test_stage1_uses_shared_chart_document_protocol(self):
        html = STAGE1_HTML.read_text(encoding="utf-8")
        script = STAGE1_JS.read_text(encoding="utf-8")
        self.assertIn('<div id="chart"></div>', html)
        self.assertIn("chart-document-viewer.html", script)
        self.assertIn("chart-document/render", script)
        self.assertIn("chart-document/ready", script)
        self.assertIn("postMessage", script)
        self.assertIn("event.origin!==chartSsotOrigin", script)

    def test_chart_projection_is_semantic_only(self):
        source = CHART_DOCUMENT.read_text(encoding="utf-8")
        forbidden = (
            "lightweight-charts",
            "LightweightCharts",
            "createChart(",
            "addLineSeries(",
            "addCandlestickSeries(",
            "canvas",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)
        self.assertIn('"version": "chart-document/v1"', source)
        self.assertIn('"bars": bars', source)
        self.assertIn('"series": series', source)
        self.assertIn('"markers": markers', source)


if __name__ == "__main__":
    unittest.main()
