from __future__ import annotations

import functools
import hashlib
import math
import os
from multiprocessing import Pool

from ..normalization import tokens

_SEM_STATE: dict = {}


@functools.lru_cache(maxsize=32768)
def _bucket(token: str, dimensions: int) -> tuple[int, float]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    raw = int.from_bytes(digest, "big")
    return raw % dimensions, 1.0 if raw & 1 else -1.0


def hashed_embedding(doc_tokens: list[str], dimensions: int = 384) -> dict[int, float]:
    vector: dict[int, float] = {}
    for token in doc_tokens:
        index, sign = _bucket(token, dimensions)
        vector[index] = vector.get(index, 0.0) + sign
    norm = math.sqrt(sum(item * item for item in vector.values())) or 1.0
    return {index: item / norm for index, item in vector.items()}


def cosine(left: dict[int, float], right: dict[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def _score_one(doc: list[str]) -> float:
    query_vector = _SEM_STATE["query_vector"]
    dimensions = _SEM_STATE["dimensions"]
    return max(0.0, cosine(hashed_embedding(doc, dimensions), query_vector))


def _init_worker(query_vector: dict[int, float], dimensions: int) -> None:
    _SEM_STATE["query_vector"] = query_vector
    _SEM_STATE["dimensions"] = dimensions


def semantic_scores(tokenized_docs: list[list[str]], query: str, dimensions: int, workers: int | None = None) -> list[float]:
    if not tokenized_docs:
        return []
    query_vector = hashed_embedding(tokens(query), dimensions)
    num_docs = len(tokenized_docs)

    worker_count = workers or os.cpu_count() or 1
    if worker_count <= 1 or num_docs < 2000:
        _init_worker(query_vector, dimensions)
        return [_score_one(doc) for doc in tokenized_docs]

    chunk_size = max(1, num_docs // (worker_count * 4))
    with Pool(
        processes=worker_count,
        initializer=_init_worker,
        initargs=(query_vector, dimensions),
    ) as pool:
        return pool.map(_score_one, tokenized_docs, chunksize=chunk_size)
