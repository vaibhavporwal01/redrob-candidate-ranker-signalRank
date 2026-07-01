from __future__ import annotations

from typing import Any

from ..jd import JobDefinition
from ..normalization import career_text, clamp, contains_any, number, skills, text


def skill_features(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> dict[str, Any]:
    history = career_text(candidate).lower()
    production = contains_any(history, jd.signals["production"])
    listed: dict[str, dict[str, Any]] = {}
    for skill in skills(candidate):
        name = text(skill.get("name") or skill.get("skill")).lower()
        if name:
            listed[name] = skill

    career_hits: list[str] = []
    listed_hits: list[str] = []
    listed_credit = 0.0
    for group, aliases in jd.skill_groups.items():
        if contains_any(history, aliases):
            career_hits.append(group)
        matched = next((item for name, item in listed.items() if any(alias.lower() in name or name in alias.lower() for alias in aliases)), None)
        if matched:
            listed_hits.append(group)
            duration = number(matched.get("duration_months"))
            duration_credit = clamp(duration / float(config["duration_full_credit_months"]))
            proficiency = text(matched.get("proficiency")).lower()
            proficiency_credit = {"beginner": 0.35, "intermediate": 0.62, "advanced": 0.84, "expert": 1.0}.get(proficiency, 0.55)
            credit = 0.55 * duration_credit + 0.45 * proficiency_credit
            if proficiency == "expert" and duration <= 0:
                credit *= float(config["expert_zero_duration_penalty"])
            listed_credit += credit

    group_count = max(1, len(jd.skill_groups))
    career_score = len(career_hits) / group_count
    if production and career_hits:
        career_score = clamp(career_score * float(config["production_boost"]))
    listed_score = listed_credit / group_count
    score = (
        career_score * float(config["career_evidence_weight"])
        + listed_score * float(config["listed_skill_weight"])
    )
    return {
        "skill_match": round(clamp(score), 6),
        "career_skill_score": round(clamp(career_score), 6),
        "listed_skill_score": round(clamp(listed_score), 6),
        "matched_skills": sorted(set(career_hits + listed_hits)),
        "career_skill_matches": sorted(career_hits),
    }

