from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, ConfigDict, Field

    class Candidate(BaseModel):
        """Loose mirror of the supplied schema; unknown challenge fields are preserved."""

        model_config = ConfigDict(extra="allow")
        candidate_id: str | int | None = None
        profile: dict[str, Any] = Field(default_factory=dict)
        career_history: list[dict[str, Any]] = Field(default_factory=list)
        education: list[dict[str, Any]] = Field(default_factory=list)
        skills: list[Any] = Field(default_factory=list)
        certifications: list[Any] = Field(default_factory=list)
        languages: list[Any] = Field(default_factory=list)
        redrob_signals: dict[str, Any] = Field(default_factory=dict)

except ImportError:  # rank.py intentionally remains usable with the standard library.
    Candidate = dict  # type: ignore[misc,assignment]


def validate_candidate(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Candidate must be a JSON object")
    try:
        model = Candidate.model_validate(record)  # type: ignore[attr-defined]
        return model.model_dump(mode="python")
    except AttributeError:
        return record

