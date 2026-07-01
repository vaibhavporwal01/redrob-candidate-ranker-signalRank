from __future__ import annotations

from typing import Any

from ..jd import JobDefinition
from .behavioral import behavioral_features
from .career import career_features
from .disqualifiers import disqualifier_features
from .honeypot import honeypot_features
from .skills import skill_features


def extract_features(candidate: dict[str, Any], jd: JobDefinition, weights: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    result.update(skill_features(candidate, jd, weights["skills"]))
    result.update(career_features(candidate, jd, weights["career"]))
    result.update(disqualifier_features(candidate, jd, weights["career"]))
    result.update(honeypot_features(candidate, weights["honeypot"]))
    result.update(behavioral_features(candidate, weights["behavioral"]))
    return result
