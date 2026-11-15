"""Command-line reporting for the offline MatchFair simulator."""

import argparse
import json
import os
from pathlib import Path
import tempfile

from .core import load_players, simulate


def _same_file(source, destination):
    """Protect the source against canonical-path and existing-hard-link aliases."""
    if source.resolve() == destination.resolve():
        return True
    return source.exists() and destination.exists() and source.samefile(destination)


def _write_report(destination, report):
    """Stage complete JSON alongside the target before replacing its contents."""
    content = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=destination.parent, prefix=f".{destination.name}.",
            suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Simulate region-scoped balanced teams")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="match-report.json")
    parser.add_argument("--team-size", type=int, default=2)
    args = parser.parse_args()
    source, destination = Path(args.input), Path(args.output)
    try:
        if _same_file(source, destination):
            raise ValueError("input and output refer to the same file")
        report = simulate(load_players(source), team_size=args.team_size)
        _write_report(destination, report)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
