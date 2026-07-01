from __future__ import annotations

import math
import os
from collections import Counter
from multiprocessing import Pool
from typing import Iterable

from ..normalization import tokens

_STATE: dict = {}
_DOCS: list[list[str]] = []


def _score_by_index(index: int) -> float:
    doc = _DOCS[index]
    query_terms = _STATE["query_terms"]
    document_frequency = _STATE["document_frequency"]
    num_docs = _STATE["num_docs"]
    average_length = _STATE["average_length"]
    frequencies = Counter(doc)
    score = 0.0
    for term in query_terms:
        frequency = frequencies.get(term, 0)
        if not frequency:
            continue
        inverse_frequency = math.log(1.0 + (num_docs - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
        denominator = frequency + 1.5 * (1.0 - 0.75 + 0.75 * len(doc) / max(average_length, 1.0))
        score += inverse_frequency * (frequency * 2.5 / denominator)
    return score


def _init_worker(query_terms: set[str], document_frequency: Counter, num_docs: int, average_length: float) -> None:
    _STATE["query_terms"] = query_terms
    _STATE["document_frequency"] = document_frequency
    _STATE["num_docs"] = num_docs
    _STATE["average_length"] = average_length


def score_corpus(tokenized_docs: list[list[str]], query: str, workers: int | None = None) -> list[float]:
    global _DOCS
    if not tokenized_docs:
        return []
    query_terms = set(tokens(query))
    document_frequency: Counter[str] = Counter()
    for doc in tokenized_docs:
        document_frequency.update(set(doc) & query_terms)
    average_length = sum(len(doc) for doc in tokenized_docs) / max(1, len(tokenized_docs))
    num_docs = len(tokenized_docs)

    worker_count = workers or os.cpu_count() or 1
    if worker_count <= 1 or num_docs < 2000:
        _DOCS = tokenized_docs
        _init_worker(query_terms, document_frequency, num_docs, average_length)
        return [_score_by_index(i) for i in range(num_docs)]

    # Assign to the module-level global BEFORE forking workers, so children
    # inherit it via copy-on-write memory instead of pickling it through pipes.
    _DOCS = tokenized_docs
    chunk_size = max(1, num_docs // (worker_count * 4))
    with Pool(
        processes=worker_count,
        initializer=_init_worker,
        initargs=(query_terms, document_frequency, num_docs, average_length),
    ) as pool:
        return pool.map(_score_by_index, range(num_docs), chunksize=chunk_size)
