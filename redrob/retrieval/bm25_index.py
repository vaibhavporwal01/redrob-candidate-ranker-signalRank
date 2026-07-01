from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from ..normalization import tokens


def score_corpus(tokenized_docs: list[list[str]], query: str) -> list[float]:
    if not tokenized_docs:
        return []
    query_terms = set(tokens(query))
    document_frequency: Counter[str] = Counter()
    for doc in tokenized_docs:
        document_frequency.update(set(doc) & query_terms)
    average_length = sum(len(doc) for doc in tokenized_docs) / max(1, len(tokenized_docs))
    scores: list[float] = []
    for doc in tokenized_docs:
        frequencies = Counter(doc)
        score = 0.0
        for term in query_terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            inverse_frequency = math.log(1.0 + (len(tokenized_docs) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            denominator = frequency + 1.5 * (1.0 - 0.75 + 0.75 * len(doc) / max(average_length, 1.0))
            score += inverse_frequency * (frequency * 2.5 / denominator)
        scores.append(score)
    return scores

