from __future__ import annotations

from datetime import date
from typing import Any

from ..normalization import career, number, parse_date, profile, skills, text, years_experience


def honeypot_features(candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    years = years_experience(candidate)
    if years < 0 or years > float(config["max_reasonable_experience_years"]):
        flags.append("implausible_experience")

    age = number(profile(candidate).get("age"), -1)
    if age > 0 and years > max(0, age - 17):
        flags.append("experience_exceeds_working_age")

    for skill in skills(candidate):
        duration = number(skill.get("duration_months"))
        proficiency = text(skill.get("proficiency")).lower()
        if duration > float(config["max_skill_duration_months"]):
            flags.append("implausible_skill_duration")
        if proficiency == "expert" and duration <= 0:
            flags.append("expert_with_zero_duration")

    intervals: list[tuple[date, date]] = []
    summed_months = 0.0
    for role in career(candidate):
        duration = number(role.get("duration_months"))
        summed_months += max(0, duration)
        if duration > float(config["max_role_duration_months"]):
            flags.append("implausible_role_duration")
        start = parse_date(role.get("start_date"))
        end = parse_date(role.get("end_date"))
        if start and end:
            if start > end:
                flags.append("reversed_timeline")
            else:
                intervals.append((start, end))

    if years > 0 and summed_months > years * 12 * 1.8:
        flags.append("career_duration_mismatch")
    if _max_overlap(intervals) > int(config["max_concurrent_roles"]):
        flags.append("excessive_overlapping_roles")
    unique = sorted(set(flags))
    severity = "severe" if any(flag in unique for flag in ("reversed_timeline", "experience_exceeds_working_age", "implausible_experience")) else "moderate" if len(unique) >= 2 else "minor" if unique else "none"
    multipliers = {
        "severe": float(config["severe_multiplier"]),
        "moderate": float(config["moderate_multiplier"]),
        "minor": float(config["minor_multiplier"]),
        "none": 1.0,
    }
    return {"honeypot_flags": unique, "honeypot_severity": severity, "honeypot_multiplier": multipliers[severity]}


def _max_overlap(intervals: list[tuple[date, date]]) -> int:
    events: list[tuple[date, int]] = []
    for start, end in intervals:
        events.extend([(start, 1), (end, -1)])
    running = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        running += delta
        maximum = max(maximum, running)
    return maximum

