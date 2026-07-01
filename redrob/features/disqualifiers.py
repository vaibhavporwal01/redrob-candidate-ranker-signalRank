from __future__ import annotations

from typing import Any

from ..jd import JobDefinition
from ..normalization import career, career_text, contains_any, number, role_description, text, title, years_experience


HARD_FLAGS = {
    "consulting_only",
    "research_only",
    "modality_mismatch",
    "recent_wrapper_only",
    "non_technical_title",
    "leadership_without_recent_code",
    "title_chaser",
    "closed_source_unvalidated",
}


def disqualifier_features(candidate: dict[str, Any], jd: JobDefinition, config: dict[str, Any]) -> dict[str, Any]:
    roles = career(candidate)
    history = career_text(candidate).lower()
    descriptions = " ".join(role_description(role) for role in roles).lower()
    companies = [text(role.get("company")).lower() for role in roles if text(role.get("company"))]
    consulting_only = bool(companies) and all(any(name in company for name in jd.company_rules["consultancies"]) for company in companies)
    production = contains_any(descriptions, jd.signals["production"])
    research = contains_any(history, jd.signals["research"])
    nlp_ir = contains_any(history, jd.signals["nlp_ir"])
    other_modalities = contains_any(history, jd.signals["other_modalities"])
    wrappers = contains_any(history, jd.signals["recent_wrapper"])
    pre_llm_depth = contains_any(history, [*jd.skill_groups["retrieval"], *jd.skill_groups["ranking"], *jd.skill_groups["recommendation"]]) and production

    senior_roles = sum(1 for role in roles if contains_any(text(role.get("title")), jd.title_rules["senior"]))
    durations = [number(role.get("duration_months")) for role in roles if number(role.get("duration_months")) > 0]
    average_tenure = sum(durations) / len(durations) if durations else 999.0
    title_chaser = len(roles) >= 3 and average_tenure < float(config["short_tenure_months"]) and senior_roles >= 2

    latest = roles[0] if roles else {}
    latest_desc = role_description(latest)
    architecture_only = contains_any(latest_desc, ["architecture", "strategy", "roadmap", "technical leadership", "mentored"]) and not contains_any(latest_desc, jd.signals["production"])
    leadership_only = (
        contains_any(title(candidate), jd.title_rules["leadership_only"])
        or (contains_any(title(candidate), jd.title_rules["senior"]) and architecture_only and number(latest.get("duration_months")) >= float(config["recent_code_months"]))
    ) and not contains_any(latest_desc, jd.signals["production"])
    external_validation = contains_any(history, ["open source", "github", "published", "conference", "patent", "technical blog", "speaker"])
    explicitly_closed = contains_any(history, ["closed-source", "closed source", "proprietary platform", "proprietary system"])
    flags = {
        "consulting_only": consulting_only,
        "research_only": research and not production,
        "modality_mismatch": other_modalities and not nlp_ir,
        "recent_wrapper_only": wrappers and not pre_llm_depth,
        "leadership_without_recent_code": leadership_only,
        "title_chaser": title_chaser,
        "closed_source_unvalidated": years_experience(candidate) >= 5 and explicitly_closed and not external_validation,
        "non_technical_title": contains_any(title(candidate), jd.title_rules["non_technical"]),
    }
    active = sorted(name for name, enabled in flags.items() if enabled)
    return {
        "disqualifier_flags": active,
        "hard_disqualified": any(flag in HARD_FLAGS for flag in active),
        "soft_disqualified": bool(active),
    }
