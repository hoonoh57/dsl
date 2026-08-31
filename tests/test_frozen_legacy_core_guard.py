from __future__ import annotations

import subprocess
import unittest


class FrozenLegacyCoreGuardTests(unittest.TestCase):
    """Fail if the preserved legacy core tree changes after the freeze checkpoint."""

    EXPECTED_CORE_TREE = "8b3f081de926f5c9f69e9cdbc158b81b2275176c"

    def test_legacy_core_tree_is_immutable(self):
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD:core"],
            check=True,
            capture_output=True,
            text=True,
        )
        actual = completed.stdout.strip()
        self.assertEqual(
            actual,
            self.EXPECTED_CORE_TREE,
            "legacy core/ is frozen. Do not modify/move/add/delete files under core/. "
            "Migrate or extend DSL capabilities only under axes/axis1_dsl/.",
        )


if __name__ == "__main__":
    unittest.main()
