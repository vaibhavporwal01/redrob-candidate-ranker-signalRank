from __future__ import annotations

from typing import Any

from ..jd import JobDefinition
from ..normalization import (
    career,
    career_text,
    clamp,
    contains_any,
    location,
    number,
    profile,
    role_description,
    signals,
    text,
    years_experience,
)


def hidden_gem_score(candidate: dict[str, Any], jd: JobDefinition) -> float:
    """Find shipped search/retrieval work in role evidence, independently of titles/skill lists."""
    evidence_groups = ["retrieval", "embeddings", "ranking", "recommendation", "vector_databases"]
    descriptions = " ".join(role_description(role) for role in career(candidate)).lower()
    hits = sum(1 for group in evidence_groups if contains_any(descriptions, jd.skill_groups[group]))
    production = contains_any(descriptions, jd.signals["production"])
    product_context = any(not _is_consultancy(text(role.get("company")), jd) for role in career(candidate))
    score = hits / len(evidence_groups)
    if hits and production:
        score += 0.24
    if hits and product_context:
        score += 0.12
    return round(clamp(score), 6)


def shipper_score(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> float:
    history = career_text(candidate).lower()
    ship_hits = sum(history.count(signal.lower()) for signal in jd.signals["shipper"])
    research_hits = sum(history.count(signal.lower()) for signal in jd.signals["research"])
    small_company_roles = 0
    for role in career(candidate):
        size = number(role.get("company_size"))
        if 0 < size <= float(config["small_company_max_size"]):
            small_company_roles += 1
    positive = min(1.0, ship_hits / 3.0) * 0.68 + min(1.0, small_company_roles / 2.0) * 0.20
    production_bonus = 0.12 if contains_any(history, jd.signals["production"]) else 0.0
    research_drag = min(0.42, research_hits * 0.10)
    return round(clamp(positive + production_bonus - research_drag), 6)


def production_score(candidate: dict[str, Any], jd: JobDefinition) -> float:
    descriptions = " ".join(role_description(role) for role in career(candidate)).lower()
    hits = sum(1 for signal in jd.signals["production"] if signal.lower() in descriptions)
    return round(clamp(hits / 4.0), 6)


def experience_fit(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> float:
    years = years_experience(candidate)
    low = float(jd.job.get("min_years", config["min_years"]))
    high = float(jd.job.get("max_years", config["max_years"]))
    tolerance = float(config["experience_tolerance_years"])
    if low <= years <= high:
        return 1.0
    distance = low - years if years < low else years - high
    return round(clamp(1.0 - distance / max(tolerance, 0.1)), 6)


def career_quality(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> float:
    roles = career(candidate)
    if not roles:
        return 0.0
    durations = [number(role.get("duration_months")) for role in roles if number(role.get("duration_months")) > 0]
    tenure = sum(durations) / len(durations) if durations else 0.0
    stability = clamp(tenure / max(float(config["short_tenure_months"]), 1.0))
    product_roles = sum(1 for role in roles if not _is_consultancy(text(role.get("company")), jd))
    progression = sum(1 for role in roles if contains_any(text(role.get("title")), jd.title_rules["senior"]))
    return round(clamp(stability * 0.45 + min(1.0, product_roles / 2.0) * 0.35 + min(1.0, progression / 2.0) * 0.20), 6)


def location_notice_score(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> float:
    loc = location(candidate).lower()
    sig = signals(candidate)
    notice = number(sig.get("notice_period_days", profile(candidate).get("notice_period_days")), 60)
    preferred = any(place.lower() in loc for place in jd.job["preferred_locations"])
    in_india = preferred or jd.job["country"].lower() in loc
    quick = float(config["quick_notice_days"])
    long = float(config["long_notice_days"])
    if preferred and notice <= quick:
        return 1.0
    if preferred and notice < long:
        return 0.78
    if preferred:
        return 0.56
    if in_india and notice <= quick:
        return 0.78
    if in_india:
        return 0.58
    return 0.28 if notice <= quick else 0.12


def career_features(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "hidden_gem": hidden_gem_score(candidate, jd),
        "shipper": shipper_score(candidate, jd, config),
        "production": production_score(candidate, jd),
        "experience_fit": experience_fit(candidate, jd, config),
        "career_quality": career_quality(candidate, jd, config),
        "location_notice": location_notice_score(candidate, jd, config),
    }


def _is_consultancy(company_name: str, jd: JobDefinition) -> bool:
    low = company_name.lower()
    return any(name in low for name in jd.company_rules["consultancies"])

