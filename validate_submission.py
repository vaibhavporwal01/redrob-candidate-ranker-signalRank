from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_COLUMNS = ["candidate_id", "rank", "score", "reasoning"]


def validate(path: str | Path) -> list[str]:
    errors: list[str] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_COLUMNS:
            errors.append(f"Columns must be exactly {EXPECTED_COLUMNS}; got {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 100:
        errors.append(f"Expected 100 rows; got {len(rows)}")
    ranks: list[int] = []
    scores: list[float] = []
    ids: list[str] = []
    for line, row in enumerate(rows, 2):
        try:
            ranks.append(int(row.get("rank", "")))
            scores.append(float(row.get("score", "")))
        except ValueError:
            errors.append(f"Line {line}: rank and score must be numeric")
            continue
        cid = row.get("candidate_id", "").strip()
        if not cid:
            errors.append(f"Line {line}: candidate_id is empty")
        ids.append(cid)
        reasoning = row.get("reasoning", "").strip()
        if not reasoning:
            errors.append(f"Line {line}: reasoning is empty")
    if sorted(ranks) != list(range(1, 101)):
        errors.append("Ranks must contain each integer 1-100 exactly once")
    if len(set(ids)) != len(ids):
        errors.append("candidate_id values must be unique")
    for index in range(1, len(scores)):
        if scores[index] > scores[index - 1]:
            errors.append(f"Score increases between ranks {index} and {index + 1}")
        if scores[index] == scores[index - 1] and ids[index] < ids[index - 1]:
            errors.append(f"Tie at ranks {index}/{index + 1} is not candidate_id ascending")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission")
    args = parser.parse_args()
    try:
        errors = validate(args.submission)
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 1
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: submission has 100 valid, correctly ordered rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

