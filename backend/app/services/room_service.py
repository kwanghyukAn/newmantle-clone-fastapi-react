from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from app.models.schemas import (
    GuessResult,
    RoomState,
)
from app.services.game_engine import GameEngine
from app.services.storage import SQLiteRepository


class RoomService:
    def __init__(self, engine: GameEngine, repository: SQLiteRepository) -> None:
        self._engine = engine
        self._repository = repository
        self._lock = Lock()

    def create_room(self, host_name: str) -> tuple[str, str]:
        room_id = uuid4().hex[:6].upper()
        player_id = uuid4().hex
        answer = self._engine.choose_room_answer(room_id)
        with self._lock:
            self._repository.create_room(room_id, answer.word, datetime.now(timezone.utc), player_id, host_name)
        return room_id, player_id

    def join_room(self, room_id: str, name: str) -> str:
        with self._lock:
            if not self._repository.room_exists(room_id):
                raise KeyError("room-not-found")
            existing_player_id = self._repository.find_room_player_id_by_name(room_id, name)
            if existing_player_id is not None:
                self._repository.touch_room_player(existing_player_id)
                return existing_player_id
            player_id = uuid4().hex
            self._repository.add_room_player(room_id, player_id, name)
            return player_id

    def guess(self, room_id: str, player_id: str, word: str) -> GuessResult:
        with self._lock:
            answer_word = self._repository.get_room_answer_word(room_id)
            if answer_word is None:
                raise KeyError("room-not-found")
            if not self._repository.room_player_exists(room_id, player_id):
                raise KeyError("player-not-found")

            answer = self._engine.find_entry(answer_word)
            assert answer is not None
            attempt = self._repository.get_player_attempt_count(room_id, player_id) + 1
            result = self._engine.guess(answer, word, attempt)
            player_name = self._repository.get_player_name(player_id)
            if player_name is None:
                raise KeyError("player-not-found")
            self._repository.save_room_guess(room_id, player_id, player_name, result)
            return result

    def get_state(self, room_id: str) -> RoomState:
        answer_word = self._repository.get_room_answer_word(room_id)
        if answer_word is None:
            raise KeyError("room-not-found")
        created_at = self._repository.get_room_created_at(room_id)
        assert created_at is not None
        answer = self._engine.find_entry(answer_word)
        assert answer is not None
        return RoomState(
            room_id=room_id,
            answer_length=len(answer.word),
            created_at=created_at,
            members=self._repository.list_room_members(room_id),
            recent_guesses=self._repository.list_recent_room_guesses(room_id),
        )
