from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.config import DB_PATH
from app.models.schemas import AdminPasswordRequest, AdminVerifyResponse, RevealResult
from app.services.game_engine import GameEngine
from app.services.storage import SQLiteRepository


ADMIN_PASSWORD = "admin1234"

router = APIRouter(prefix="/api/admin", tags=["admin"])
engine = GameEngine()
repository = SQLiteRepository(DB_PATH)


def _ensure_admin(password: str) -> None:
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="invalid-admin-password")


@router.post("/verify", response_model=AdminVerifyResponse)
def verify_admin(payload: AdminPasswordRequest) -> AdminVerifyResponse:
    _ensure_admin(payload.password)
    return AdminVerifyResponse(unlocked=True)


@router.post("/daily-answer", response_model=RevealResult)
def reveal_daily_answer(payload: AdminPasswordRequest) -> RevealResult:
    _ensure_admin(payload.password)
    resolved_date = payload.game_date or date.today()
    answer = engine.choose_daily_answer(resolved_date)
    return engine.reveal(answer)


@router.post("/room-answer/{room_id}", response_model=RevealResult)
def reveal_room_answer(room_id: str, payload: AdminPasswordRequest) -> RevealResult:
    _ensure_admin(payload.password)
    answer_word = repository.get_room_answer_word(room_id)
    if answer_word is None:
        raise HTTPException(status_code=404, detail="room-not-found")
    answer = engine.find_entry(answer_word)
    if answer is None:
        raise HTTPException(status_code=404, detail="room-answer-not-found")
    return engine.reveal(answer)
