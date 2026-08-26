import unittest

from core.tactical_sector_provider import SectorMembershipSnapshotProvider


class FakeExecutor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def fetchall(self, database, sql, params=()):
        self.calls.append((database, sql, tuple(params)))
        return [dict(row) for row in self.rows]


class SectorProviderTests(unittest.TestCase):
    def test_exact_sector_snapshot_preserves_role_and_membership(self):
        rows = [
            {"code": "000001", "name": "Leader", "sector_name": "AI", "role": "LEADER", "rs": 3.2},
            {"code": "000002", "name": "Follower", "sector_name": "AI", "role": "FOLLOWER", "rs": 1.1},
        ]
        provider = SectorMembershipSnapshotProvider(
            FakeExecutor(rows),
            database="research_db",
            table="sector_membership_snapshot",
            feature_columns=("rs",),
        )
        snapshot = provider.load(
            as_of="20260825090000",
            sector_id="AI",
        )
        self.assertEqual(snapshot.symbols, ("000001", "000002"))
        self.assertEqual(snapshot.members[0].features["role"], "LEADER")
        self.assertEqual(snapshot.metadata["membership_contract"], "EXACT_AS_OF")

    def test_missing_exact_sector_snapshot_fails_closed(self):
        provider = SectorMembershipSnapshotProvider(
            FakeExecutor([]),
            database="research_db",
            table="sector_membership_snapshot",
        )
        with self.assertRaisesRegex(ValueError, "정확한 sector membership"):
            provider.load(as_of="20260825090000", sector_id="AI")


if __name__ == "__main__":
    unittest.main()
