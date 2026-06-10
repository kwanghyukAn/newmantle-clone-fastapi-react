from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class GuessRequest(BaseModel):
    player_name: str | None = None
    word: str


class GuessResult(BaseModel):
    word: str
    similarity: float
    rank: int
    correct: bool
    attempt: int


class HintResult(BaseModel):
    word: str
    similarity: float
    rank: int
    kind: Literal["nearby", "initial"]


class RevealResult(BaseModel):
    word: str
    answer_length: int
    tags: list[str]
    description: str


class EmbeddingInfo(BaseModel):
    source: str
    total_words: int
    answer_words: int
    metadata: dict[str, object]


class DailyState(BaseModel):
    game_date: date
    guesses: list[GuessResult]
    completed: bool
    revealed: bool
    hint_count: int
    initial_hint_used: bool
    answer_length: int
    reveal: RevealResult | None = None


class RoomCreateRequest(BaseModel):
    host_name: str = Field(min_length=1, max_length=20)


class RoomCreateResponse(BaseModel):
    room_id: str
    player_id: str


class RoomJoinRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)


class RoomGuessRequest(BaseModel):
    player_id: str
    word: str


class RoomMemberView(BaseModel):
    player_id: str
    name: str
    attempts: int
    best_rank: int | None
    best_similarity: float | None
    solved: bool
    last_active_at: datetime


class RoomGuessView(BaseModel):
    player_id: str
    name: str
    word: str
    similarity: float
    rank: int
    correct: bool
    attempt: int
    created_at: datetime


class RoomState(BaseModel):
    room_id: str
    answer_length: int
    created_at: datetime
    members: list[RoomMemberView]
    recent_guesses: list[RoomGuessView]
