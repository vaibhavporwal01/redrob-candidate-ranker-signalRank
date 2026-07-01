from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml_compatible(path: Path) -> dict[str, Any]:
    """Load our JSON-compatible YAML without making rank.py depend on PyYAML."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_jd_config() -> dict[str, Any]:
    return _load_yaml_compatible(ROOT / "config" / "jd_config.yaml")


@lru_cache(maxsize=1)
def load_scoring_config() -> dict[str, Any]:
    return _load_yaml_compatible(ROOT / "config" / "scoring_weights.yaml")

