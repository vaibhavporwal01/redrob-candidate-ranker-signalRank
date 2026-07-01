from __future__ import annotations

from pathlib import Path
from typing import Any


def load_optional_index(path: str | Path) -> Any | None:
    """Load an offline FAISS index when the optional dependency/artifact is present."""
    try:
        import faiss  # type: ignore
    except ImportError:
        return None
    target = Path(path)
    return faiss.read_index(str(target)) if target.exists() else None

