import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML = ROOT / "core" / "templates" / "stage1.html"
TRADE_AUDIT = ROOT / "core" / "static" / "stage1_trade_audit.js"


class Stage1TradeAuditUiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.script = TRADE_AUDIT.read_text(encoding="utf-8")

    def test_selected_trade_has_explicit_visible_ui_state(self):
        self.assertIn('id="selected-trade"', self.html)
        self.assertIn('stage1_trade_audit.js', self.html)
        self.assertIn('trade-selected', self.html)
        self.assertIn('ENTRY / EXIT / 보유구간', self.html)

    def test_trade_click_uses_delegated_capture_and_exact_experiment_evidence(self):
        self.assertIn("document.addEventListener('click',activateFromEvent,true)", self.script)
        self.assertIn('event.stopImmediatePropagation()', self.script)
        self.assertIn('/api/stage1/experiments/${experimentId}', self.script)
        self.assertIn("closed_trades", self.script)
        self.assertIn("aria-selected", self.script)

    def test_trade_chart_audit_requests_semantic_overlay_without_chart_library_ownership(self):
        self.assertIn("vertical-region", self.script)
        self.assertIn("Trade #${tradeId} ENTRY", self.script)
        self.assertIn("Trade #${tradeId} EXIT", self.script)
        self.assertIn("#${tradeId} ENTRY", self.script)
        self.assertIn("#${tradeId} EXIT", self.script)
        self.assertIn("chart-document/render", self.script)
        self.assertNotIn("lightweight-charts", self.script)
        self.assertNotIn("createChart(", self.script)


if __name__ == "__main__":
    unittest.main()
