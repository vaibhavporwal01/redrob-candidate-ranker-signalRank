from __future__ import annotations

import argparse
import sys

from redrob.pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank Redrob Senior AI Engineer candidates")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Path for submission.csv")
    args = parser.parse_args()
    try:
        run(args.candidates, args.out)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

