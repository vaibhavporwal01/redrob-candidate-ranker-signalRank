from __future__ import annotations

import hashlib
from typing import Any

from .normalization import candidate_id, career, company, number, role_description, signals, text, title, years_experience


DISPLAY_NAMES = {
    "retrieval": "retrieval/search",
    "embeddings": "embeddings",
    "ranking": "ranking",
    "recommendation": "recommendation systems",
    "vector_databases": "vector databases",
    "evaluation": "ranking evaluation",
    "ml_platform": "ML platform work",
    "python": "Python ML",
}


def generate_reasoning(candidate: dict[str, Any], features: dict[str, Any]) -> str:
    cid = candidate_id(candidate)
    current_title = title(candidate)
    current_company = company(candidate) or "their current company"
    years = years_experience(candidate)
    matched = [DISPLAY_NAMES.get(item, item.replace("_", " ")) for item in features.get("matched_skills", [])]
    skill_phrase = _join(matched[:3]) or "limited direct retrieval evidence"
    evidence = _evidence_snippet(candidate)
    response = features.get("recruiter_response_rate", 0.0)
    active_days = features.get("days_since_active", 0)
    flags = features.get("disqualifier_flags", []) + features.get("honeypot_flags", [])

    if flags:
        readable = flags[0].replace("_", " ")
        return f"{current_title} with {years:g} years of experience shows {skill_phrase}, but the profile is materially down-ranked for {readable}. Evidence was checked across {len(career(candidate))} recorded role(s), not only the skills list."

    templates = [
        f"{current_title} at {current_company} brings {years:g} years of experience with evidence across {skill_phrase}. {evidence}",
        f"Career history supports {skill_phrase}, including {evidence[0].lower() + evidence[1:] if evidence else 'concrete delivery evidence.'} The profile has {years:g} years overall and a {response:.0%} recruiter response rate.",
        f"With {years:g} years in engineering, this candidate pairs {skill_phrase} with a shipper score of {features.get('shipper', 0) * 100:.0f}/100. {evidence}",
        f"The strongest signal is career-level evidence for {skill_phrase}, rather than title keywords alone. {current_title} was active {active_days} day(s) ago; {evidence[0].lower() + evidence[1:] if evidence else 'the work history is production-oriented.'}",
    ]
    index = int(hashlib.blake2b(cid.encode("utf-8"), digest_size=2).hexdigest(), 16) % len(templates)
    return templates[index].strip()


def _evidence_snippet(candidate: dict[str, Any]) -> str:
    for role in career(candidate):
        description = role_description(role)
        if description:
            clean = " ".join(description.split()).replace(".", ";").rstrip("; ")
            if len(clean) > 125:
                clean = clean[:122].rsplit(" ", 1)[0] + "…"
            company_name = text(role.get("company")) or "a prior role"
            return f"At {company_name}, the record says: “{clean}”"
    notice = number(signals(candidate).get("notice_period_days"), -1)
    return f"The recorded notice period is {notice:g} days." if notice >= 0 else "The career record is internally consistent."


def _join(items: list[str]) -> str:
    if len(items) > 1:
        return ", ".join(items[:-1]) + " and " + items[-1]
    return items[0] if items else ""
