from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from app.models.schemas import DailyState, EmbeddingInfo, GuessRequest, GuessResult, HintResult, RevealResult
from app.services.game_engine import GameEngine
from app.services.storage import SQLiteRepository
from app.core.config import DB_PATH


router = APIRouter(prefix="/api/daily", tags=["daily"])
engine = GameEngine()
repository = SQLiteRepository(DB_PATH)


@router.get("/state", response_model=DailyState)
def get_daily_state(player_name: str | None = None, game_date: date | None = None) -> DailyState:
    resolved_date = game_date or date.today()
    guesses = repository.get_daily_guesses(player_name, resolved_date)
    meta = repository.get_daily_session_meta(player_name, resolved_date)
    answer = engine.choose_daily_answer(resolved_date)
    return DailyState(
        game_date=resolved_date,
        guesses=guesses,
        completed=any(item.correct for item in guesses),
        revealed=bool(meta["revealed"]),
        hint_count=int(meta["hint_count"]),
        initial_hint_used=bool(meta["initial_hint_used"]),
        answer_length=len(answer.word),
        reveal=meta["reveal"] if isinstance(meta["reveal"], RevealResult) or meta["reveal"] is None else None,
    )


@router.post("/guess", response_model=GuessResult)
def submit_daily_guess(payload: GuessRequest, game_date: date | None = None) -> GuessResult:
    resolved_date = game_date or date.today()
    answer = engine.choose_daily_answer(resolved_date)
    guesses = repository.get_daily_guesses(payload.player_name, resolved_date)
    try:
        result = engine.guess(answer, payload.word, len(guesses) + 1)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    repository.save_daily_guess(payload.player_name, resolved_date, result)
    return result


@router.post("/hint", response_model=HintResult)
def get_hint(player_name: str | None = None, game_date: date | None = None) -> HintResult:
    resolved_date = game_date or date.today()
    answer = engine.choose_daily_answer(resolved_date)
    guesses = repository.get_daily_guesses(player_name, resolved_date)
    best_rank = min((guess.rank for guess in guesses), default=999)
    hint = engine.nearby_hint(answer, max(best_rank, 1))
    repository.increment_daily_hint(player_name, resolved_date)
    return hint


@router.post("/initial-hint", response_model=HintResult)
def get_initial_hint(player_name: str | None = None, game_date: date | None = None) -> HintResult:
    resolved_date = game_date or date.today()
    answer = engine.choose_daily_answer(resolved_date)
    hint = engine.initial_hint(answer)
    repository.increment_daily_hint(player_name, resolved_date)
    repository.mark_daily_initial_hint(player_name, resolved_date)
    return hint


@router.post("/give-up", response_model=RevealResult)
def give_up(player_name: str | None = None, game_date: date | None = None) -> RevealResult:
    resolved_date = game_date or date.today()
    answer = engine.choose_daily_answer(resolved_date)
    reveal = engine.reveal(answer)
    repository.reveal_daily_answer(player_name, resolved_date, reveal)
    return reveal


@router.get("/embedding-info", response_model=EmbeddingInfo)
def get_embedding_info() -> EmbeddingInfo:
    return EmbeddingInfo(
        source=engine.source,
        total_words=engine.total_words,
        answer_words=engine.total_answer_words,
        metadata=engine.metadata,
    )
