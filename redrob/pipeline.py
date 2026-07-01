from __future__ import annotations

import time
import tracemalloc
from pathlib import Path
from typing import Any

from .config import load_scoring_config
from .features.pipeline import extract_features
from .jd import load_job
from .loader import load_candidates
from .normalization import candidate_id, company, location, title, years_experience
from .reasoning import generate_reasoning
from .retrieval.hybrid import retrieve
from .scoring import final_score
from .submission import write_submission


def _stage(label: str, started: float) -> None:
    _, peak = tracemalloc.get_traced_memory()
    print(f"[{label:<18}] {time.perf_counter() - started:7.2f}s | peak {peak / 1024 / 1024:7.1f} MB", flush=True)


def rank_candidates(candidates: list[dict[str, Any]], top_n: int = 100) -> list[dict[str, Any]]:
    if not candidates:
        return []
    jd = load_job()
    weights = load_scoring_config()
    pool = retrieve(candidates, jd, weights["retrieval"])
    ranked: list[dict[str, Any]] = []
    for candidate, retrieval_score in pool:
        features = extract_features(candidate, jd, weights)
        score, breakdown = final_score(features, retrieval_score, weights["final"])
        ranked.append({
            "candidate_id": candidate_id(candidate),
            "current_title": title(candidate),
            "current_company": company(candidate),
            "location": location(candidate),
            "years_of_experience": years_experience(candidate),
            "score": score,
            "reasoning": generate_reasoning(candidate, features),
            "breakdown": breakdown,
            "matched_skills": features["matched_skills"],
            "disqualifier_flags": features["disqualifier_flags"],
            "honeypot_flags": features["honeypot_flags"],
            "availability_risk": features["availability_risk"],
            "days_since_active": features["days_since_active"],
            "recruiter_response_rate": features["recruiter_response_rate"],
            "candidate": candidate,
        })
    ranked.sort(key=lambda item: (-item["score"], item["candidate_id"]))
    selected = ranked[: min(top_n, len(ranked))]
    for index, item in enumerate(selected, 1):
        item["rank"] = index
    return selected


def run(candidates_path: str | Path, out_path: str | Path, top_n: int = 100) -> list[dict[str, Any]]:
    total_started = time.perf_counter()
    tracemalloc.start()
    candidates = load_candidates(candidates_path)
    _stage("load", total_started)
    if len(candidates) < top_n:
        raise ValueError(f"Need at least {top_n} candidates; received {len(candidates)}")
    rank_started = time.perf_counter()
    ranked = rank_candidates(candidates, top_n=top_n)
    _stage("retrieve + score", rank_started)
    write_submission(ranked, out_path)
    _stage("write", total_started)
    print(f"[complete          ] wrote {len(ranked)} rows to {Path(out_path)}", flush=True)
    tracemalloc.stop()
    return ranked
