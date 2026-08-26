import unittest

from core.tactical_chart_document import build_tactical_chart_document


def market(symbol):
    return {
        "time": ["20260715090000", "20260715090500", "20260715091000"],
        "open": [100, 101, 102],
        "high": [102, 103, 104],
        "low": [99, 100, 101],
        "close": [101, 102, 103],
        "volume": [1000, 1100, 1200],
        "_meta": {"instrument": symbol, "timeframe": "5m"},
    }


def result_fixture(capture="20260715090500"):
    return {
        "scenario_hash": "s",
        "run_hash": "r",
        "unit": {
            "metadata": {
                "capture_as_of": capture,
                "cohort_snapshot_hash": "cohort",
            }
        },
        "regime": {"windows": []},
        "ranking": [
            {"rank": 1, "symbol": "A", "score": 100},
            {"rank": 2, "symbol": "B", "score": 90},
            {"rank": 3, "symbol": "C", "score": 80},
        ],
        "results": [
            {"symbol": "A", "official_outcome": {"label_10": 0}, "backtest": {"markers": []}},
            {"symbol": "B", "official_outcome": {"label_10": 0}, "backtest": {"markers": []}},
            {"symbol": "C", "official_outcome": {"label_10": 1}, "backtest": {"markers": []}},
        ],
    }


class TacticalChartDocumentTests(unittest.TestCase):
    def test_comparison_selection_follows_point_in_time_ranking_not_outcome(self):
        result = result_fixture()
        document = build_tactical_chart_document(
            result,
            {"A": market("A"), "B": market("B"), "C": market("C")},
            comparison_limit=2,
        )
        self.assertEqual(document["meta"]["focusSymbol"], "A")
        self.assertEqual(document["meta"]["comparisonSymbols"], ["A", "B"])
        self.assertFalse(document["meta"]["outcomeSelectionUsed"])
        self.assertEqual(document["meta"]["selectionBasis"], "point_in_time_rank_only")
        self.assertEqual(len(document["series"]), 2)
        cutoff = next(
            item
            for item in document["geometries"]
            if item.get("label") == "capture cutoff interval"
        )
        self.assertEqual(document["meta"]["captureCutoff"], "20260715090500")
        self.assertLess(cutoff["fromTime"], cutoff["toTime"])
        self.assertEqual(document["meta"]["captureRegion"], {
            "fromTime": cutoff["fromTime"],
            "toTime": cutoff["toTime"],
        })

    def test_capture_cutoff_without_two_actual_post_cutoff_bars_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "비영"):
            build_tactical_chart_document(
                result_fixture("20260715091000"),
                {"A": market("A"), "B": market("B"), "C": market("C")},
            )


if __name__ == "__main__":
    unittest.main()
