from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.config import DB_PATH
from app.models.schemas import (
    GuessResult,
    RoomCreateRequest,
    RoomCreateResponse,
    RoomGuessRequest,
    RoomJoinRequest,
    RoomState,
)
from app.services.game_engine import GameEngine
from app.services.realtime import RoomBroadcaster
from app.services.room_service import RoomService
from app.services.storage import SQLiteRepository


router = APIRouter(prefix="/api/rooms", tags=["rooms"])
repository = SQLiteRepository(DB_PATH)
room_service = RoomService(GameEngine(), repository)
broadcaster = RoomBroadcaster()


@router.post("", response_model=RoomCreateResponse)
async def create_room(payload: RoomCreateRequest) -> RoomCreateResponse:
    room_id, player_id = room_service.create_room(payload.host_name)
    await broadcaster.broadcast_state(room_id, room_service.get_state(room_id))
    return RoomCreateResponse(room_id=room_id, player_id=player_id)


@router.post("/{room_id}/join", response_model=RoomCreateResponse)
async def join_room(room_id: str, payload: RoomJoinRequest) -> RoomCreateResponse:
    try:
        player_id = room_service.join_room(room_id, payload.name)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    await broadcaster.broadcast_state(room_id, room_service.get_state(room_id))
    return RoomCreateResponse(room_id=room_id, player_id=player_id)


@router.get("/{room_id}", response_model=RoomState)
def get_room_state(room_id: str) -> RoomState:
    try:
        return room_service.get_state(room_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{room_id}/guess", response_model=GuessResult)
async def submit_room_guess(room_id: str, payload: RoomGuessRequest) -> GuessResult:
    try:
        result = room_service.guess(room_id, payload.player_id, payload.word)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    await broadcaster.broadcast_state(room_id, room_service.get_state(room_id))
    return result


@router.websocket("/{room_id}/ws")
async def room_websocket(room_id: str, websocket: WebSocket) -> None:
    if not repository.room_exists(room_id):
        await websocket.close(code=4404)
        return

    await broadcaster.connect(room_id, websocket)
    await broadcaster.broadcast_state(room_id, room_service.get_state(room_id))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(room_id, websocket)
