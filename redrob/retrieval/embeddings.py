from __future__ import annotations

import functools
import hashlib
import math

from ..normalization import tokens


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


def semantic_scores(tokenized_docs: list[list[str]], query: str, dimensions: int) -> list[float]:
    query_vector = hashed_embedding(tokens(query), dimensions)
    return [max(0.0, cosine(hashed_embedding(doc, dimensions), query_vector)) for doc in tokenized_docs]

