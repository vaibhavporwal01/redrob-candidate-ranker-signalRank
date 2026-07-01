from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


COLUMNS = ["candidate_id", "rank", "score", "reasoning"]


def write_submission(ranked: list[dict[str, Any]], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for item in ranked:
            writer.writerow({
                "candidate_id": item["candidate_id"],
                "rank": item["rank"],
                "score": f"{item['score']:.6f}",
                "reasoning": item["reasoning"],
            })
    return target

