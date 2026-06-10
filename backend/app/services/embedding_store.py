from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from app.core.config import DATA_PATH, FULL_ANSWER_WORDS_PATH, FULL_METADATA_PATH, FULL_VECTORS_PATH, FULL_WORDS_PATH


@dataclass(frozen=True)
class VocabEntry:
    word: str
    tags: tuple[str, ...]
    index: int


@dataclass(frozen=True)
class EmbeddingBundle:
    entries: tuple[VocabEntry, ...]
    matrix: np.ndarray
    source: str
    metadata: dict[str, object]
    answer_words: frozenset[str]


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _load_seed_bundle() -> EmbeddingBundle:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    entries = tuple(
        VocabEntry(
            word=item["word"],
            tags=tuple(item["tags"]),
            index=index,
        )
        for index, item in enumerate(raw)
    )
    matrix = np.array([item["vector"] for item in raw], dtype=np.float32)
    return EmbeddingBundle(
        entries=entries,
        matrix=_normalize_rows(matrix),
        source="seed-json",
        metadata={"path": str(DATA_PATH)},
        answer_words=frozenset(entry.word for entry in entries),
    )


def _load_npz_bundle() -> EmbeddingBundle:
    words = json.loads(FULL_WORDS_PATH.read_text(encoding="utf-8"))
    data = np.load(FULL_VECTORS_PATH)
    matrix = np.asarray(data["vectors"], dtype=np.float32)
    metadata = json.loads(FULL_METADATA_PATH.read_text(encoding="utf-8")) if FULL_METADATA_PATH.exists() else {}
    answer_words = (
        frozenset(json.loads(FULL_ANSWER_WORDS_PATH.read_text(encoding="utf-8")))
        if FULL_ANSWER_WORDS_PATH.exists()
        else frozenset(str(word) for word in words)
    )
    entries = tuple(
        VocabEntry(
            word=str(word),
            tags=(),
            index=index,
        )
        for index, word in enumerate(words)
    )
    return EmbeddingBundle(
        entries=entries,
        matrix=_normalize_rows(matrix),
        source="fasttext-npz",
        metadata=metadata,
        answer_words=answer_words,
    )


@lru_cache(maxsize=1)
def load_vocab() -> EmbeddingBundle:
    if FULL_WORDS_PATH.exists() and FULL_VECTORS_PATH.exists():
        return _load_npz_bundle()
    return _load_seed_bundle()
