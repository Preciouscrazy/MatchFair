import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from matchfair.core import simulate, load_players

class MatchFairTests(unittest.TestCase):
    def setUp(self):
        self.players = [
            {"player_id": f"p{i}", "region": "NA", "skill_rating": float(v), "wait_seconds": float(i)}
            for i, v in enumerate([100, 120, 110, 110])
        ]

    def test_balanced_teams(self):
        match = simulate(self.players)["matches"][0]
        self.assertEqual(match["skill_gap"], 0)
        self.assertEqual(len(match["team_a"]), 2)
        self.assertEqual(len(set(match["team_a"] + match["team_b"])), 4)

    def test_determinism(self):
        self.assertEqual(simulate(self.players), simulate(list(reversed(self.players))))

    def test_reject_incomplete_pool(self):
        with self.assertRaises(ValueError):
            simulate(self.players[:3])

    def test_reject_invalid_team_size(self):
        with self.assertRaises(ValueError):
            simulate(self.players, 6)

    def test_sample_csv(self):
        sample = Path(__file__).resolve().parents[1] / "examples" / "players.csv"
        self.assertEqual(len(load_players(sample)), 8)

if __name__ == "__main__":
    unittest.main()
