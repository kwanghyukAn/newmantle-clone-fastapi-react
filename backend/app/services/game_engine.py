from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date

import numpy as np

from app.models.schemas import GuessResult, HintResult
from app.services.embedding_store import EmbeddingBundle, VocabEntry, load_vocab


def normalize_word(word: str) -> str:
    return word.strip().lower()


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def leading_consonants(word: str) -> str:
    result: list[str] = []
    for char in word:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            choseong = (code - 0xAC00) // 588
            result.append("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"[choseong])
        else:
            result.append(char[:1])
    return "".join(result)


@dataclass
class RankedWord:
    entry: VocabEntry
    similarity: float
    rank: int


class GameEngine:
    def __init__(self) -> None:
        self._bundle: EmbeddingBundle = load_vocab()
        self._entries = self._bundle.entries
        self._matrix = self._bundle.matrix
        self._entry_map = {normalize_word(entry.word): entry for entry in self._entries}
        self._answer_entries = [entry for entry in self._entries if entry.word in self._bundle.answer_words]
        self._rank_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}

    @property
    def vocab(self) -> list[VocabEntry]:
        return list(self._entries)

    @property
    def source(self) -> str:
        return self._bundle.source

    @property
    def metadata(self) -> dict[str, object]:
        return self._bundle.metadata

    def find_entry(self, word: str) -> VocabEntry | None:
        return self._entry_map.get(normalize_word(word))

    def choose_daily_answer(self, game_date: date) -> VocabEntry:
        digest = hashlib.sha256(game_date.isoformat().encode("utf-8")).digest()
        pool = self._answer_entries or list(self._entries)
        return pool[int.from_bytes(digest[:4], "big") % len(pool)]

    def choose_room_answer(self, room_id: str) -> VocabEntry:
        rng = random.Random(room_id)
        pool = self._answer_entries or list(self._entries)
        return pool[rng.randrange(len(pool))]

    def _similarities_and_ranks(self, answer: VocabEntry) -> tuple[np.ndarray, np.ndarray]:
        cached = self._rank_cache.get(answer.index)
        if cached is not None:
            return cached

        similarities = self._matrix @ self._matrix[answer.index]
        order = np.argsort(-similarities, kind="stable")
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(order) + 1)
        self._rank_cache[answer.index] = (similarities, ranks)
        return similarities, ranks

    def guess(self, answer: VocabEntry, word: str, attempt: int) -> GuessResult:
        entry = self.find_entry(word)
        if entry is None:
            raise ValueError("unknown-word")

        similarities, ranks = self._similarities_and_ranks(answer)
        similarity = float(similarities[entry.index])
        rank = int(ranks[entry.index])
        return GuessResult(
            word=entry.word,
            similarity=round(similarity * 100, 2),
            rank=rank,
            correct=entry.word == answer.word,
            attempt=attempt,
        )

    def nearby_hint(self, answer: VocabEntry, rank_floor: int) -> HintResult:
        similarities, ranks = self._similarities_and_ranks(answer)
        target_rank = max(2, min(len(self._entries), rank_floor + 1))
        target_index = int(np.where(ranks == target_rank)[0][0])
        target = self._entries[target_index]
        return HintResult(
            word=target.word,
            similarity=round(float(similarities[target_index]) * 100, 2),
            rank=target_rank,
            kind="nearby",
        )

    def initial_hint(self, answer: VocabEntry) -> HintResult:
        return HintResult(
            word=leading_consonants(answer.word),
            similarity=100.0,
            rank=0,
            kind="initial",
        )
