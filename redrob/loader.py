from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .normalization import candidate_id
from .schema import validate_candidate


def stream_candidates(path: str | Path) -> Iterator[dict]:
    seen: set[str] = set()
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                record = validate_candidate(json.loads(raw))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Invalid candidate on JSONL line {line_number}: {exc}") from exc
            cid = candidate_id(record)
            if not cid:
                raise ValueError(f"Missing candidate_id on JSONL line {line_number}")
            if cid in seen:
                raise ValueError(f"Duplicate candidate_id {cid!r} on JSONL line {line_number}")
            seen.add(cid)
            yield record


def load_candidates(path: str | Path) -> list[dict]:
    return list(stream_candidates(path))

