"""Cross-platform, real-process tests of the MatchFair CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MatchFairCliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "matchfair", *(str(arg) for arg in args)],
            cwd=cwd or ROOT, env=env,
            capture_output=True, text=True, timeout=20, check=False,
        )

    def test_sample_golden_cli_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            result = self.run_cli("--input", ROOT / "examples" / "players.csv", "--output", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                json.loads((ROOT / "evidence" / "sample-match-report.json").read_text(encoding="utf-8")),
            )

    def test_queue_tradeoff_golden_cli_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            result = self.run_cli("--input", ROOT / "examples" / "queue_tradeoff.csv", "--output", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                json.loads((ROOT / "evidence" / "queue-tradeoff-report.json").read_text(encoding="utf-8")),
            )

    def test_default_output_in_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("--input", ROOT / "examples" / "players.csv", cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((Path(tmp) / "match-report.json").read_text())["match_count"], 2)

    def test_reject_same_input_output_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "players.csv"
            csv.write_text("player_id,skill_rating,wait_seconds,region\na,10,1,NA\nb,10,1,NA\n", encoding="utf-8")
            before = csv.read_bytes()
            result = self.run_cli("--input", csv, "--output", csv, "--team-size", 1)
            self.assertEqual(result.returncode, 2)
            self.assertIn("same file", result.stderr)
            self.assertEqual(csv.read_bytes(), before)

    def test_reject_hard_link_to_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "players.csv"
            alias = Path(tmp) / "alias.csv"
            csv.write_text("player_id,skill_rating,wait_seconds,region\na,10,1,NA\nb,10,1,NA\n", encoding="utf-8")
            try:
                os.link(csv, alias)
            except OSError as exc:
                self.skipTest(f"hard links not supported: {exc}")
            before = csv.read_bytes()
            result = self.run_cli("--input", csv, "--output", alias, "--team-size", 1)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(csv.read_bytes(), before)

    def test_bad_csv_preserves_prior_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "bad.csv"
            out = Path(tmp) / "out.json"
            csv.write_text("player_id,skill_rating,wait_seconds,region\np1,hello,5,NA\n", encoding="utf-8")
            out.write_text("older valid report", encoding="utf-8")
            result = self.run_cli("--input", csv, "--output", out)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(out.read_text(encoding="utf-8"), "older valid report")

    def test_existing_output_replaced_and_no_temp_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.json"
            output.write_text("old", encoding="utf-8")
            result = self.run_cli("--input", ROOT / "examples" / "players.csv", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["match_count"], 2)
            self.assertFalse(list(Path(tmp).glob("*.tmp")))

    def test_incomplete_region_pool_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "bad.csv"
            out = Path(tmp) / "result.json"
            csv.write_text("player_id,skill_rating,wait_seconds,region\np1,100,1,NA\n", encoding="utf-8")
            result = self.run_cli("--input", csv, "--output", out)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(out.exists())

    def test_invalid_team_size_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            for size in ("0", "6", "-1", "nope"):
                with self.subTest(size=size):
                    result = self.run_cli("--input", ROOT / "examples" / "players.csv",
                                          "--output", Path(tmp) / "result.json", "--team-size", size)
                    self.assertEqual(result.returncode, 2)

    def test_missing_input_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("--input", Path(tmp) / "absent.csv",
                                  "--output", Path(tmp) / "report.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Error:", result.stderr)

    def test_help_exits_zero(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--team-size", result.stdout)

    def test_missing_required_input_exits_two(self):
        result = self.run_cli("--team-size", "2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("required", result.stderr)


if __name__ == "__main__":
    unittest.main()
