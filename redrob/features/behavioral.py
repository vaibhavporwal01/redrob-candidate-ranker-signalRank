from __future__ import annotations

from typing import Any

from ..normalization import clamp, number, parse_date, signals, today_utc


def behavioral_features(candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    data = signals(candidate)
    active = parse_date(data.get("last_active_date"))
    days_stale = (today_utc() - active).days if active else int(config["very_stale_days"])
    response = number(data.get("recruiter_response_rate"), 0.0)
    if response > 1.0:
        response /= 100.0
    stale = float(config["stale_days"])
    very_stale = float(config["very_stale_days"])
    low_response = float(config["low_response_rate"])
    healthy = float(config["healthy_response_rate"])

    if days_stale > very_stale and response < low_response:
        multiplier = float(config["severe_multiplier"])
    elif days_stale > stale and response < low_response:
        multiplier = min(0.5, float(config["stale_multiplier"]))
    else:
        recency = 1.0 if days_stale <= 30 else clamp(1.0 - (days_stale - 30) / max(very_stale, 1.0))
        responsiveness = clamp(response / max(healthy, 0.01))
        multiplier = 0.58 + 0.24 * recency + 0.23 * responsiveness
    multiplier = clamp(multiplier, float(config["floor"]), float(config["ceiling"]))
    return {
        "behavioral_multiplier": round(multiplier, 6),
        "days_since_active": max(0, days_stale),
        "recruiter_response_rate": round(response, 4),
        "availability_risk": "high" if multiplier < 0.55 else "medium" if multiplier < 0.78 else "low",
    }

