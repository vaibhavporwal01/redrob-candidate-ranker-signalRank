from __future__ import annotations

from typing import Any

from .normalization import clamp


def final_score(features: dict[str, Any], retrieval_relevance: float, config: dict[str, Any]) -> tuple[float, dict[str, float]]:
    weighted = (
        retrieval_relevance * float(config["retrieval_relevance"])
        + features["skill_match"] * float(config["skill_match"])
        + features["hidden_gem"] * float(config["hidden_gem"])
        + features["shipper"] * float(config["shipper"])
        + features["production"] * float(config["production"])
        + features["experience_fit"] * float(config["experience_fit"])
        + features["location_notice"] * float(config["location_notice"])
        + features["career_quality"] * float(config["career_quality"])
    )
    gate = 1.0
    if features["hard_disqualified"]:
        gate = float(config["hard_gate_multiplier"])
    elif features["soft_disqualified"]:
        gate = float(config["soft_gate_multiplier"])
    behavioral = float(features["behavioral_multiplier"])
    honeypot = float(features["honeypot_multiplier"])
    score = weighted * gate * behavioral * honeypot * float(config["score_scale"])
    breakdown = {
        "retrieval": round(clamp(retrieval_relevance) * 100, 1),
        "skills": round(features["skill_match"] * 100, 1),
        "hidden_gem": round(features["hidden_gem"] * 100, 1),
        "shipper": round(features["shipper"] * 100, 1),
        "production": round(features["production"] * 100, 1),
        "career": round(features["career_quality"] * 100, 1),
        "availability": round(behavioral * 100, 1),
        "integrity": round(honeypot * 100, 1),
    }
    return round(max(0.0, score), 6), breakdown

