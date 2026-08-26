import tempfile
from pathlib import Path
import unittest

import tactical_main
from core.tactical_evolution_lineage import TacticalEvolutionLineage
from core.tactical_evolution_store import TacticalEvolutionStore


ROOT = Path(__file__).resolve().parent


class TacticalEvolutionUiTests(unittest.TestCase):
    def test_read_only_endpoint_projects_lineage_without_write_route(self):
        with tempfile.TemporaryDirectory() as temp:
            store = TacticalEvolutionStore(Path(temp) / "evolution.db")
            lineage = TacticalEvolutionLineage(store)
            original = tactical_main.evolution_lineage
            tactical_main.evolution_lineage = lineage
            try:
                payload = tactical_main.tactical_evolution_family("EMPTY_FAMILY")
            finally:
                tactical_main.evolution_lineage = original

        self.assertEqual(payload["schema"], "tactical_evolution_lineage/v1")
        self.assertEqual(payload["nodes"], [])
        self.assertEqual(payload["attempts"], [])
        self.assertEqual(payload["projection_policy"], "READ_ONLY_APPEND_ONLY_EVIDENCE_NO_AUTOMATIC_PROMOTION")

        main_source = (ROOT / "tactical_main.py").read_text(encoding="utf-8")
        self.assertIn('@app.get("/api/stage1/tactical/evolution/{family_id}")', main_source)
        self.assertNotIn('@app.post("/api/stage1/tactical/evolution/', main_source)
        self.assertNotIn("evolution_store.promote(", main_source)

    def test_tactical_ui_exposes_skill_tree_and_attempt_evidence(self):
        html = (ROOT / "core" / "templates" / "tactical.html").read_text(encoding="utf-8")
        javascript = (ROOT / "core" / "static" / "tactical.js").read_text(encoding="utf-8")

        for token in (
            'id="evo-family"',
            'id="evo-load"',
            'id="evo-head"',
            'id="evo-lineage"',
            'id="evo-nodes"',
            'id="evo-attempts"',
            "read-only projection",
        ):
            self.assertIn(token, html)

        self.assertIn("/api/stage1/tactical/evolution/", javascript)
        self.assertIn("acquisition_evidence", javascript)
        self.assertIn("holdout_failures", javascript)
        self.assertIn("promoted_generation_hash", javascript)
        self.assertNotIn("/promote", javascript)

    def test_health_advertises_read_only_lineage_capability(self):
        health = tactical_main.tactical_health()
        self.assertIn("evolution_lineage_read_only", health["capabilities"])


if __name__ == "__main__":
    unittest.main()
