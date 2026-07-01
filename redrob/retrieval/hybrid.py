from __future__ import annotations

import heapq
import multiprocessing
import os
from typing import Any

from ..jd import JobDefinition
from ..normalization import candidate_text, tokens
from .bm25_index import score_corpus
from .embeddings import semantic_scores

def _extract_tokens(candidate: dict[str, Any]) -> list[str]:
    return tokens(candidate_text(candidate))

def retrieve(candidates: list[dict[str, Any]], jd: JobDefinition, config: dict[str, Any]) -> list[tuple[dict[str, Any], float]]:
    tokenized_docs = [_extract_tokens(c) for c in candidates]

    lexical = score_corpus(tokenized_docs, jd.retrieval_text)
    semantic = semantic_scores(tokenized_docs, jd.retrieval_text, int(config["hash_dimensions"]))
    lexical_max = max(lexical, default=1.0) or 1.0
    semantic_max = max(semantic, default=1.0) or 1.0
    lexical_weight = float(config["bm25_weight"])
    semantic_weight = float(config["dense_weight"])
    combined = [
        lexical_weight * (lexical[index] / lexical_max) + semantic_weight * (semantic[index] / semantic_max)
        for index in range(len(candidates))
    ]
    count = min(len(candidates), int(config["candidate_pool_size"]))
    best = heapq.nlargest(count, range(len(candidates)), key=combined.__getitem__)
    maximum = max((combined[index] for index in best), default=1.0) or 1.0
    return [(candidates[index], round(combined[index] / maximum, 6)) for index in best]

