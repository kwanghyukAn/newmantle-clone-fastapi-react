from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date

import numpy as np

from app.models.schemas import GuessResult, HintResult, RevealResult, RoomHintMetrics
from app.services.embedding_store import EmbeddingBundle, VocabEntry, load_vocab


JOSA_SUFFIXES = (
    "에서는",
    "으로는",
    "에게서",
    "까지는",
    "부터는",
    "이라고",
    "에서",
    "으로",
    "에게",
    "한테",
    "까지",
    "부터",
    "보다",
    "처럼",
    "마다",
    "이나",
    "나",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "로",
    "과",
    "와",
    "도",
    "만",
    "께",
)


def normalize_word(word: str) -> str:
    return word.strip().lower().replace(" ", "")


def word_variants(word: str) -> list[str]:
    normalized = normalize_word(word)
    variants: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        if candidate and candidate not in seen:
            variants.append(candidate)
            seen.add(candidate)

    add(normalized)
    add(normalized.rstrip(".,!?~"))

    for suffix in JOSA_SUFFIXES:
        if normalized.endswith(suffix):
            stem = normalized[: -len(suffix)]
            if len(stem) >= 2:
                add(stem)

    return variants


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

    @property
    def total_words(self) -> int:
        return len(self._entries)

    @property
    def total_answer_words(self) -> int:
        return len(self._answer_entries)

    def find_entry(self, word: str) -> VocabEntry | None:
        for candidate in word_variants(word):
            entry = self._entry_map.get(candidate)
            if entry is not None:
                return entry
        return None

    def unknown_word_message(self) -> str:
        if self.source == "seed-json":
            return (
                "unknown-word: 현재 서버가 seed 사전으로 실행 중입니다. "
                "실제 fastText 데이터를 준비하지 않으면 대부분의 일반 명사가 인식되지 않습니다."
            )
        return (
            f"unknown-word: 허용 추측 단어 사전에 없는 입력입니다. "
            f"현재 허용 단어 수는 {self.total_words:,}개입니다."
        )

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
            raise ValueError(self.unknown_word_message())

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

    def room_hint_metrics(self, answer: VocabEntry) -> RoomHintMetrics:
        similarities, ranks = self._similarities_and_ranks(answer)

        def similarity_for_rank(target_rank: int) -> float:
            effective_rank = min(len(self._entries), max(1, target_rank))
            target_index = int(np.where(ranks == effective_rank)[0][0])
            return round(float(similarities[target_index]) * 100, 2)

        return RoomHintMetrics(
            rank_1_similarity=100.0,
            top_10_cutoff_similarity=similarity_for_rank(10),
            top_100_cutoff_similarity=similarity_for_rank(100),
        )

    def reveal(self, answer: VocabEntry) -> RevealResult:
        tags = list(answer.tags) if answer.tags else ["일반명사"]
        description = (
            f"'{answer.word}'은(는) {', '.join(tags)} 범주의 한국어 일반명사입니다."
            if tags
            else f"'{answer.word}'은(는) 오늘의 정답 단어입니다."
        )
        return RevealResult(
            word=answer.word,
            answer_length=len(answer.word),
            tags=tags,
            description=description,
        )
