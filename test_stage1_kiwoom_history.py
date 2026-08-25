import unittest

from core.kiwoom_rest import KiwoomAPIError, KiwoomConfig, KiwoomRESTClient


class FakeKiwoom(KiwoomRESTClient):
    def __init__(self):
        super().__init__(KiwoomConfig("x", "y", mock=True))
        self.token = "token"
        self.calls = []

    def _post(self, path, body, api_id=None, *, continuation="", next_key=""):
        self.calls.append({
            "path": path,
            "body": dict(body),
            "api_id": api_id,
            "continuation": continuation,
            "next_key": next_key,
        })
        if len(self.calls) == 1:
            rows = [
                {"cntr_tm": "20260825091500", "cur_prc": "103", "open_pric": "102", "high_pric": "104", "low_pric": "101", "trde_qty": "130"},
                {"cntr_tm": "20260825091000", "cur_prc": "102", "open_pric": "101", "high_pric": "103", "low_pric": "100", "trde_qty": "120"},
            ]
            return {"return_code": 0, "stk_min_pole_chart_qry": rows}, {"cont-yn": "Y", "next-key": "NEXT1"}
        rows = [
            {"cntr_tm": "20260825090500", "cur_prc": "101", "open_pric": "100", "high_pric": "102", "low_pric": "99", "trde_qty": "110"},
            {"cntr_tm": "20260825090000", "cur_prc": "100", "open_pric": "99", "high_pric": "101", "low_pric": "98", "trde_qty": "100"},
        ]
        return {"return_code": 0, "stk_min_pole_chart_qry": rows}, {"cont-yn": "N", "next-key": ""}


class Stage1KiwoomHistoryTest(unittest.TestCase):
    def test_symbol_venue_formatting_is_explicit_and_fail_closed(self):
        self.assertEqual(KiwoomRESTClient.format_symbol("214330", "SOR"), "214330_AL")
        self.assertEqual(KiwoomRESTClient.format_symbol("214330_AL", "SOR"), "214330_AL")
        self.assertEqual(KiwoomRESTClient.format_symbol("214330", "NXT"), "214330_NX")
        with self.assertRaisesRegex(KiwoomAPIError, "충돌"):
            KiwoomRESTClient.format_symbol("214330_NX", "SOR")

    def test_chart_history_replays_continuation_headers_and_merges_exact_timestamps(self):
        client = FakeKiwoom()
        result = client.chart_history(
            "214330", "5m", venue="SOR", required_bars=4, required_start="20260825090000"
        )
        self.assertEqual(result["symbol"], "214330_AL")
        self.assertEqual(result["coverage"]["pages"], 2)
        self.assertEqual(result["market"]["time"], [
            "20260825090000", "20260825090500", "20260825091000", "20260825091500"
        ])
        self.assertEqual(client.calls[0]["body"]["stk_cd"], "214330_AL")
        self.assertEqual(client.calls[1]["continuation"], "Y")
        self.assertEqual(client.calls[1]["next_key"], "NEXT1")

    def test_chart_history_fails_when_coverage_cannot_be_proven(self):
        client = FakeKiwoom()
        with self.assertRaisesRegex(KiwoomAPIError, "coverage"):
            client.chart_history("214330", "5m", venue="SOR", required_bars=10, max_pages=2)

    def test_history_requires_explicit_coverage_contract(self):
        client = FakeKiwoom()
        with self.assertRaisesRegex(KiwoomAPIError, "required_bars"):
            client.chart_history("214330", "5m", venue="SOR")


if __name__ == "__main__":
    unittest.main()
