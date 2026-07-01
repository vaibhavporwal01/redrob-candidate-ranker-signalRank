from __future__ import annotations

import math
import re
from datetime import date, datetime, timezone
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]{1,}")


def number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return " ".join(text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text(item) for item in value.values())
    return str(value)


def candidate_id(candidate: dict[str, Any]) -> str:
    profile = candidate.get("profile") or {}
    value = candidate.get("candidate_id", candidate.get("id", profile.get("candidate_id", profile.get("id", ""))))
    return str(value).strip()


def profile(candidate: dict[str, Any]) -> dict[str, Any]:
    value = candidate.get("profile")
    return value if isinstance(value, dict) else {}


def career(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    value = candidate.get("career_history") or candidate.get("experience") or []
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def skills(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    value = candidate.get("skills") or []
    if not isinstance(value, list):
        return result
    for item in value:
        if isinstance(item, str):
            result.append({"name": item})
        elif isinstance(item, dict):
            result.append(item)
    return result


def signals(candidate: dict[str, Any]) -> dict[str, Any]:
    value = candidate.get("redrob_signals") or candidate.get("signals") or {}
    return value if isinstance(value, dict) else {}


def title(candidate: dict[str, Any]) -> str:
    p = profile(candidate)
    return text(p.get("current_title") or candidate.get("current_title") or p.get("headline") or "Not specified")


def company(candidate: dict[str, Any]) -> str:
    p = profile(candidate)
    return text(p.get("current_company") or candidate.get("current_company") or (career(candidate)[0].get("company") if career(candidate) else ""))


def years_experience(candidate: dict[str, Any]) -> float:
    p = profile(candidate)
    direct = number(p.get("years_of_experience", candidate.get("years_of_experience")), -1)
    if direct >= 0:
        return direct
    months = sum(max(0.0, number(role.get("duration_months"))) for role in career(candidate))
    return round(months / 12.0, 1)


def location(candidate: dict[str, Any]) -> str:
    p = profile(candidate)
    return text(p.get("location") or candidate.get("location") or signals(candidate).get("location"))


def role_description(role: dict[str, Any]) -> str:
    return text(role.get("description") or role.get("summary") or role.get("responsibilities") or role.get("achievements"))


def career_text(candidate: dict[str, Any]) -> str:
    chunks = []
    for role in career(candidate):
        chunks.extend([text(role.get("title")), text(role.get("company")), role_description(role)])
    return " ".join(chunks)


def candidate_text(candidate: dict[str, Any]) -> str:
    p = profile(candidate)
    skill_text = " ".join(text(item.get("name") or item.get("skill")) for item in skills(candidate))
    return " ".join([
        title(candidate), company(candidate), text(p.get("headline")), text(p.get("summary")),
        career_text(candidate), skill_text, location(candidate),
    ]).lower()


def tokens(value: str) -> list[str]:
    return TOKEN_RE.findall(value.lower())


def contains_any(haystack: str, needles: Iterable[str]) -> bool:
    low = haystack.lower()
    return any(needle.lower() in low for needle in needles)


def count_matches(haystack: str, needles: Iterable[str]) -> int:
    low = haystack.lower()
    return sum(1 for needle in needles if needle.lower() in low)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    raw = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))

