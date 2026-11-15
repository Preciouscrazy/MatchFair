"""Algorithm, CSV, and evidence regression checks for MatchFair."""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from matchfair.core import balance, load_players, simulate


def make_players(ratings, region="NA", prefix="p", waits=None):
    if waits is None:
        waits = list(range(len(ratings), 0, -1))
    return [
        {"player_id": f"{prefix}{i}", "region": region,
         "skill_rating": float(skill), "wait_seconds": float(wait)}
        for i, (skill, wait) in enumerate(zip(ratings, waits))
    ]


class MatchFairTests(unittest.TestCase):
    def setUp(self):
        self.players = make_players([100, 120, 110, 110])

    def load_csv(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "players.csv"
            path.write_text(content, encoding="utf-8")
            return load_players(path)

    def test_balanced_teams(self):
        match = simulate(self.players)["matches"][0]
        self.assertEqual(match["skill_gap"], 0)
        self.assertEqual(len(match["team_a"]), 2)
        self.assertEqual(len(set(match["team_a"] + match["team_b"])), 4)

    def test_determinism_and_source_unchanged(self):
        original = [p.copy() for p in self.players]
        result = simulate(self.players)
        self.assertEqual(result, simulate(list(reversed(self.players))))
        self.assertEqual(self.players, original)

    def test_reject_incomplete_pool(self):
        with self.assertRaisesRegex(ValueError, "multiple"):
            simulate(self.players[:3])

    def test_reject_invalid_team_size(self):
        for size in (0, -1, 6, 2.0, True, "2", None):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    simulate(self.players, size)

    def test_team_size_one(self):
        result = simulate(make_players([100, 80]), 1)
        match = result["matches"][0]
        self.assertEqual(match["team_a"], ["p0"])
        self.assertEqual(match["team_b"], ["p1"])
        self.assertEqual(match["skill_gap"], 20)

    def test_team_size_five_supported(self):
        result = simulate(make_players([10] * 10), 5)
        self.assertEqual(result["match_count"], 1)
        self.assertEqual(result["matches"][0]["skill_gap"], 0)
        self.assertEqual(len(result["matches"][0]["team_a"]), 5)

    def test_precise_skill_gap_not_rounded_before_ranking(self):
        players = make_players([0, 1e-10, 2e-10, 3e-10])
        players[0]["player_id"] = "anchor"
        players[1]["player_id"] = "aaa"
        players[2]["player_id"] = "bbb"
        players[3]["player_id"] = "ccc"
        match = simulate(players)["matches"][0]
        self.assertEqual(match["team_a"], ["anchor", "ccc"])
        self.assertAlmostEqual(match["skill_gap"], 0, places=20)

    def test_deterministic_tie_break_by_player_id(self):
        group = make_players([100, 100, 100, 100], waits=[3, 3, 3, 3])
        actual = simulate(group)["matches"][0]
        self.assertEqual(actual["team_a"], ["p0", "p1"])
        self.assertEqual(actual["team_b"], ["p2", "p3"])

    def test_group_validation(self):
        with self.assertRaises(ValueError):
            balance(self.players[:3], 2)

    def test_regions_do_not_mix(self):
        players = make_players([100, 101, 102, 103], "NA", "n")
        players += make_players([900, 901, 902, 903], "EU", "e")
        result = simulate(players)
        self.assertEqual([m["region"] for m in result["matches"]], ["EU", "NA"])
        for match in result["matches"]:
            self.assertTrue(all(p[0] == match["region"][0].lower() for p in match["team_a"] + match["team_b"]))

    def test_queue_wait_order_selects_match_groups(self):
        players = make_players([100, 100, 100, 0, 0, 0, 0, 100],
                               waits=[80, 70, 60, 50, 40, 30, 20, 10])
        matches = simulate(players)["matches"]
        self.assertEqual(set(matches[0]["team_a"] + matches[0]["team_b"]), {"p0", "p1", "p2", "p3"})
        self.assertEqual(set(matches[1]["team_a"] + matches[1]["team_b"]), {"p4", "p5", "p6", "p7"})
        self.assertEqual([m["skill_gap"] for m in matches], [100, 100])

    def test_multiple_groups_summaries(self):
        players = make_players([100] * 8, waits=[8, 7, 6, 5, 4, 3, 2, 1])
        summary = simulate(players)
        self.assertEqual(summary["match_count"], 2)
        self.assertEqual(summary["mean_skill_gap"], 0)
        self.assertEqual([m["mean_wait_seconds"] for m in summary["matches"]], [6.5, 2.5])

    def test_reject_no_players(self):
        with self.assertRaises(ValueError):
            simulate([])

    def test_reject_duplicate_ids_direct(self):
        players = [p.copy() for p in self.players]
        players[-1]["player_id"] = players[0]["player_id"]
        with self.assertRaisesRegex(ValueError, "duplicate player ID"):
            simulate(players)

    def test_reject_duplicate_ids_across_regions(self):
        players = make_players([100, 100], "EU")
        players += make_players([100, 100], "NA")
        with self.assertRaisesRegex(ValueError, "duplicate player ID"):
            simulate(players, 1)

    def test_reject_empty_and_nonstring_ids_regions(self):
        for field, value in (("player_id", ""), ("region", ""), ("player_id", 5), ("region", None)):
            with self.subTest(field=field, value=value):
                players = [p.copy() for p in self.players]
                players[0][field] = value
                with self.assertRaises(ValueError):
                    simulate(players)

    def test_reject_nonfinite_and_negative_direct_metrics(self):
        for field in ("skill_rating", "wait_seconds"):
            for value in (math.nan, math.inf, -math.inf, -1, True, "12"):
                with self.subTest(field=field, value=value):
                    players = [p.copy() for p in self.players]
                    players[0][field] = value
                    with self.assertRaises(ValueError):
                        simulate(players)

    def test_reject_missing_direct_fields(self):
        with self.assertRaises(ValueError):
            simulate([{"player_id": "p0"}])

    def test_reject_excessive_team_skill_total(self):
        players = make_players([1e308] * 4)
        with self.assertRaisesRegex(ValueError, "finite numeric range"):
            simulate(players)

    def test_sample_csv(self):
        self.assertEqual(len(load_players(ROOT / "examples" / "players.csv")), 8)

    def test_sample_report_matches_golden(self):
        actual = simulate(load_players(ROOT / "examples" / "players.csv"))
        expected = json.loads((ROOT / "evidence" / "sample-match-report.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_queue_tradeoff_report_matches_golden(self):
        actual = simulate(load_players(ROOT / "examples" / "queue_tradeoff.csv"))
        expected = json.loads((ROOT / "evidence" / "queue-tradeoff-report.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_csv_supports_utf8_bom_and_quoted_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "players.csv"
            path.write_text('player_id,skill_rating,wait_seconds,region\n"a,1",100,0,NA\n',
                            encoding="utf-8-sig")
            self.assertEqual(load_players(path)[0]["player_id"], "a,1")

    def test_csv_rejects_extra_missing_and_duplicate_headers(self):
        for header in (
            "player_id,skill_rating,wait_seconds",
            "player_id,skill_rating,wait_seconds,region,extra",
            "player_id,skill_rating,wait_seconds,region,region",
            "region,player_id,skill_rating,wait_seconds",
        ):
            with self.subTest(header=header):
                with self.assertRaisesRegex(ValueError, "header"):
                    self.load_csv(header + "\np1,100,5,NA\n")

    def test_csv_rejects_extra_or_missing_columns(self):
        for row in ("p1,100,5,NA,other", "p1,100,5", "p1,100,5,NA,"):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "four columns"):
                    self.load_csv("player_id,skill_rating,wait_seconds,region\n" + row + "\n")

    def test_csv_rejects_duplicate_ids_after_whitespace_trim(self):
        with self.assertRaisesRegex(ValueError, "duplicate player ID"):
            self.load_csv("player_id,skill_rating,wait_seconds,region\np1,100,5,NA\n p1 ,110,2,EU\n")

    def test_csv_rejects_invalid_numeric_rows_with_line_number(self):
        for row in ("p1,nan,1,NA", "p1,2,inf,NA", "p1,-1,2,NA", "p1,10,-5,NA",
                    "p1,nope,2,NA", "p1,,3,NA"):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, r"players.csv:2:"):
                    self.load_csv("player_id,skill_rating,wait_seconds,region\n" + row + "\n")

    def test_csv_rejects_empty_names_and_regions(self):
        for row in (",100,5,NA", "p1,100,5,"):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    self.load_csv("player_id,skill_rating,wait_seconds,region\n" + row + "\n")

    def test_csv_rejects_unclosed_quoted_field(self):
        with self.assertRaises(ValueError):
            self.load_csv('player_id,skill_rating,wait_seconds,region\n"p1,100,5,NA\n')

    def test_csv_rejects_no_players(self):
        with self.assertRaisesRegex(ValueError, "no players"):
            self.load_csv("player_id,skill_rating,wait_seconds,region\n")


if __name__ == "__main__":
    unittest.main()
