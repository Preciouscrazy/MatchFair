import argparse
import json
from .core import load_players, simulate

def main():
    parser = argparse.ArgumentParser(description="Simulate region-scoped balanced teams")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="match-report.json")
    parser.add_argument("--team-size", type=int, default=2)
    args = parser.parse_args()
    try:
        report = simulate(load_players(args.input), team_size=args.team_size)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Saved {args.output}")

if __name__ == "__main__":
    main()
